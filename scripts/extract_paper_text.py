#!/usr/bin/env python3
"""
Extract readable text from downloaded HTML papers.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup
import re


def clean_text(text):
    """Clean extracted text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_text_from_html(html_path):
    """Extract text from HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'header', 'footer', 'nav']):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up
        text = clean_text(text)
        
        return text
    
    except Exception as e:
        print(f"Error extracting text from {html_path}: {e}")
        return None


def main():
    """Extract text from all downloaded papers."""
    papers_dir = Path('data/reading_list_papers')
    
    if not papers_dir.exists():
        print(f"Directory not found: {papers_dir}")
        return
    
    # Find all HTML files
    html_files = list(papers_dir.glob('*.html'))
    
    if not html_files:
        print("No HTML files found")
        return
    
    print(f"Found {len(html_files)} HTML files")
    print()
    
    results = []
    
    for html_file in html_files:
        print(f"Processing: {html_file.name}")
        
        text = extract_text_from_html(html_file)
        
        if text:
            # Save as text file
            text_file = html_file.with_suffix('.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            results.append({
                'html_file': html_file.name,
                'text_file': text_file.name,
                'text_length': len(text),
                'word_count': len(text.split()),
                'preview': text[:200] + '...' if len(text) > 200 else text
            })
            
            print(f"  ✓ Extracted {len(text):,} characters ({len(text.split())} words)")
            print(f"  ✓ Saved to: {text_file.name}")
        else:
            print(f"  ✗ Failed to extract text")
        
        print()
    
    # Save summary
    summary_file = papers_dir / 'extraction_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Processed: {len(html_files)} files")
    print(f"Successful: {len(results)} files")
    print(f"Total characters: {sum(r['text_length'] for r in results):,}")
    print(f"Total words: {sum(r['word_count'] for r in results):,}")
    print(f"\nSummary saved to: {summary_file}")
    print(f"Text files saved with .txt extension")


if __name__ == '__main__':
    main()
