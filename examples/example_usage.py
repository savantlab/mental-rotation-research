#!/usr/bin/env python3
"""
Example usage of mental-rotation-research as a Python library.

This demonstrates how to use the package programmatically rather than via CLI.
"""

import sys
from pathlib import Path

# Add parent directory to path if running directly
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from scripts (these will be organized into proper modules later)
from scripts.manage_reading_list import load_reading_list, add_article
from scripts.analyze_data import load_latest_data, basic_stats, top_cited
import json


def example_reading_list():
    """Example: Working with the reading list."""
    print("=" * 70)
    print("EXAMPLE: Reading List Management")
    print("=" * 70)
    
    # Load reading list
    data = load_reading_list()
    articles = data['reading_list']
    
    print(f"\nTotal articles in reading list: {len(articles)}")
    
    # Show first 3 articles
    print("\nFirst 3 articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Authors: {article['authors']}")
        print(f"   Year: {article['year']} | Citations: {article['citations']}")
        print(f"   Tags: {', '.join(article.get('tags', []))}")
    
    # Filter by tag
    aphantasia_papers = [a for a in articles if 'aphantasia' in a.get('tags', [])]
    print(f"\n\nPapers tagged 'aphantasia': {len(aphantasia_papers)}")


def example_data_analysis():
    """Example: Analyzing collected articles."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Data Analysis")
    print("=" * 70)
    
    # Load latest dataset
    try:
        df = load_latest_data()
        
        # Print basic statistics
        print(f"\nDataset contains {len(df)} articles")
        print(f"Years covered: {df['search_year'].nunique()}")
        
        # Show top 5 most cited
        print("\nTop 5 most cited articles:")
        df['citations'] = df['citations'].astype(int)
        top5 = df.nlargest(5, 'citations')[['title', 'citations', 'year']]
        
        for idx, row in top5.iterrows():
            print(f"  [{row['citations']:4d}] {row['title'][:60]}... ({row['year']})")
        
    except FileNotFoundError:
        print("\nNo dataset found. Run scraper first to collect articles.")


def example_search_articles():
    """Example: Search within collected articles."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Searching Articles")
    print("=" * 70)
    
    try:
        df = load_latest_data()
        
        # Search for papers about fMRI
        search_term = "fmri"
        matches = df[
            df['title'].str.contains(search_term, case=False, na=False) |
            df['abstract'].str.contains(search_term, case=False, na=False)
        ]
        
        print(f"\nFound {len(matches)} articles mentioning '{search_term}'")
        
        # Show top 3 most cited fMRI papers
        matches = matches.sort_values('citations', ascending=False)
        print(f"\nTop 3 most cited '{search_term}' papers:")
        for idx, row in matches.head(3).iterrows():
            print(f"  [{int(row['citations']):4d}] {row['title'][:60]}...")
        
    except FileNotFoundError:
        print("\nNo dataset found. Run scraper first to collect articles.")


def example_export_bibtex():
    """Example: Export citations in BibTeX format."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Export BibTeX Citations")
    print("=" * 70)
    
    data = load_reading_list()
    articles = data['reading_list']
    
    print("\nExporting BibTeX for first 2 articles:\n")
    
    for i, article in enumerate(articles[:2], 1):
        # Generate simple BibTeX entry
        # Clean title for citation key
        first_word = article['title'].split()[0].lower()
        year = article.get('year', 'YEAR')
        key = f"{first_word}{year}"
        
        # Get first author last name
        authors_str = article['authors']
        if authors_str and authors_str != 'N/A':
            first_author = authors_str.split(',')[0]
            authors_bibtex = authors_str.replace(' and ', ' and ').replace(',', ' and')
        else:
            authors_bibtex = 'Unknown'
        
        print(f"@article{{{key},")
        print(f"  title = {{{article['title']}}},")
        print(f"  author = {{{authors_bibtex}}},")
        print(f"  year = {{{year}}},")
        print(f"  url = {{{article['url']}}}")
        print("}\n")


if __name__ == '__main__':
    # Run all examples
    example_reading_list()
    example_data_analysis()
    example_search_articles()
    example_export_bibtex()
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
