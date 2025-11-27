#!/usr/bin/env python3
"""
Command-line interface for mental rotation research tools.
"""

import argparse
import sys
from pathlib import Path


def scrape_main():
    """Entry point for mental-rotation-scrape command."""
    parser = argparse.ArgumentParser(
        description='Scrape mental rotation articles from Google Scholar'
    )
    parser.add_argument(
        '--year-start',
        type=int,
        default=1970,
        help='Start year for scraping (default: 1970)'
    )
    parser.add_argument(
        '--year-end',
        type=int,
        help='End year for scraping (default: current year)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='Maximum pages to scrape per year (default: 100)'
    )
    parser.add_argument(
        '--calculate-ranges',
        action='store_true',
        help='Calculate optimal year ranges without scraping'
    )
    
    args = parser.parse_args()
    
    # Import here to avoid circular dependencies
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    if args.calculate_ranges:
        from scripts import calculate_ranges
        import asyncio
        asyncio.run(calculate_ranges.main())
    else:
        from scripts import scrape_async
        import asyncio
        
        if not args.year_end:
            from datetime import datetime
            args.year_end = datetime.now().year
        
        # Use scrape_continuous_async which handles progress saving and rate limiting
        asyncio.run(scrape_async.scrape_continuous_async(
            start_year=args.year_start,
            end_year=args.year_end,
            max_requests_per_session=900
        ))


def analyze_main():
    """Entry point for mental-rotation-analyze command."""
    parser = argparse.ArgumentParser(
        description='Analyze collected mental rotation articles'
    )
    parser.add_argument(
        '--data-file',
        type=str,
        help='Path to JSON data file (default: auto-detect latest)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=20,
        help='Number of top cited articles to show (default: 20)'
    )
    
    args = parser.parse_args()
    
    # Import here to avoid circular dependencies
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts import analyze_data
    
    analyze_data.main()


def reading_main():
    """Entry point for mental-rotation-reading command."""
    parser = argparse.ArgumentParser(
        description='Manage reading list of articles'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List articles in reading list')
    list_parser.add_argument('--tag', type=str, help='Filter by tag')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add article to reading list')
    add_parser.add_argument('title', type=str, help='Article title')
    add_parser.add_argument('authors', type=str, help='Article authors')
    add_parser.add_argument('url', type=str, help='Article URL')
    add_parser.add_argument('--year', type=int, help='Publication year')
    add_parser.add_argument('--citations', type=int, help='Citation count')
    add_parser.add_argument('--tags', nargs='+', help='Tags')
    add_parser.add_argument('--notes', type=str, help='Notes')
    add_parser.add_argument('--paywall', action='store_true', help='Mark as paywalled')
    add_parser.add_argument('--no-download', action='store_true', help='Skip auto-download')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove article from reading list')
    remove_parser.add_argument('index', type=int, help='Article index')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download papers from reading list')
    download_parser.add_argument('--url', type=str, help='Specific URL to download')
    download_parser.add_argument('--index', type=int, help='Specific index to download')
    
    # Export command
    subparsers.add_parser('export', help='Export reading list URLs')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Import here to avoid circular dependencies
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts import manage_reading_list, scrape_reading_list
    
    if args.command == 'list':
        manage_reading_list.list_articles(tag_filter=args.tag)
    
    elif args.command == 'add':
        manage_reading_list.add_article(
            title=args.title,
            authors=args.authors,
            url=args.url,
            year=args.year,
            citations=args.citations,
            tags=args.tags,
            notes=args.notes,
            paywall=args.paywall,
            auto_download=not args.no_download
        )
    
    elif args.command == 'remove':
        manage_reading_list.remove_article(args.index)
    
    elif args.command == 'download':
        import sys as _sys
        if args.url:
            _sys.argv = ['scrape_reading_list.py', 'url', args.url]
        elif args.index:
            _sys.argv = ['scrape_reading_list.py', 'index', str(args.index)]
        else:
            _sys.argv = ['scrape_reading_list.py']
        scrape_reading_list.main()
    
    elif args.command == 'export':
        manage_reading_list.export_urls()


if __name__ == '__main__':
    # Default to scrape if run directly
    scrape_main()
