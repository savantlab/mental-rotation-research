#!/usr/bin/env python3
"""
Async version of Google Scholar scraper with rate-limited requests.
Makes scraping significantly faster while respecting rate limits.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import random
import secrets
import os


# Rate limiting settings
MAX_PARALLEL_REQUESTS = 3  # Number of parallel requests (conservative)
REQUEST_DELAY_MIN = 30  # Minimum seconds between requests
REQUEST_DELAY_MAX = 50  # Maximum seconds between requests (randomized)
MAX_REQUESTS_PER_SESSION = 900  # Daily limit buffer
SESSION_BREAK_HOURS = 24  # Hours to wait between sessions


class RateLimiter:
    """Manages rate limiting for requests."""
    
    def __init__(self, max_concurrent=5, delay_min=30, delay_max=50):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.last_request_time = 0
        self.lock = asyncio.Lock()
        self.request_count = 0
    
    async def acquire(self):
        """Acquire permission to make a request. Returns delay used in seconds."""
        await self.semaphore.acquire()
        
        async with self.lock:
            # Random delay between min and max for each request
            delay = self.delay_min + secrets.randbelow(self.delay_max - self.delay_min + 1)
            
            # Ensure minimum delay between requests
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < delay:
                await asyncio.sleep(delay - time_since_last)
            self.last_request_time = time.time()
            self.request_count += 1
            return delay
    
    def release(self):
        """Release the semaphore."""
        self.semaphore.release()


async def scrape_single_page(session, url, page_num, rate_limiter, extract_total=False):
    """
    Scrape a single page asynchronously.
    
    Args:
        session: aiohttp ClientSession
        url: URL to scrape
        page_num: Page number (0-indexed)
        rate_limiter: RateLimiter instance
        extract_total: If True, also extract total results count from page
        
    Returns:
        List of article dictionaries, or tuple of (articles, total_results) if extract_total=True
    """
    articles = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # Acquire rate limiter and show delay
    delay_used = await rate_limiter.acquire()
    print(f"  Page {page_num + 1}: fetching (waited {delay_used}s)...")
    
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 429:
                print(f"    Page {page_num + 1}: Rate limited!")
                return articles
            
            response.raise_for_status()
            html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract total results if requested
            total_results = None
            if extract_total:
                import re
                # Look for "Page X of Y results"
                for div in soup.find_all('div'):
                    text = div.get_text()
                    match = re.search(r'Page\s+\d+\s+of\s+(\d+)\s+results?', text, re.IGNORECASE)
                    if match:
                        total_results = int(match.group(1))
                        break
                
                # Fallback: "About X results"
                if not total_results:
                    match = re.search(r'About\s+([\d,]+)\s+results?', html, re.IGNORECASE)
                    if match:
                        total_results = int(match.group(1).replace(',', ''))
            
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
                    cite_tag = result.find('div', class_='gs_fl')
                    if cite_tag:
                        cite_link = cite_tag.find('a', string=lambda x: x and 'Cited by' in x)
                        if cite_link:
                            cite_text = cite_link.get_text()
                            cite_count = cite_text.replace('Cited by ', '').strip()
                            article['citations'] = int(cite_count) if cite_count.isdigit() else 0
                        else:
                            article['citations'] = 0
                    else:
                        article['citations'] = 0
                    
                    # Related articles link
                    if cite_tag:
                        related_tag = cite_tag.find('a', string=lambda x: x and 'Related articles' in x)
                        article['related_url'] = related_tag['href'] if related_tag and related_tag.has_attr('href') else 'N/A'
                    else:
                        article['related_url'] = 'N/A'
                    
                    # Add page and position info
                    article['page'] = page_num + 1
                    article['position'] = start + idx + 1
                    
                    articles.append(article)
                
                except Exception as e:
                    print(f"    Error parsing result {idx + 1} on page {page_num + 1}: {e}")
                    continue
        
        print(f"  Page {page_num + 1}: found {len(articles)} articles")
    
    except asyncio.TimeoutError:
        print(f"    Page {page_num + 1}: Timeout")
    except Exception as e:
        print(f"    Page {page_num + 1}: Error - {e}")
    finally:
        rate_limiter.release()
    
    if extract_total:
        return articles, total_results
    return articles


async def get_total_results(session, url, rate_limiter):
    """
    Get total number of results from first page.
    
    Args:
        session: aiohttp ClientSession
        url: URL to scrape
        rate_limiter: RateLimiter instance
        
    Returns:
        Total number of results (int) or None if not found
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    await rate_limiter.acquire()
    
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 429:
                print("    Rate limited while getting total!")
                return None
            
            response.raise_for_status()
            html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for pagination text like "Page 1 of 279 results"
            import re
            for div in soup.find_all('div'):
                text = div.get_text()
                # Match "Page X of Y results" or similar patterns
                match = re.search(r'Page\s+\d+\s+of\s+(\d+)\s+results?', text, re.IGNORECASE)
                if match:
                    total_results = int(match.group(1))
                    return total_results
            
            # Fallback: look for "About X results"
            match = re.search(r'About\s+([\d,]+)\s+results?', html, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '')
                return int(total_str)
            
            return None
            
    except Exception as e:
        print(f"    Error getting total results: {e}")
        return None
    finally:
        rate_limiter.release()


