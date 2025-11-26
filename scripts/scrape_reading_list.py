#!/usr/bin/env python3
"""
Scrape papers from reading list URLs.
Downloads PDFs when available, otherwise extracts HTML content.
"""

import json
import asyncio
import aiohttp
from pathlib import Path
import secrets
from datetime import datetime


async def download_paper(session, paper_info, output_dir):
    """
    Download paper from URL.
    
    Args:
        session: aiohttp ClientSession
        paper_info: Dictionary with paper metadata
        output_dir: Directory to save downloaded papers
    """
    url = paper_info['url']
    title = paper_info['title']
    authors = paper_info['authors']
    year = paper_info['year']
    
    # Create safe filename from title
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    safe_title = safe_title[:100]  # Limit length
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"\n{'='*70}")
    print(f"Paper: {title[:60]}...")
    print(f"Authors: {authors}")
    print(f"Year: {year}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        async with session.get(url, headers=headers, timeout=30, allow_redirects=True) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Determine file extension
                if 'pdf' in content_type:
                    ext = 'pdf'
                    print(f"✓ Found PDF")
                else:
                    ext = 'html'
                    print(f"✓ Found HTML")
                
                # Save file
                filename = f"{year}_{safe_title}.{ext}"
                filepath = output_dir / filename
                
                content = await response.read()
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                print(f"✓ Saved: {filename} ({len(content):,} bytes)")
                
                # Random delay 5-10 seconds between downloads
                delay = 5 + secrets.randbelow(6)
                print(f"  Waiting {delay}s before next download...")
                await asyncio.sleep(delay)
                
                return {
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'url': url,
                    'filename': filename,
                    'file_type': ext,
                    'size_bytes': len(content),
                    'status': 'success',
                    'downloaded_at': datetime.now().isoformat()
                }
            else:
                print(f"✗ HTTP {response.status}: {response.reason}")
                return {
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'url': url,
                    'status': 'failed',
                    'error': f"HTTP {response.status}",
                    'downloaded_at': datetime.now().isoformat()
                }
    
    except asyncio.TimeoutError:
        print(f"✗ Timeout after 30 seconds")
        return {
            'title': title,
            'authors': authors,
            'year': year,
            'url': url,
            'status': 'failed',
            'error': 'Timeout',
            'downloaded_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        return {
            'title': title,
            'authors': authors,
            'year': year,
            'url': url,
            'status': 'failed',
            'error': str(e),
            'downloaded_at': datetime.now().isoformat()
        }


async def scrape_reading_list():
    """Main function to scrape all papers from reading list."""
    
    # Load reading list
    reading_list_path = Path('reading_list.json')
    if not reading_list_path.exists():
        print(f"✗ Error: {reading_list_path} not found")
        return
    
    with open(reading_list_path, 'r') as f:
        data = json.load(f)
    
    papers = data['reading_list']
    print(f"Found {len(papers)} papers in reading list")
    
    # Create output directory
    output_dir = Path('data/reading_list_papers')
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Download papers
    results = []
    async with aiohttp.ClientSession() as session:
        for paper in papers:
            result = await download_paper(session, paper, output_dir)
            results.append(result)
    
    # Save results
    results_file = output_dir / f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print(f"\n{'='*70}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count
    
    print(f"Total papers: {len(results)}")
    print(f"✓ Successful: {success_count}")
    print(f"✗ Failed: {failed_count}")
    
    if success_count > 0:
        pdf_count = sum(1 for r in results if r.get('file_type') == 'pdf')
        html_count = sum(1 for r in results if r.get('file_type') == 'html')
        print(f"\n  PDFs: {pdf_count}")
        print(f"  HTML: {html_count}")
    
    print(f"\nResults saved to: {results_file}")
    print(f"Papers saved to: {output_dir}")


if __name__ == '__main__':
    asyncio.run(scrape_reading_list())
