#!/usr/bin/env python3
"""
Test scraper: Collect LAST 10 pages of 2025 results.
Uses optimized query string method with secure random delays.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import json
import secrets
import re
from datetime import datetime


async def get_total_results(session, url):
    """Get total number of results from first page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 429:
                print("❌ Rate limited! (HTTP 429)")
                return None
            elif response.status != 200:
                print(f"❌ HTTP {response.status}: {response.reason}")
                return None
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for "Page X of Y results"
            for div in soup.find_all('div'):
                text = div.get_text()
                match = re.search(r'Page\s+\d+\s+of\s+(\d+)\s+results?', text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            # Fallback: "About X results"
            match = re.search(r'About\s+([\d,]+)\s+results?', html, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(',', ''))
            
            return None
            
    except asyncio.TimeoutError:
        print(f"❌ TIMEOUT: Request took longer than 10 seconds")
        return None
    except aiohttp.ClientError as e:
        print(f"❌ NETWORK ERROR: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


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
                print(f"  ❌ Page {page_num}: Rate limited! (HTTP 429)")
                return articles
            elif response.status != 200:
                print(f"  ❌ Page {page_num}: HTTP {response.status}: {response.reason}")
                return articles
            
            html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            results = soup.find_all('div', class_='gs_ri')
            
            if not results:
                return articles
            
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
                        
                        # Extract year
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
                    
                    # Abstract
                    abstract_tag = result.find('div', class_='gs_rs')
                    article['abstract'] = abstract_tag.get_text().strip() if abstract_tag else 'N/A'
                    
                    # Citations
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
                    
                    article['page'] = page_num
                    articles.append(article)
                
                except Exception as e:
                    print(f"    Error parsing result {idx + 1}: {e}")
                    continue
        
        # Secure random delay between 30-50 seconds
        delay = 30 + secrets.randbelow(21)
        print(f"  Waiting {delay} seconds...")
        await asyncio.sleep(delay)
        
    except asyncio.TimeoutError:
        print(f"  ❌ TIMEOUT: Page {page_num} request took longer than 10 seconds")
    except aiohttp.ClientError as e:
        print(f"  ❌ NETWORK ERROR on page {page_num}: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  ❌ UNEXPECTED ERROR on page {page_num}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    return articles


async def test_last_10_pages():
    """Test scraping last 10 pages of 2025 results."""
    year = 2025
    
    print("="*70)
    print(f"TEST SCRAPER: Last 10 Pages of {year} Mental Rotation Articles")
    print("="*70)
    
    # Best query string: sorted by date, exclude patents
    base_url = f'https://scholar.google.com/scholar?q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1&scisbd=1&as_ylo={year}&as_yhi={year}'
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Get total results
        print(f"\nStep 1: Detecting total results for {year}...")
        total_results = await get_total_results(session, base_url)
        
        if not total_results:
            print("Could not detect total results. Aborting.")
            return
        
        # Google Scholar limit: 999 results = 100 pages max
        total_pages = min((total_results + 9) // 10, 100)
        print(f"  Total results: {total_results}")
        print(f"  Total pages: {total_pages} (capped at 100)")
        
        # Step 2: Calculate last 10 pages
        if total_pages <= 10:
            pages_to_scrape = list(range(1, total_pages + 1))
            print(f"\n  Only {total_pages} pages exist, scraping all of them")
        else:
            start_page = total_pages - 9  # Last 10 pages
            pages_to_scrape = list(range(start_page, total_pages + 1))
            print(f"\n  Scraping pages {start_page} to {total_pages} (last 10 pages)")
        
        # Step 3: Scrape pages
        print(f"\nStep 2: Scraping {len(pages_to_scrape)} pages...")
        all_articles = []
        
        for page_num in pages_to_scrape:
            start = (page_num - 1) * 10
            if start == 0:
                url = base_url
            else:
                url = f"{base_url}&start={start}"
            
            print(f"\nPage {page_num}/{total_pages} (start={start})...")
            articles = await scrape_page(session, url, page_num)
            all_articles.extend(articles)
            print(f"  Found {len(articles)} articles (Total: {len(all_articles)})")
        
        # Step 4: Save results
        if all_articles:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save as JSON
            json_path = f'test_2025_last10pages_{timestamp}.json'
            with open(json_path, 'w') as f:
                json.dump(all_articles, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Saved {len(all_articles)} articles to {json_path}")
            
            # Save as CSV
            df = pd.DataFrame(all_articles)
            csv_path = f'test_2025_last10pages_{timestamp}.csv'
            df.to_csv(csv_path, index=False)
            print(f"✅ Saved {len(all_articles)} articles to {csv_path}")
            
            # Summary
            print("\n" + "="*70)
            print("TEST SUMMARY")
            print("="*70)
            print(f"Year: {year}")
            print(f"Total results in {year}: {total_results}")
            print(f"Pages scraped: {len(pages_to_scrape)} (pages {pages_to_scrape[0]}-{pages_to_scrape[-1]})")
            print(f"Articles collected: {len(all_articles)}")
            print(f"Average citations: {df['citations'].mean():.1f}")
            print(f"Most recent articles: Last 10 pages sorted by date")
        else:
            print("\nNo articles collected.")


if __name__ == '__main__':
    try:
        asyncio.run(test_last_10_pages())
    except KeyboardInterrupt:
        print("\n\n❌ Script interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
