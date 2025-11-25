#!/usr/bin/env python3
"""
Collect articles about mental rotation from Google Scholar.
"""

import json
import time
from datetime import datetime
from scholarly import scholarly, ProxyGenerator
import pandas as pd


def search_mental_rotation(max_results=100):
    """
    Search Google Scholar for articles about mental rotation.
    
    Args:
        max_results: Maximum number of results to retrieve
        
    Returns:
        List of article dictionaries
    """
    print(f"Searching for 'mental rotation' articles...")
    print("Setting up proxy to avoid blocking...")
    
    # Set up proxy to avoid being blocked
    try:
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)
        print("Proxy setup successful.")
    except Exception as e:
        print(f"Warning: Could not set up proxy: {e}")
        print("Continuing without proxy...")
    
    search_query = scholarly.search_pubs('mental rotation')
    articles = []
    
    for i, article in enumerate(search_query):
        if i >= max_results:
            break
            
        try:
            article_data = {
                'title': article.get('bib', {}).get('title', 'N/A'),
                'author': article.get('bib', {}).get('author', 'N/A'),
                'year': article.get('bib', {}).get('pub_year', 'N/A'),
                'citation_count': article.get('num_citations', 0),
                'journal': article.get('bib', {}).get('venue', 'N/A'),
                'abstract': article.get('bib', {}).get('abstract', 'N/A'),
                'url': article.get('pub_url', 'N/A'),
                'scholar_id': article.get('url_scholarbib', 'N/A')
            }
            
            articles.append(article_data)
            print(f"Collected {i+1}/{max_results}: {article_data['title'][:50]}...")
            
            # Be respectful to Google Scholar's servers
            time.sleep(2)
            
        except Exception as e:
            print(f"Error processing article {i+1}: {e}")
            continue
    
    return articles


def save_results(articles, output_dir='data'):
    """Save articles to CSV and JSON formats."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as CSV
    df = pd.DataFrame(articles)
    csv_path = f'{output_dir}/mental_rotation_articles_{timestamp}.csv'
    df.to_csv(csv_path, index=False)
    print(f"\nSaved {len(articles)} articles to {csv_path}")
    
    # Save as JSON
    json_path = f'{output_dir}/mental_rotation_articles_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(articles)} articles to {json_path}")
    
    return df


def main():
    """Main execution function."""
    print("=" * 60)
    print("Mental Rotation Article Collection")
    print("=" * 60)
    
    # Collect articles
    articles = search_mental_rotation(max_results=50)
    
    # Save results
    if articles:
        df = save_results(articles)
        
        # Print summary statistics
        print("\n" + "=" * 60)
        print("Summary Statistics")
        print("=" * 60)
        print(f"Total articles collected: {len(articles)}")
        print(f"Year range: {df['year'].min()} - {df['year'].max()}")
        print(f"Average citations: {df['citation_count'].mean():.1f}")
        print(f"Most cited: {df['citation_count'].max()}")
    else:
        print("No articles collected.")


if __name__ == '__main__':
    main()
