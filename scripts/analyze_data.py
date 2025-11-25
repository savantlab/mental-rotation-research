#!/usr/bin/env python3
"""
Analyze collected mental rotation articles.
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)


def load_latest_data():
    """Load the most recent data file."""
    # Load the complete dataset
    with open('data/mental_rotation_complete_20251123_133107.json', 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    return df


def basic_stats(df):
    """Print basic statistics."""
    print("="*70)
    print("BASIC STATISTICS")
    print("="*70)
    print(f"Total articles collected: {len(df)}")
    print(f"Years covered: {df['search_year'].nunique()}")
    print(f"\nArticles per year:")
    year_counts = df['search_year'].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"  {year}: {count:3d} articles")
    
    # Publication year vs search year
    df['pub_year'] = pd.to_numeric(df['year'], errors='coerce')
    print(f"\nPublication year range: {df['pub_year'].min():.0f} - {df['pub_year'].max():.0f}")
    
    # Citations
    df['citations'] = pd.to_numeric(df['citations'], errors='coerce')
    print(f"\nCitation statistics:")
    print(f"  Total citations: {df['citations'].sum():.0f}")
    print(f"  Average citations per article: {df['citations'].mean():.1f}")
    print(f"  Median citations: {df['citations'].median():.0f}")
    print(f"  Most cited article: {df['citations'].max():.0f} citations")
    
    return df


def top_cited(df, n=20):
    """Show top cited articles."""
    print("\n" + "="*70)
    print(f"TOP {n} MOST CITED ARTICLES")
    print("="*70)
    
    top = df.nlargest(n, 'citations')[['title', 'authors', 'pub_year', 'citations', 'search_year']]
    
    for idx, row in top.iterrows():
        cites = int(row['citations']) if pd.notna(row['citations']) else 0
        year = int(row['pub_year']) if pd.notna(row['pub_year']) else 'N/A'
        print(f"\n[{cites:4d} citations] {row['title']}")
        print(f"  Authors: {row['authors'][:80]}")
        print(f"  Year: {year} (found in {row['search_year']} search)")


def author_analysis(df):
    """Analyze author patterns."""
    print("\n" + "="*70)
    print("AUTHOR ANALYSIS")
    print("="*70)
    
    # Extract first authors (before first comma or 'and')
    first_authors = []
    for authors in df['authors']:
        if authors and authors != 'N/A':
            # Get first author
            first = re.split(r',|and', str(authors))[0].strip()
            if first:
                first_authors.append(first)
    
    if first_authors:
        author_counts = Counter(first_authors)
        print(f"\nMost prolific first authors (top 15):")
        for author, count in author_counts.most_common(15):
            print(f"  {author}: {count} articles")


def publication_venue_analysis(df):
    """Analyze publication venues."""
    print("\n" + "="*70)
    print("PUBLICATION VENUE ANALYSIS")
    print("="*70)
    
    # Clean up publication names
    venues = df['publication'].value_counts()
    
    print(f"\nMost common publication venues (top 15):")
    for venue, count in venues.head(15).items():
        if venue != 'N/A':
            print(f"  {count:3d} articles: {venue[:60]}")


def keyword_analysis(df):
    """Analyze common keywords in titles and abstracts."""
    print("\n" + "="*70)
    print("KEYWORD ANALYSIS")
    print("="*70)
    
    # Combine titles and abstracts
    all_text = ' '.join(df['title'].fillna('') + ' ' + df['abstract'].fillna(''))
    all_text = all_text.lower()
    
    # Common keywords related to mental rotation
    keywords = [
        'spatial', 'cognitive', 'rotation', 'mental', 'imagery',
        'visuospatial', 'task', 'performance', 'gender', 'sex',
        'brain', 'fmri', 'neural', 'training', 'ability',
        'object', '3d', 'three-dimensional', 'parietal',
        'working memory', 'age', 'children', 'development'
    ]
    
    keyword_counts = {}
    for kw in keywords:
        count = all_text.count(kw)
        if count > 0:
            keyword_counts[kw] = count
    
    print("\nKeyword frequency in titles and abstracts:")
    for kw, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {kw:20s}: {count:4d} occurrences")


def create_visualizations(df):
    """Create visualizations."""
    print("\n" + "="*70)
    print("CREATING VISUALIZATIONS")
    print("="*70)
    
    df['pub_year'] = pd.to_numeric(df['year'], errors='coerce')
    df['citations'] = pd.to_numeric(df['citations'], errors='coerce')
    
    # 1. Articles by search year
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Search year distribution
    year_counts = df['search_year'].value_counts().sort_index()
    axes[0, 0].bar(year_counts.index, year_counts.values, color='steelblue')
    axes[0, 0].set_xlabel('Search Year')
    axes[0, 0].set_ylabel('Number of Articles')
    axes[0, 0].set_title('Articles Collected by Search Year')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Citation distribution
    axes[0, 1].hist(df['citations'].dropna(), bins=30, color='coral', edgecolor='black')
    axes[0, 1].set_xlabel('Citation Count')
    axes[0, 1].set_ylabel('Number of Articles')
    axes[0, 1].set_title('Distribution of Citations')
    axes[0, 1].set_yscale('log')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Top 15 most cited
    top15 = df.nlargest(15, 'citations')[['title', 'citations']].copy()
    top15['short_title'] = top15['title'].str[:40] + '...'
    axes[1, 0].barh(range(len(top15)), top15['citations'], color='green')
    axes[1, 0].set_yticks(range(len(top15)))
    axes[1, 0].set_yticklabels(top15['short_title'], fontsize=8)
    axes[1, 0].set_xlabel('Citations')
    axes[1, 0].set_title('Top 15 Most Cited Articles')
    axes[1, 0].invert_yaxis()
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # Citations by search year
    year_cites = df.groupby('search_year')['citations'].agg(['mean', 'median', 'sum'])
    x = year_cites.index
    axes[1, 1].bar(x, year_cites['mean'], color='purple', alpha=0.7, label='Mean')
    axes[1, 1].set_xlabel('Search Year')
    axes[1, 1].set_ylabel('Average Citations')
    axes[1, 1].set_title('Average Citations by Search Year')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/analysis_overview.png', dpi=300, bbox_inches='tight')
    print("  Saved: results/analysis_overview.png")
    
    plt.close()


def main():
    """Main analysis function."""
    print("="*70)
    print("MENTAL ROTATION ARTICLES ANALYSIS")
    print("="*70)
    
    # Load data
    df = load_latest_data()
    
    # Run analyses
    df = basic_stats(df)
    top_cited(df)
    author_analysis(df)
    publication_venue_analysis(df)
    keyword_analysis(df)
    
    # Create visualizations
    create_visualizations(df)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
