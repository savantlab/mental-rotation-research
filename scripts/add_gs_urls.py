#!/usr/bin/env python3
"""
Add Google Scholar search URLs to reading list entries.
Constructs URLs from author + title information.
"""

import json
import urllib.parse


def construct_gs_url(authors, title):
    """
    Construct Google Scholar search URL from author and title.
    
    Args:
        authors: Author string (e.g., "MR Maechler, P Cavanagh, PU Tse")
        title: Paper title
        
    Returns:
        Google Scholar search URL
    """
    # Get first author's last name
    first_author = authors.split(',')[0].strip()
    # Try to extract last name (assuming format like "MR Maechler" or "Maechler")
    author_parts = first_author.split()
    if len(author_parts) > 1:
        # Has initials, take last part as last name
        last_name = author_parts[-1]
    else:
        last_name = author_parts[0]
    
    # Construct query: author+"exact title match"
    query = f'{last_name} "{title}"'
    
    # URL encode
    encoded_query = urllib.parse.quote(query)
    
    # Construct full URL
    gs_url = f"https://scholar.google.com/scholar?q={encoded_query}"
    
    return gs_url


def add_gs_urls_to_reading_list():
    """Add Google Scholar URLs to all entries in reading list."""
    
    # Load reading list
    with open('reading_list.json', 'r') as f:
        data = json.load(f)
    
    print("="*70)
    print("ADDING GOOGLE SCHOLAR URLS")
    print("="*70)
    print()
    
    updated_count = 0
    
    for paper in data['reading_list']:
        title = paper['title']
        authors = paper['authors']
        
        # Construct GS URL
        gs_url = construct_gs_url(authors, title)
        
        # Add to paper
        paper['google_scholar_url'] = gs_url
        
        print(f"✓ {title[:60]}...")
        print(f"  GS URL: {gs_url}")
        print()
        
        updated_count += 1
    
    # Save updated reading list
    with open('reading_list.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("="*70)
    print(f"✓ Added Google Scholar URLs to {updated_count} papers")
    print("="*70)


def display_gs_urls():
    """Display all Google Scholar URLs from reading list."""
    
    with open('reading_list.json', 'r') as f:
        data = json.load(f)
    
    print("="*70)
    print("GOOGLE SCHOLAR URLS")
    print("="*70)
    print()
    
    for i, paper in enumerate(data['reading_list'], 1):
        print(f"{i}. {paper['title']}")
        print(f"   Authors: {paper['authors']}")
        
        if 'google_scholar_url' in paper:
            print(f"   GS URL: {paper['google_scholar_url']}")
        else:
            gs_url = construct_gs_url(paper['authors'], paper['title'])
            print(f"   GS URL (generated): {gs_url}")
        
        print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'display':
        display_gs_urls()
    else:
        add_gs_urls_to_reading_list()
