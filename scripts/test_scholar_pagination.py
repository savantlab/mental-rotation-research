#!/usr/bin/env python3
"""
Test script to analyze Google Scholar pagination and result counts.
"""

import requests
from bs4 import BeautifulSoup
import time


def test_result_count(year):
    """
    Test how Google Scholar displays result counts for a given year.
    """
    url = f'https://scholar.google.com/scholar?as_ylo={year}&as_yhi={year}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"\n{'='*70}")
    print(f"Testing year: {year}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for result count information
        # Google Scholar typically shows: "About X results"
        
        # Method 1: Look for result stats div
        result_stats = soup.find('div', {'id': 'gs_ab_md'})
        if result_stats:
            print(f"\nResult stats div found:")
            print(f"  Text: {result_stats.get_text().strip()}")
        
        # Method 2: Look for all divs that might contain result info
        print(f"\nSearching for result count indicators...")
        for div in soup.find_all('div'):
            text = div.get_text().strip()
            if 'result' in text.lower() or 'about' in text.lower():
                if len(text) < 200:  # Avoid long texts
                    print(f"  Found: {text}")
        
        # Method 3: Look at the pagination
        print(f"\nPagination information:")
        
        # Find navigation/pagination elements
        nav_elements = soup.find_all('a', href=lambda x: x and 'start=' in x)
        if nav_elements:
            print(f"  Found {len(nav_elements)} pagination links")
            for link in nav_elements[:5]:  # Show first 5
                print(f"    - {link.get_text()}: {link.get('href')}")
        else:
            print("  No pagination links found")
        
        # Method 4: Count actual results on page
        results = soup.find_all('div', class_='gs_ri')
        print(f"\nActual results on page: {len(results)}")
        
        # Method 5: Look for "Next" button to see if there are more pages
        next_button = soup.find('a', string=lambda x: x and 'Next' in x if x else False)
        if next_button:
            print(f"  'Next' button found - more pages available")
        else:
            print(f"  No 'Next' button - this might be the last page")
        
        # Save HTML for manual inspection
        html_file = f'data/test_scholar_{year}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\nHTML saved to: {html_file}")
        
    except Exception as e:
        print(f"Error: {e}")


def test_multiple_years():
    """Test multiple years to see patterns."""
    test_years = [2025, 2024, 2020, 2015, 2010, 2000, 1990, 1980, 1970]
    
    print("="*70)
    print("Google Scholar Pagination Analysis")
    print("Testing multiple years to understand result counts")
    print("="*70)
    
    for year in test_years:
        test_result_count(year)
        time.sleep(5)  # Be respectful
        print("\n")


if __name__ == '__main__':
    # Test a single year first
    test_result_count(2024)
    
    # Uncomment to test multiple years:
    # test_multiple_years()
