#!/usr/bin/env python3
"""
Scrape Google Scholar for mental rotation articles year by year from 1970 to present.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime
import random
import os


def scrape_single_page(url, page_num):
    """
    Scrape a single page of Google Scholar results.
    
    Args:
        url: The full URL to scrape
        page_num: Page number (0-indexed)
        
    Returns:
        List of article dictionaries from this page
    """
    articles = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='gs_ri')
        
        if not results:
            return articles
        
        start = page_num * 10
        
        for idx, result in enumerate(results):
            try:
                article = {}
                
                # Title
                title_tag = result.find('h3', class_='gs_rt')
                if title_tag:
                    for span in title_tag.find_all('span'):
                        span.decompose()
                    article['title'] = title_tag.get_text().strip()
                    link = title_tag.find('a')
                    article['url'] = link['href'] if link and link.has_attr('href') else 'N/A'
                else:
                    article['title'] = 'N/A'
                    article['url'] = 'N/A'
                
                # Authors, journal, year
                info_tag = result.find('div', class_='gs_a')
                if info_tag:
                    info_text = info_tag.get_text()
                    parts = info_text.split(' - ')
                    
                    article['authors'] = parts[0].strip() if len(parts) > 0 else 'N/A'
                    article['publication'] = parts[1].strip() if len(parts) > 1 else 'N/A'
                    
                    year_part = parts[1] if len(parts) > 1 else ''
                    year = 'N/A'
                    for word in year_part.split(','):
                        word = word.strip()
                        if word.isdigit() and len(word) == 4:
                            year = word
                            break
                    article['year'] = year
                else:
                    article['authors'] = 'N/A'
                    article['publication'] = 'N/A'
                    article['year'] = 'N/A'
                
                # Abstract/snippet
                abstract_tag = result.find('div', class_='gs_rs')
                article['abstract'] = abstract_tag.get_text().strip() if abstract_tag else 'N/A'
                
                # Citation count
                cite_tag = result.find('div', class_='gs_fl').find('a', string=lambda x: x and 'Cited by' in x)
                if cite_tag:
                    cite_text = cite_tag.get_text()
                    cite_count = cite_text.replace('Cited by ', '').strip()
                    article['citations'] = int(cite_count) if cite_count.isdigit() else 0
                else:
                    article['citations'] = 0
                
                # Related articles link
                related_tag = result.find('div', class_='gs_fl').find('a', string=lambda x: x and 'Related articles' in x)
                article['related_url'] = related_tag['href'] if related_tag and related_tag.has_attr('href') else 'N/A'
                
                # Add page and position info
                article['page'] = page_num + 1
                article['position'] = start + idx + 1
                
                articles.append(article)
            
            except Exception as e:
                print(f"    Error parsing result {idx + 1}: {e}")
                continue
    
    except requests.RequestException as e:
        print(f"    Error fetching page: {e}")
    
    return articles


def scrape_year(year, base_url_template, max_pages=100, request_counter={'count': 0}):
    """
    Scrape all articles for a specific year.
    
    Args:
        year: The year to scrape
        base_url_template: URL template with {year} placeholder
        max_pages: Maximum pages per year (Google Scholar limit)
        request_counter: Dict tracking total requests made
        
    Returns:
        List of articles for this year
    """
    print(f"\n{'='*70}")
    print(f"Scraping year: {year}")
    print(f"{'='*70}")
    
    year_articles = []
    page = 0
    consecutive_empty = 0
    
    while page < max_pages:
        start = page * 10
        
        # Build URL for this page
        if page == 0:
            url = base_url_template.format(year=year)
        else:
            url = f"{base_url_template.format(year=year)}&start={start}"
        
        print(f"  Page {page + 1} (results {start + 1}-{start + 10})...", end=" ")
        
        # Track request count
        request_counter['count'] += 1
        
        # Scrape the page
        page_articles = scrape_single_page(url, page)
        
        if not page_articles:
            consecutive_empty += 1
            print(f"No results (empty count: {consecutive_empty})")
            
            # Stop if we get 2 consecutive empty pages
            if consecutive_empty >= 2:
                print(f"  Stopping after {consecutive_empty} consecutive empty pages")
                break
        else:
            consecutive_empty = 0
            year_articles.extend(page_articles)
            print(f"Found {len(page_articles)} articles (Total: {len(year_articles)})")
        
        page += 1
        
        # Longer delay between requests to avoid rate limiting
        delay = random.uniform(5, 10)
        time.sleep(delay)
    
    print(f"\nYear {year} complete: {len(year_articles)} articles collected")
    return year_articles


def scrape_all_years(start_year=1970, end_year=2025, max_requests_per_session=200):
    """
    Scrape articles for all years from start_year to end_year.
    
    Args:
        start_year: First year to scrape (default: 1970)
        end_year: Last year to scrape (default: 2025)
        max_requests_per_session: Max requests before stopping (default: 200)
        
    Returns:
        Dictionary mapping year to list of articles
    """
    # Base URL template
    base_url = 'https://scholar.google.com/scholar?as_ylo={year}&as_yhi={year}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1'
    
    all_articles_by_year = {}
    total_articles = 0
    request_count = 0
    
    print("="*70)
    print(f"Google Scholar Mental Rotation Scraper (Year by Year)")
    print(f"Years: {start_year} to {end_year}")
    print(f"Request limit per session: {max_requests_per_session}")
    print("="*70)
    
    # Request counter shared across all years
    request_counter = {'count': 0}
    
    # Iterate through years (newest to oldest for better data first)
    for year in range(end_year, start_year - 1, -1):
        # Check if we've hit the request limit
        if request_counter['count'] >= max_requests_per_session:
            print(f"\n{'='*70}")
            print(f"REACHED REQUEST LIMIT: {request_counter['count']} requests made")
            print(f"Stopping to avoid rate limiting. Progress has been saved.")
            print(f"To continue, run the script again starting from year {year}")
            print(f"{'='*70}")
            save_final_results(all_articles_by_year, total_articles)
            return all_articles_by_year
        
        try:
            articles = scrape_year(year, base_url, request_counter=request_counter)
            all_articles_by_year[year] = articles
            total_articles += len(articles)
            
            print(f"Total requests so far: {request_counter['count']}/{max_requests_per_session}")
            
            # Save progress after each year
            save_progress(all_articles_by_year, total_articles)
            
            # Longer delay between years to avoid rate limiting
            if year > start_year:
                delay = random.uniform(15, 25)
                print(f"\nWaiting {delay:.1f} seconds before next year...")
                time.sleep(delay)
                
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Saving progress...")
            save_final_results(all_articles_by_year, total_articles)
            return all_articles_by_year
        except Exception as e:
            print(f"\nError processing year {year}: {e}")
            continue
    
    # Save final results
    save_final_results(all_articles_by_year, total_articles)
    
    return all_articles_by_year


def save_progress(articles_by_year, total_count):
    """Save progress to a temporary file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Flatten all articles
    all_articles = []
    for year, articles in sorted(articles_by_year.items(), reverse=True):
        for article in articles:
            article['search_year'] = year
            all_articles.append(article)
    
    if all_articles:
        # Save progress as JSON
        progress_file = 'data/scraping_progress.json'
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                'last_updated': timestamp,
                'total_articles': total_count,
                'years_completed': list(articles_by_year.keys()),
                'articles': all_articles
            }, f, indent=2, ensure_ascii=False)


