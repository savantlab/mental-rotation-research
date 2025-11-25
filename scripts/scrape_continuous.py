#!/usr/bin/env python3
"""
Continuous scraper with automatic session breaks to respect daily limits.
Runs 800 requests per session, then waits 6 hours before continuing.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import random
import os


def scrape_single_page(url, page_num):
    """Scrape a single page of Google Scholar results."""
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


def scrape_year(year, base_url_template, request_counter, max_pages=100):
    """Scrape all articles for a specific year."""
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
        
        # Delay between requests
        delay = random.uniform(5, 10)
        time.sleep(delay)
    
    print(f"\nYear {year} complete: {len(year_articles)} articles collected")
    return year_articles


def load_progress():
    """Load progress from file if it exists."""
    progress_file = 'data/scraping_progress.json'
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('years_completed', []), data.get('articles', [])
    return [], []


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
        citations = int(row['citations']) if pd.notna(row['citations']) else 0
        year = int(row['year']) if pd.notna(row['year']) else 0
        print(f"  [{citations:4d}] {row['title'][:55]}... ({year})")
    
    # Clean up progress file
    if os.path.exists('data/scraping_progress.json'):
        os.remove('data/scraping_progress.json')


def scrape_continuous(start_year=1970, end_year=2025, requests_per_session=900, break_hours=24):
    """
    Continuously scrape with automatic breaks between sessions.
    
    Args:
        start_year: First year to scrape
        end_year: Last year to scrape
        requests_per_session: Max requests per session (default: 900)
        break_hours: Hours to wait between sessions (default: 24)
    """
    # Note: Google Scholar has a ~1000 request/day limit
    # We use 900 to have a safety buffer
    base_url = 'https://scholar.google.com/scholar?as_ylo={year}&as_yhi={year}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1'
    
    # Load any existing progress
    completed_years, existing_articles = load_progress()
    
    print("="*70)
    print(f"Continuous Google Scholar Scraper")
    print(f"Years: {start_year} to {end_year}")
    print(f"Requests per session: {requests_per_session}")
    print(f"Break between sessions: {break_hours} hours")
    print("="*70)
    
    if completed_years:
        print(f"\nResuming from previous progress:")
        print(f"  Already completed {len(completed_years)} years")
        print(f"  Already collected {len(existing_articles)} articles")
        print(f"  Last completed year: {max(completed_years)}")
    
    # Reconstruct articles_by_year from existing progress
    articles_by_year = {}
    for article in existing_articles:
        year = article.get('search_year')
        if year:
            if year not in articles_by_year:
                articles_by_year[year] = []
            articles_by_year[year].append(article)
    
    total_articles = len(existing_articles)
    session_number = 1
    
    # Continue from where we left off
    years_to_scrape = [y for y in range(end_year, start_year - 1, -1) if y not in completed_years]
    
    while years_to_scrape:
        print(f"\n{'#'*70}")
        print(f"SESSION {session_number}")
        print(f"Years remaining: {len(years_to_scrape)}")
        print(f"{'#'*70}")
        
        request_counter = {'count': 0}
        session_start_time = datetime.now()
        
        # Scrape years until we hit the request limit
        years_completed_this_session = []
        
        for year in years_to_scrape[:]:  # Copy list to safely modify during iteration
            # Check if we've hit the request limit
            if request_counter['count'] >= requests_per_session:
                print(f"\n{'='*70}")
                print(f"SESSION {session_number} COMPLETE")
                print(f"Requests made: {request_counter['count']}")
                print(f"Years completed this session: {len(years_completed_this_session)}")
                print(f"{'='*70}")
                break
            
            try:
                articles = scrape_year(year, base_url, request_counter)
                articles_by_year[year] = articles
                total_articles += len(articles)
                years_completed_this_session.append(year)
                years_to_scrape.remove(year)
                
                print(f"Total requests this session: {request_counter['count']}/{requests_per_session}")
                print(f"Total articles collected (all time): {total_articles}")
                
                # Save progress after each year
                save_progress(articles_by_year, total_articles)
                
                # Delay between years
                if years_to_scrape and request_counter['count'] < requests_per_session:
                    delay = random.uniform(15, 25)
                    print(f"\nWaiting {delay:.1f} seconds before next year...")
                    time.sleep(delay)
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Saving progress...")
                save_final_results(articles_by_year, total_articles)
                return
            except Exception as e:
                print(f"\nError processing year {year}: {e}")
                continue
        
        # Check if we're done
        if not years_to_scrape:
            print(f"\n{'#'*70}")
            print(f"ALL YEARS COMPLETE!")
            print(f"{'#'*70}")
            save_final_results(articles_by_year, total_articles)
            break
        
        # Calculate wait time
        session_end_time = datetime.now()
        session_duration = session_end_time - session_start_time
        
        # Wait break_hours before next session
        resume_time = session_end_time + timedelta(hours=break_hours)
        
        print(f"\n{'='*70}")
        print(f"TAKING A BREAK TO RESPECT RATE LIMITS")
        print(f"{'='*70}")
        print(f"Session duration: {session_duration}")
        print(f"Current time: {session_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Resume time: {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Waiting {break_hours} hours...")
        print(f"\nProgress saved. Years remaining: {len(years_to_scrape)}")
        print(f"You can safely Ctrl+C now and resume later, or let it continue.")
        print(f"{'='*70}")
        
        # Sleep for break_hours
        time.sleep(break_hours * 3600)
        
        session_number += 1


def main():
    """Main execution function."""
    # Scrape continuously with 900 requests per session, 24 hour breaks
    # Google Scholar limit: ~1000 requests per day
    # Estimated: ~900 requests × 7.5 sec = ~1.9 hours per session
    # One session per day with 24 hour breaks ensures we stay under limit
    # Total time: ~56 days for all years (1970-2025)
    scrape_continuous(
        start_year=1970,
        end_year=2025,
        requests_per_session=900,
        break_hours=24
    )


if __name__ == '__main__':
    main()
