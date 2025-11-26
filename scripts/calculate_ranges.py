#!/usr/bin/env python3
"""
Calculate optimal year ranges for scraping based on result counts.
Shows the plan without actually scraping.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import secrets
import time


class RateLimiter:
    """Simple rate limiter for range calculation queries."""
    
    def __init__(self, max_concurrent=1, delay_min=5, delay_max=10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.last_request_time = 0
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        await self.semaphore.acquire()
        
        async with self.lock:
            delay = self.delay_min + secrets.randbelow(self.delay_max - self.delay_min + 1)
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < delay:
                await asyncio.sleep(delay - time_since_last)
            self.last_request_time = time.time()
            return delay
    
    def release(self):
        self.semaphore.release()


async def get_total_results(session, url, rate_limiter):
    """Get total results count from a Google Scholar query."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    await rate_limiter.acquire()
    
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 429:
                print("  ⚠ Rate limited!")
                return None
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for "Page X of Y results"
            import re
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
    except Exception as e:
        print(f"  ⚠ Error: {e}")
        return None
    finally:
        rate_limiter.release()


async def calculate_ranges(start_year=1970, end_year=2023, max_results_per_range=800):
    """Calculate optimal year ranges based on result counts."""
    
    print("="*70)
    print("CALCULATING OPTIMAL YEAR RANGES FOR MENTAL ROTATION")
    print("="*70)
    print(f"Years: {start_year}-{end_year}")
    print(f"Target: ~{max_results_per_range} results per range")
    print("="*70)
    print()
    
    # Query each year
    base_url = 'https://scholar.google.com/scholar?as_ylo={year}&as_yhi={year}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1&scisbd=1'
    rate_limiter = RateLimiter(max_concurrent=1, delay_min=5, delay_max=10)
    
    year_counts = {}
    
    print("Querying individual years...")
    async with aiohttp.ClientSession() as session:
        for year in range(start_year, end_year + 1):
            url = base_url.format(year=year)
            total = await get_total_results(session, url, rate_limiter)
            year_counts[year] = total if total else 0
            print(f"  {year}: {year_counts[year]:4d} results")
    
    # Group years into ranges
    print("\nGrouping into ranges...")
    ranges = []
    current_start = start_year
    current_total = 0
    
    for year in range(start_year, end_year + 1):
        year_count = year_counts[year]
        
        if current_total + year_count > max_results_per_range and current_total > 0:
            ranges.append((current_start, year - 1))
            current_start = year
            current_total = year_count
        else:
            current_total += year_count
    
    # Add final range
    if current_start <= end_year:
        ranges.append((current_start, end_year))
    
    print(f"\nCreated {len(ranges)} ranges:")
    for i, (start, end) in enumerate(ranges, 1):
        calculated = sum(year_counts[y] for y in range(start, end + 1))
        print(f"  Range {i}: {start}-{end} (~{calculated} results)")
    
    # Verify ranges
    print("\nVerifying with actual range queries...")
    range_url = 'https://scholar.google.com/scholar?as_ylo={start}&as_yhi={end}&q=%22mental+rotation%22&hl=en&as_sdt=0,47&as_vis=1&scisbd=1'
    
    async with aiohttp.ClientSession() as session:
        for start, end in ranges:
            url = range_url.format(start=start, end=end)
            actual = await get_total_results(session, url, rate_limiter)
            calculated = sum(year_counts[y] for y in range(start, end + 1))
            
            if actual:
                diff = abs(actual - calculated)
                status = "✓" if diff < 50 else "⚠"
                print(f"  {status} {start}-{end}: {actual} actual vs {calculated} calculated (diff: {diff})")
            else:
                print(f"  ⚠ {start}-{end}: Could not verify")
    
    print("\n" + "="*70)
    print("CALCULATION COMPLETE")
    print("="*70)


if __name__ == '__main__':
    asyncio.run(calculate_ranges(start_year=1970, end_year=2023, max_results_per_range=800))