async def scrape_year_async(year_range, base_url_template, max_pages=100, progress_callback=None, articles_by_year=None):
    """
    Scrape all articles for a specific year range using async requests.
    Automatically detects total results and only scrapes necessary pages.
    
    Args:
        year_range: Tuple of (start_year, end_year) or single year
        base_url_template: URL template with {year_start} and {year_end} placeholders
        max_pages: Maximum pages per year (safety limit)
        
    Returns:
        Tuple of (articles list, request count, first page articles for incremental save)
    """
    # Handle both single year and year range
    if isinstance(year_range, tuple):
        year_start, year_end = year_range
        year_label = f"{year_start}-{year_end}"
    else:
        year_start = year_end = year_range
        year_label = str(year_range)
    
    print(f"\n{'='*70}")
    print(f"Scraping years: {year_label}")
    print(f"{'='*70}")
    
    # Create rate limiter with random delays between 30-50 seconds per request
    rate_limiter = RateLimiter(
        max_concurrent=MAX_PARALLEL_REQUESTS,
        delay_min=REQUEST_DELAY_MIN,
        delay_max=REQUEST_DELAY_MAX
    )
    
    async with aiohttp.ClientSession() as session:
        # First, scrape page 1 and extract total results
        first_url = base_url_template.format(year_start=year_start, year_end=year_end)
        first_page_articles, total_results = await scrape_single_page(session, first_url, 0, rate_limiter, extract_total=True)
        
        if total_results:
            # Calculate actual pages needed (Google Scholar limit: 999 results = 100 pages max)
            pages_needed = min((total_results + 9) // 10, max_pages, 100)
            print(f"Total results: {total_results} → Need {pages_needed} pages (max 100)")
        else:
            # Fallback to max_pages if we can't detect
            pages_needed = max_pages
            print(f"Could not detect total results, using max pages: {max_pages}")
        
        # Execute pages sequentially to save progress after each
        results = []
        if pages_needed > 1:
            print(f"Scraping pages 2-{pages_needed} ({pages_needed - 1} pages)...")
            for page in range(1, pages_needed):
                start = page * 10
                url = f"{base_url_template.format(year_start=year_start, year_end=year_end)}&start={start}"
                
                # Execute page scrape
                page_result = await scrape_single_page(session, url, page, rate_limiter)
                results.append(page_result)
                
                # Save progress after each page if callback provided
                if progress_callback and articles_by_year is not None:
                    # Update current year's articles
                    current_articles = first_page_articles[:]
                    for r in results:
                        current_articles.extend(r)
                    articles_by_year[year] = current_articles
                    progress_callback(articles_by_year)
                    print(f"  💾 Saved progress: {len(current_articles)} articles from {year} so far")
        
        # Flatten results (include first page articles)
        year_articles = first_page_articles[:]
        for page_articles in results:
            year_articles.extend(page_articles)
        
        requests_made = rate_limiter.request_count
        print(f"\nYear {year} complete: {len(year_articles)} articles collected ({requests_made} requests)")
        return year_articles, requests_made, first_page_articles


def load_progress():
    """Load progress from file if it exists, or from latest completed dataset."""
    progress_file = 'data/scraping_progress.json'
    
    # First check for progress file
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\n📂 Loaded progress file: {len(data.get('articles', []))} articles, {len(data.get('years_completed', []))} years")
            return data.get('years_completed', []), data.get('articles', [])
    
    # If no progress file, check for most recent complete dataset
    import glob
    complete_files = glob.glob('data/mental_rotation_complete_*.json')
    if complete_files:
        # Get most recent file
        latest_file = max(complete_files, key=os.path.getmtime)
        print(f"\n📂 Found existing dataset: {os.path.basename(latest_file)}")
        print(f"   Loading to avoid re-scraping...")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        # Extract years from articles
        years_completed = sorted(set(a.get('search_year') for a in articles if a.get('search_year')))
        
        print(f"   ✓ Loaded {len(articles)} articles")
        print(f"   ✓ Years already scraped: {years_completed}")
        
        return years_completed, articles
    
    return [], []


def save_progress(articles_by_year, total_count):
    """Save progress to a temporary file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    all_articles = []
    for year, articles in sorted(articles_by_year.items(), reverse=True):
        for article in articles:
            article['search_year'] = year
            all_articles.append(article)
    
    if all_articles:
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
    
    all_articles = []
    for year, articles in sorted(articles_by_year.items(), reverse=True):
        for article in articles:
            article['search_year'] = year
            all_articles.append(article)
    
    # Final deduplication by URL
    seen_urls = set()
    unique_articles = []
    duplicates_removed = 0
    
    for article in all_articles:
        url = article.get('url')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
        else:
            duplicates_removed += 1
    
    if duplicates_removed > 0:
        print(f"\n⚠ Removed {duplicates_removed} duplicate(s) in final deduplication")
    
    all_articles = unique_articles
    
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
    
    # Print summary
    print(f"\n{'='*70}")
    print("Summary Statistics")
    print(f"{'='*70}")
    print(f"Total articles: {len(all_articles)}")
    print(f"Years covered: {min(articles_by_year.keys())} - {max(articles_by_year.keys())}")
    
    # Clean up progress file
    if os.path.exists('data/scraping_progress.json'):
        os.remove('data/scraping_progress.json')


async def scrape_continuous_async(start_year=1970, end_year=2025, max_requests_per_session=900):
    """
    Continuously scrape with async requests and automatic breaks.
    Uses decade ranges for better results (1970-1979, 1980-1989, etc.)
    
    Args:
        start_year: First year to scrape
        end_year: Last year to scrape
        max_requests_per_session: Max requests per session (default: 900)
    """
    # URL format: decade ranges (as_ylo to as_yhi)
    base_url = 'https://scholar.google.com/scholar?as_ylo={year_start}&as_yhi={year_end}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1&scisbd=1'
    
    # Load existing progress
    completed_years, existing_articles = load_progress()
    
    print("="*70)
    print("Async Google Scholar Scraper")
    print(f"Years: {start_year} to {end_year}")
    print(f"Requests per session: {max_requests_per_session}")
    print("="*70)
    
    if completed_years:
        print(f"\nResuming from previous progress:")
        print(f"  Completed {len(completed_years)} years")
        print(f"  Collected {len(existing_articles)} articles")
    
    # Reconstruct articles_by_year
    articles_by_year = {}
    for article in existing_articles:
        year = article.get('search_year')
        if year:
            if year not in articles_by_year:
                articles_by_year[year] = []
            articles_by_year[year].append(article)
    
    total_articles = len(existing_articles)
    session_number = 1
    
    # Create decade ranges (1970-1979, 1980-1989, ..., 2020-2025)
    decade_ranges = []
    for decade_start in range(start_year, end_year, 10):
        decade_end = min(decade_start + 9, end_year)
        decade_ranges.append((decade_start, decade_end))
    
    # Keep track of completed ranges
    completed_ranges = []
    if completed_years:
        # Mark single years (2024, 2025) as needing different handling
        decade_ranges = [(s, e) for s, e in decade_ranges if not all(y in completed_years for y in range(s, e+1))]
    
    ranges_to_scrape = decade_ranges
    
    while ranges_to_scrape:
        print(f"\n{'#'*70}")
        print(f"SESSION {session_number}")
        print(f"Decade ranges remaining: {len(ranges_to_scrape)}")
        print(f"{'#'*70}")
        
        request_count = 0
        session_start_time = datetime.now()
        
        for year_range in ranges_to_scrape[:]:
            # Check if we're approaching the limit (leave 100 request buffer)
            if request_count >= max_requests_per_session:
                print(f"\n{'='*70}")
                print(f"SESSION {session_number} COMPLETE")
                print(f"Requests made: {request_count}")
                print(f"{'='*70}")
                break
            
            # Check if we have enough headroom (at least 100 requests left for safety)
            remaining = max_requests_per_session - request_count
            if remaining < 100:
                print(f"\n{'='*70}")
                print(f"SESSION {session_number} COMPLETE (Safety Buffer)")
                print(f"Requests made: {request_count}/{max_requests_per_session}")
                print(f"Remaining: {remaining} (< 100 safety threshold)")
                print(f"{'='*70}")
                break
            
            try:
                # Define progress callback to save after each page
                def save_page_progress(articles_dict):
                    save_progress(articles_dict, sum(len(arts) for arts in articles_dict.values()))
                
                # Scrape decade range asynchronously with page-level progress saving
                articles, requests, _ = await scrape_year_async(
                    year_range, 
                    base_url, 
                    progress_callback=save_page_progress,
                    articles_by_year=articles_by_year
                )
                
                # Deduplicate by URL across all existing articles
                existing_urls = set()
                for existing_articles in articles_by_year.values():
                    for a in existing_articles:
                        existing_urls.add(a.get('url'))
                
                # Filter out duplicates
                unique_articles = [a for a in articles if a.get('url') not in existing_urls]
                duplicates_found = len(articles) - len(unique_articles)
                
                if duplicates_found > 0:
                    print(f"  ⚠ Removed {duplicates_found} duplicate(s) based on URL")
                
                # Store by range label
                range_label = f"{year_range[0]}-{year_range[1]}" if isinstance(year_range, tuple) else str(year_range)
                articles_by_year[range_label] = unique_articles
                total_articles += len(unique_articles)
                ranges_to_scrape.remove(year_range)
                
                # Track actual requests made
                request_count += requests
                remaining = max_requests_per_session - request_count
                
                print(f"✓ Total requests this session: {request_count}/{max_requests_per_session} ({remaining} remaining)")
                print(f"✓ Total articles (all time): {total_articles}")
                
                # Save progress after every year completion
                save_progress(articles_by_year, total_articles)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Saving progress...")
                save_final_results(articles_by_year, total_articles)
                return
            except Exception as e:
                print(f"\nError processing year {year}: {e}")
                continue
        
        # Check if done
        if not ranges_to_scrape:
            print(f"\n{'#'*70}")
            print(f"ALL RANGES COMPLETE!")
            print(f"{'#'*70}")
            save_final_results(articles_by_year, total_articles)
            break
        
        # Wait between sessions
        session_end_time = datetime.now()
        session_duration = session_end_time - session_start_time
        resume_time = session_end_time + timedelta(hours=SESSION_BREAK_HOURS)
        
        print(f"\n{'='*70}")
        print(f"TAKING A BREAK")
        print(f"{'='*70}")
        print(f"Session duration: {session_duration}")
        print(f"Resume time: {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Waiting {SESSION_BREAK_HOURS} hours...")
        print(f"Ranges remaining: {len(ranges_to_scrape)}")
        print(f"{'='*70}")
        
        await asyncio.sleep(SESSION_BREAK_HOURS * 3600)
        session_number += 1


def main():
    """Main execution function."""
    asyncio.run(scrape_continuous_async(
        start_year=1970,
        end_year=2025,
        max_requests_per_session=900
    ))


if __name__ == '__main__':
    main()
