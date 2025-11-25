#!/usr/bin/env python3
"""
Scrape Google Scholar for mental rotation articles using direct HTTP requests.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime
import random


def get_all_articles(query_url, max_articles=None):
    """
    Get all articles from Google Scholar search results.
    
    Args:
        query_url: The Google Scholar search URL
        max_articles: Maximum number of articles to retrieve (None = all, up to 1000)
        
    Returns:
        List of article dictionaries
    
    Note:
        Google Scholar limits results to approximately 1000 articles (100 pages).
    """
    all_articles = []
    page = 0
    MAX_PAGES = 100  # Google Scholar's limit
    
    print(f"Starting to collect {'all available' if max_articles is None else max_articles} articles...")
    print(f"Note: Google Scholar limits to ~1000 results (100 pages max)")
    
    while True:
        # Stop if we've reached Google Scholar's page limit
        if page >= MAX_PAGES:
            print(f"\nReached Google Scholar's maximum page limit (100 pages).")
            break
        
        # Stop if we've reached max_articles
        if max_articles and len(all_articles) >= max_articles:
            print(f"\nReached maximum of {max_articles} articles.")
            break
        
        # Scrape one page
        start = page * 10
        if page == 0:
            url = query_url
        else:
            separator = '&' if '?' in query_url else '?'
            url = f"{query_url}{separator}start={start}"
        
        print(f"\nScraping page {page + 1} (results {start + 1}-{start + 10})...")
        
        # Get articles from this page
        page_articles = scrape_single_page(url, page)
        
        # If no articles found, we've reached the end
        if not page_articles:
            print(f"\nNo more results found. Stopping.")
            break
        
        all_articles.extend(page_articles)
        page += 1
        
        # Random delay between requests
        delay = random.uniform(3, 7)
        print(f"Collected {len(all_articles)} articles so far. Waiting {delay:.1f}s...")
        time.sleep(delay)
    
    return all_articles


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
        
        print(f"Found {len(results)} results on this page")
        
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
                print(f"  [{article['position']}] {article['title'][:60]}... (Citations: {article['citations']})")
            
            except Exception as e:
                print(f"  Error parsing result {idx + 1}: {e}")
                continue
    
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
    
    return articles


def scrape_google_scholar(query_url, max_pages=5):
    """
    Scrape Google Scholar search results.
    
    Args:
        query_url: The Google Scholar search URL
        max_pages: Maximum number of pages to scrape
        
    Returns:
        List of article dictionaries
    """
    articles = []
    
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    for page in range(max_pages):
        # Calculate start parameter for pagination (0, 10, 20, etc.)
        start = page * 10
        
        # Add start parameter for pagination
        if page == 0:
            url = query_url
        else:
            separator = '&' if '?' in query_url else '?'
            url = f"{query_url}{separator}start={start}"
        
        print(f"\nScraping page {page + 1} (results {start + 1}-{start + 10})...")
        print(f"URL: {url}")
        
        try:
            # Make the request
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all result entries
            results = soup.find_all('div', class_='gs_ri')
            
            if not results:
                print(f"No results found on page {page + 1}. Stopping.")
                break
            
            print(f"Found {len(results)} results on this page")
            
            # Extract information from each result
            for idx, result in enumerate(results):
                try:
                    article = {}
                    
                    # Title
                    title_tag = result.find('h3', class_='gs_rt')
                    if title_tag:
                        # Remove citation links [PDF], [HTML], etc.
                        for span in title_tag.find_all('span'):
                            span.decompose()
                        article['title'] = title_tag.get_text().strip()
                        
                        # URL
                        link = title_tag.find('a')
                        article['url'] = link['href'] if link and link.has_attr('href') else 'N/A'
                    else:
                        article['title'] = 'N/A'
                        article['url'] = 'N/A'
                    
                    # Authors, journal, year (in gs_a tag)
                    info_tag = result.find('div', class_='gs_a')
                    if info_tag:
                        info_text = info_tag.get_text()
                        parts = info_text.split(' - ')
                        
                        article['authors'] = parts[0].strip() if len(parts) > 0 else 'N/A'
                        article['publication'] = parts[1].strip() if len(parts) > 1 else 'N/A'
                        
                        # Extract year from publication info
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
                    article['page'] = page + 1
                    article['position'] = start + idx + 1
                    
                    articles.append(article)
                    print(f"  [{article['position']}] {article['title'][:60]}... (Citations: {article['citations']})")
                
                except Exception as e:
                    print(f"  Error parsing result {idx + 1}: {e}")
                    continue
            
            # Random delay between requests to be respectful
            if page < max_pages - 1:
                delay = random.uniform(3, 7)
                print(f"Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
        
        except requests.RequestException as e:
            print(f"Error fetching page {page + 1}: {e}")
            break
    
    return articles


def save_results(articles, output_dir='data'):
    """Save articles to CSV and JSON formats."""
    if not articles:
        print("No articles to save.")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as CSV
    df = pd.DataFrame(articles)
    csv_path = f'{output_dir}/scholar_results_{timestamp}.csv'
    df.to_csv(csv_path, index=False)
    print(f"\nSaved {len(articles)} articles to {csv_path}")
    
    # Save as JSON
    json_path = f'{output_dir}/scholar_results_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(articles)} articles to {json_path}")
    
    return df


def main():
    """Main execution function."""
    print("=" * 70)
    print("Google Scholar Mental Rotation Scraper")
    print("=" * 70)
    
    # The search URL from the user
    query_url = 'https://scholar.google.com/scholar?hl=en&as_sdt=0,47&as_vis=1&q=%22mental+rotation%22&scisbd=1'
    
    # Scrape all articles (up to Google Scholar's limit)
    # Change max_articles parameter to limit results, e.g., max_articles=100
    articles = get_all_articles(query_url, max_articles=None)
    
    # Save results
    if articles:
        df = save_results(articles)
        
        # Print summary statistics
        print("\n" + "=" * 70)
        print("Summary Statistics")
        print("=" * 70)
        print(f"Total articles collected: {len(articles)}")
        
        if df is not None:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df['citations'] = pd.to_numeric(df['citations'], errors='coerce')
            
            print(f"Year range: {df['year'].min():.0f} - {df['year'].max():.0f}")
            print(f"Average citations: {df['citations'].mean():.1f}")
            print(f"Median citations: {df['citations'].median():.1f}")
            print(f"Most cited: {df['citations'].max():.0f}")
            
            print("\nTop 5 most cited articles:")
            top5 = df.nlargest(5, 'citations')[['title', 'authors', 'year', 'citations']]
            for idx, row in top5.iterrows():
                print(f"  [{row['citations']:.0f}] {row['title'][:60]}... ({row['year']:.0f})")
    else:
        print("No articles collected.")


if __name__ == '__main__':
    main()