def save_final_results(articles_by_year, total_count):
    """Save final results to CSV and JSON."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Flatten all articles
    all_articles = []
    for year, articles in sorted(articles_by_year.items(), reverse=True):
        for article in articles:
            article['search_year'] = year
            all_articles.append(article)
    
    if not all_articles:
        print("No articles to save.")
        return
    
    # Save as CSV
    df = pd.DataFrame(all_articles)
    csv_path = f'data/mental_rotation_complete_{timestamp}.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n{'='*70}")
    print(f"Saved {len(all_articles)} articles to {csv_path}")
    
    # Save as JSON
    json_path = f'data/mental_rotation_complete_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_articles)} articles to {json_path}")
    
    # Print summary statistics
    print(f"\n{'='*70}")
    print("Summary Statistics")
    print(f"{'='*70}")
    print(f"Total articles collected: {len(all_articles)}")
    print(f"Years covered: {min(articles_by_year.keys())} - {max(articles_by_year.keys())}")
    print(f"\nArticles per year:")
    for year in sorted(articles_by_year.keys(), reverse=True):
        count = len(articles_by_year[year])
        if count > 0:
            print(f"  {year}: {count:4d} articles")
    
    # Citation statistics
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['citations'] = pd.to_numeric(df['citations'], errors='coerce')
    
    print(f"\nCitation Statistics:")
    print(f"  Average citations: {df['citations'].mean():.1f}")
    print(f"  Median citations: {df['citations'].median():.1f}")
    print(f"  Most cited: {df['citations'].max():.0f}")
    
    print(f"\nTop 10 most cited articles:")
    top10 = df.nlargest(10, 'citations')[['title', 'authors', 'year', 'citations']]
    for idx, row in top10.iterrows():
        print(f"  [{int(row['citations']):4d}] {row['title'][:55]}... ({int(row['year'])})")
    
    # Clean up progress file
    if os.path.exists('data/scraping_progress.json'):
        os.remove('data/scraping_progress.json')


def main():
    """Main execution function."""
    # Scrape from 1970 (Shepard & Metzler) to 2025
    # Conservative limit: 200 requests per session (safe for daily limit)
    # At ~7 seconds per request, this is ~25 minutes of scraping
    # You can run this multiple times per day to continue where it left off
    scrape_all_years(start_year=1970, end_year=2025, max_requests_per_session=200)


if __name__ == '__main__':
    main()
