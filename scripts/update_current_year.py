#!/usr/bin/env python3
"""
Monthly update script to collect new publications from current year.
Checks for new articles and appends to existing collection.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime
import os
import sys

# Add parent directory to path to import from scrape_async
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def scrape_page(session, url, page_num):
    """Scrape a single page."""
    articles = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 429:
                print(f"    Page {page_num + 1}: Rate limited!")
                return articles
            
            response.raise_for_status()
            html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
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
                    print(f"    Error parsing result {idx + 1}: {e}")
                    continue
        
        # Randomize delay between requests (30-50 seconds) using secure random
        import secrets
        delay = 30 + secrets.randbelow(21)  # 30 to 50 seconds
        await asyncio.sleep(delay)
        
    except Exception as e:
        print(f"    Error fetching page {page_num + 1}: {e}")
    
    return articles


async def get_total_results(session, url):
    """Get total number of results."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 429:
                return None
            
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for pagination text
            import re
            for div in soup.find_all('div'):
                text = div.get_text()
                match = re.search(r'Page\\s+\\d+\\s+of\\s+(\\d+)\\s+results?', text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            # Fallback
            match = re.search(r'About\\s+([\\d,]+)\\s+results?', html, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(',', ''))
            
            return None
            
    except Exception as e:
        print(f"    Error getting total: {e}")
        return None


async def scrape_current_year():
    """Scrape current year for new publications."""
    current_year = datetime.now().year
    
    print("="*70)
    print(f"Monthly Update: Checking {current_year} for New Publications")
    print("="*70)
    
    base_url = f'https://scholar.google.com/scholar?as_ylo={current_year}&as_yhi={current_year}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1&scisbd=1'
    
    async with aiohttp.ClientSession() as session:
        # Get total results
        print(f"\\nChecking total results for {current_year}...")
        total_results = await get_total_results(session, base_url)
        
        if total_results:
            # Google Scholar limit: 999 results = 100 pages max
            pages_needed = min((total_results + 9) // 10, 100)
            print(f"Found {total_results} results → {pages_needed} pages to scrape (max 100)")
        else:
            print("Could not detect total, scraping first 10 pages")
            pages_needed = 10
        
        # Scrape all pages sequentially
        all_articles = []
        for page in range(pages_needed):
            start = page * 10
            if start == 0:
                url = base_url
            else:
                url = f"{base_url}&start={start}"
            
            print(f"\\nScraping page {page + 1}/{pages_needed}...")
            articles = await scrape_page(session, url, page)
            all_articles.extend(articles)
            print(f"  Found {len(articles)} articles (Total: {len(all_articles)})")
        
        return current_year, all_articles


def load_existing_data():
    """Load existing data to check for duplicates."""
    import glob
    
    # Find most recent complete dataset
    json_files = glob.glob('data/mental_rotation_complete_*.json')
    if not json_files:
        return []
    
    latest_file = max(json_files)
    print(f"Loading existing data from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        return json.load(f)


def merge_and_save(year, new_articles):
    """Merge new articles with existing data and save."""
    # Load existing data
    existing_articles = load_existing_data()
    
    # Create set of existing URLs for deduplication
    existing_urls = {article['url'] for article in existing_articles if article.get('url')}
    
    # Filter out duplicates
    unique_new_articles = []
    duplicates = 0
    
    for article in new_articles:
        article['search_year'] = year
        if article.get('url') not in existing_urls:
            unique_new_articles.append(article)
        else:
            duplicates += 1
    
    print(f"\\n{'='*70}")
    print(f"Deduplication Results")
    print(f"{'='*70}")
    print(f"New articles found: {len(unique_new_articles)}")
    print(f"Duplicates skipped: {duplicates}")
    
    if not unique_new_articles:
        print("\\nNo new articles to add.")
        return
    
    # Merge with existing
    all_articles = existing_articles + unique_new_articles
    
    # Save updated collection
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as CSV
    df = pd.DataFrame(all_articles)
    csv_path = f'data/mental_rotation_complete_{timestamp}.csv'
    df.to_csv(csv_path, index=False)
    print(f"\\nSaved {len(all_articles)} total articles to {csv_path}")
    
    # Save as JSON
    json_path = f'data/mental_rotation_complete_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_articles)} total articles to {json_path}")
    
    # Save update log
    log_entry = {
        'update_date': timestamp,
        'year_checked': year,
        'new_articles': len(unique_new_articles),
        'total_articles': len(all_articles),
        'duplicates_found': duplicates
    }
    
    log_file = 'data/update_log.json'
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log = json.load(f)
    else:
        log = []
    
    log.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"\\nUpdate logged to {log_file}")


async def main():
    """Main execution."""
    year, articles = await scrape_current_year()
    
    if articles:
        merge_and_save(year, articles)
    else:
        print("\\nNo articles collected.")


if __name__ == '__main__':
    asyncio.run(main())
