#!/usr/bin/env python3
"""
Manage reading list of articles to save.
"""

import json
import sys
from datetime import datetime


READING_LIST_FILE = 'reading_list.json'


def load_reading_list():
    """Load the reading list."""
    try:
        with open(READING_LIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'reading_list': []}


def save_reading_list(data):
    """Save the reading list."""
    with open(READING_LIST_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def add_article(title, authors, url, year=None, citations=None, tags=None, notes=None):
    """Add an article to the reading list."""
    data = load_reading_list()
    
    # Check if URL already exists
    for article in data['reading_list']:
        if article['url'] == url:
            print(f"Article already in reading list: {title}")
            return
    
    article = {
        'title': title,
        'authors': authors,
        'year': year or 'N/A',
        'url': url,
        'citations': citations or 0,
        'tags': tags or [],
        'notes': notes or '',
        'date_added': datetime.now().strftime('%Y-%m-%d')
    }
    
    data['reading_list'].append(article)
    save_reading_list(data)
    print(f"Added to reading list: {title}")


def list_articles(tag_filter=None):
    """List all articles in the reading list."""
    data = load_reading_list()
    articles = data['reading_list']
    
    if tag_filter:
        articles = [a for a in articles if tag_filter in a.get('tags', [])]
    
    if not articles:
        print("Reading list is empty.")
        return
    
    print("="*70)
    print(f"READING LIST ({len(articles)} articles)")
    if tag_filter:
        print(f"Filtered by tag: {tag_filter}")
    print("="*70)
    print()
    
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   Authors: {article['authors']}")
        print(f"   Year: {article['year']} | Citations: {article['citations']}")
        print(f"   URL: {article['url']}")
        if article.get('tags'):
            print(f"   Tags: {', '.join(article['tags'])}")
        if article.get('notes'):
            print(f"   Notes: {article['notes']}")
        print(f"   Added: {article['date_added']}")
        print()


def remove_article(index):
    """Remove an article by index."""
    data = load_reading_list()
    
    if 0 < index <= len(data['reading_list']):
        removed = data['reading_list'].pop(index - 1)
        save_reading_list(data)
        print(f"Removed from reading list: {removed['title']}")
    else:
        print(f"Invalid index: {index}")


def add_from_collection(search_term):
    """Add articles from collection that match search term."""
    # Load collection data
    try:
        with open('data/mental_rotation_complete_20251123_133107.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Collection data not found.")
        return
    
    import pandas as pd
    df = pd.DataFrame(data)
    df['citations'] = pd.to_numeric(df['citations'], errors='coerce')
    
    # Search in title and abstract
    matches = df[
        df['title'].str.contains(search_term, case=False, na=False) | 
        df['abstract'].str.contains(search_term, case=False, na=False)
    ].sort_values('citations', ascending=False)
    
    if len(matches) == 0:
        print(f"No articles found matching: {search_term}")
        return
    
    print(f"\nFound {len(matches)} articles matching '{search_term}':")
    print()
    
    for idx, row in matches.iterrows():
        cites = int(row['citations']) if pd.notna(row['citations']) else 0
        print(f"{idx+1}. [{cites} cites] {row['title'][:60]}...")
    
    print("\nEnter article numbers to add (comma-separated) or 'all': ", end='')
    choice = input().strip()
    
    if choice.lower() == 'all':
        indices = matches.index.tolist()
    else:
        try:
            indices = [int(x.strip())-1 for x in choice.split(',')]
        except:
            print("Invalid input.")
            return
    
    for idx in indices:
        if idx in matches.index:
            row = matches.loc[idx]
            add_article(
                title=row['title'],
                authors=row['authors'],
                url=row['url'],
                year=row['year'],
                citations=int(row['citations']) if pd.notna(row['citations']) else 0,
                tags=[search_term],
                notes=f"Found via search: {search_term}"
            )


def export_urls():
    """Export just the URLs to a text file."""
    data = load_reading_list()
    
    if not data['reading_list']:
        print("Reading list is empty.")
        return
    
    output_file = 'reading_list_urls.txt'
    with open(output_file, 'w') as f:
        for article in data['reading_list']:
            f.write(f"{article['url']}\n")
    
    print(f"Exported {len(data['reading_list'])} URLs to {output_file}")


def main():
    """Main CLI."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_reading_list.py list [tag]")
        print("  python manage_reading_list.py add <title> <authors> <url> [year] [citations]")
        print("  python manage_reading_list.py search <term>")
        print("  python manage_reading_list.py remove <index>")
        print("  python manage_reading_list.py export")
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        tag = sys.argv[2] if len(sys.argv) > 2 else None
        list_articles(tag)
    
    elif command == 'add' and len(sys.argv) >= 5:
        title = sys.argv[2]
        authors = sys.argv[3]
        url = sys.argv[4]
        year = sys.argv[5] if len(sys.argv) > 5 else None
        citations = int(sys.argv[6]) if len(sys.argv) > 6 else None
        add_article(title, authors, url, year, citations)
    
    elif command == 'search' and len(sys.argv) >= 3:
        search_term = sys.argv[2]
        add_from_collection(search_term)
    
    elif command == 'remove' and len(sys.argv) >= 3:
        index = int(sys.argv[2])
        remove_article(index)
    
    elif command == 'export':
        export_urls()
    
    else:
        print("Invalid command or missing arguments.")


if __name__ == '__main__':
    main()
