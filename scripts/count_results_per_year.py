#!/usr/bin/env python3
"""
Count total results available for each year to plan scraping strategy.
This makes one request per year to get result counts.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime
import re


def get_result_count(year):
    """
    Get the total number of results for a given year.
    
    Returns:
        tuple: (result_count, has_results, error_message)
    """
    url = f'https://scholar.google.com/scholar?as_ylo={year}&as_yhi={year}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check for rate limiting
        if response.status_code == 429:
            return None, False, "Rate limited"
        
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Look for "About X results" text
        result_count = None
        result_stats = soup.find('div', {'id': 'gs_ab_md'})
        if result_stats:
            text = result_stats.get_text()
            # Extract number from "About X results"
            match = re.search(r'About\s+([\d,]+)\s+results?', text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(',', '')
                result_count = int(count_str)
        
        # Method 2: Check if there are any results at all
        results = soup.find_all('div', class_='gs_ri')
        has_results = len(results) > 0
        
        # Method 3: Look for alternative result count indicators
        if result_count is None:
            # Sometimes it's in different divs
            for div in soup.find_all('div'):
                text = div.get_text()
                if 'result' in text.lower():
                    match = re.search(r'(\d+(?:,\d+)*)\s+results?', text, re.IGNORECASE)
                    if match:
                        count_str = match.group(1).replace(',', '')
                        try:
                            result_count = int(count_str)
                            break
                        except:
                            pass
        
        # If we have results but no count, estimate from pagination
        if has_results and result_count is None:
            # Look for last page number in pagination
            max_page = 1
            for link in soup.find_all('a', href=lambda x: x and 'start=' in x):
                match = re.search(r'start=(\d+)', link.get('href'))
                if match:
                    start = int(match.group(1))
                    page_num = (start // 10) + 1
                    max_page = max(max_page, page_num)
            
            # Estimate: if we see pagination to page X, there are at least X*10 results
            if max_page > 1:
                result_count = f"~{max_page * 10}+ (estimated)"
        
        return result_count, has_results, None
        
    except requests.RequestException as e:
        return None, False, str(e)


def survey_all_years(start_year=1970, end_year=2025):
    """
    Survey all years to get result counts.
    This is a lightweight operation - only 1 request per year.
    """
    print("="*70)
    print("Mental Rotation Research - Result Count Survey")
    print(f"Years: {start_year} to {end_year}")
    print("="*70)
    print("\nThis will make ONE request per year to count available results.")
    print(f"Total requests: {end_year - start_year + 1}")
    print("Estimated time: ~{:.1f} minutes\n".format((end_year - start_year + 1) * 7.5 / 60))
    
    results_by_year = {}
    total_results = 0
    
    for year in range(end_year, start_year - 1, -1):
        print(f"Year {year}...", end=" ", flush=True)
        
        count, has_results, error = get_result_count(year)
        
        if error:
            print(f"ERROR: {error}")
            results_by_year[year] = {
                'count': None,
                'has_results': False,
                'error': error
            }
        else:
            results_by_year[year] = {
                'count': count,
                'has_results': has_results,
                'error': None
            }
            
            if isinstance(count, int):
                print(f"{count:5d} results")
                total_results += count
            elif count:
                print(f"{count}")
            elif has_results:
                print("Results found (count unknown)")
            else:
                print("No results")
        
        # Delay between requests
        if year > start_year:
            delay = random.uniform(5, 10)
            time.sleep(delay)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'data/result_counts_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump({
            'survey_date': timestamp,
            'start_year': start_year,
            'end_year': end_year,
            'results_by_year': results_by_year,
            'total_results': total_results
        }, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("SURVEY COMPLETE")
    print("="*70)
    print(f"Saved to: {output_file}")
    print(f"\nTotal countable results: {total_results:,}")
    
    years_with_results = sum(1 for y in results_by_year.values() if y['has_results'])
    print(f"Years with results: {years_with_results}/{len(results_by_year)}")
    
    # Show breakdown
    print("\nResults by decade:")
    for decade_start in range(start_year, end_year + 1, 10):
        decade_end = min(decade_start + 9, end_year)
        decade_total = sum(
            r['count'] for y, r in results_by_year.items()
            if decade_start <= y <= decade_end and isinstance(r['count'], int)
        )
        if decade_total > 0:
            print(f"  {decade_start}s: {decade_total:6,} results")
    
    # Calculate scraping requirements
    print("\n" + "="*70)
    print("SCRAPING PLAN")
    print("="*70)
    
    # Assuming 900 requests per day, 10 results per request
    results_per_day = 900 * 10  # 9000 results per day (if all pages full)
    
    # But we need to account for pagination overhead
    # Each year might have up to 100 pages (1000 results max per year query)
    
    print(f"\nAt 900 requests/day (Google limit = 1000):")
    print(f"  Can get ~{results_per_day:,} results per day (if all pages full)")
    print(f"  Estimated days needed: {(total_results / results_per_day):.1f} days")
    print(f"\nNote: This assumes all pages have 10 results, actual may vary")
    
    return results_by_year


def main():
    """Main execution."""
    survey_all_years(start_year=1970, end_year=2025)


if __name__ == '__main__':
    main()
