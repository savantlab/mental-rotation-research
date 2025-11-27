# Mental Rotation Research Project

A Python library and toolkit for scraping, managing, and analyzing mental rotation research articles from Google Scholar.

> **Quick Start**: See [QUICKSTART.md](QUICKSTART.md) to get up and running in 5 minutes.

## Features

- **Async Web Scraping**: Efficient parallel scraping with rate limiting and automatic progress saving
- **Reading List Management**: Curated collection of important papers with citation tracking
- **Data Analysis**: Built-in analysis tools with visualizations
- **CLI Tools**: Command-line interface for all major operations

## Installation

### As a Python Library

Install in editable mode for development:

```bash
git clone git@github.com:savantlab/mental-rotation-research.git
cd mental-rotation-research
pip install -e .
```

Or install directly from GitHub (once published):

```bash
pip install git+https://github.com/savantlab/mental-rotation-research.git
```

### Manual Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:savantlab/mental-rotation-research.git
   cd mental-rotation-research
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command-Line Interface

After installation, three CLI commands are available:

#### 1. Scraping Articles

```bash
# Scrape all articles (1970 to current year)
mental-rotation-scrape

# Scrape specific year range
mental-rotation-scrape --year-start 2020 --year-end 2023

# Calculate optimal year ranges without scraping
mental-rotation-scrape --calculate-ranges
```

#### 2. Analyzing Data

```bash
# Analyze collected articles
mental-rotation-analyze

# Analyze specific data file
mental-rotation-analyze --data-file data/my_articles.json

# Show top 50 most cited papers
mental-rotation-analyze --top-n 50
```

#### 3. Managing Reading List

```bash
# List all papers in reading list
mental-rotation-reading list

# Add a paper
mental-rotation-reading add "Paper Title" "Author Names" "https://url" --year 2024 --citations 42

# Remove a paper
mental-rotation-reading remove 5

# Download papers
mental-rotation-reading download

# Export URLs
mental-rotation-reading export
```

### Python Scripts

You can also run the scripts directly:

```bash
# Scrape articles
python scripts/scrape_async.py

# Analyze data
python scripts/analyze_data.py

# Manage reading list
python scripts/manage_reading_list.py list
```

### Jupyter Notebooks

Start Jupyter for interactive analysis:

```bash
jupyter notebook
```

Check out `notebooks/analysis_2024_2025.ipynb` for example analysis.

### As a Python Library

You can also use the package programmatically in your own scripts:

```python
from scripts.manage_reading_list import load_reading_list
from scripts.analyze_data import load_latest_data
import pandas as pd

# Load reading list
data = load_reading_list()
articles = data['reading_list']
print(f"Total papers: {len(articles)}")

# Filter by tag
aphantasia_papers = [a for a in articles if 'aphantasia' in a.get('tags', [])]
print(f"Aphantasia papers: {len(aphantasia_papers)}")

# Load and analyze collected dataset
df = load_latest_data()
top_cited = df.nlargest(10, 'citations')
print(top_cited[['title', 'citations', 'year']])
```

See `examples/example_usage.py` for more examples.

## Project Structure

```
mental-rotation-research/
├── mental_rotation/          # Python package
│   ├── __init__.py
│   └── cli.py               # Command-line interface
├── scripts/                 # Core scripts
│   ├── scrape_async.py     # Main async scraper
│   ├── analyze_data.py     # Data analysis tools
│   ├── manage_reading_list.py
│   └── scrape_reading_list.py
├── data/                    # Scraped data (gitignored)
├── notebooks/              # Jupyter notebooks
├── results/                # Analysis outputs
├── reading_list.json       # Curated papers
├── setup.py               # Package configuration
└── requirements.txt       # Dependencies
```

## Data Collection Details

- **Query**: Articles containing "mental rotation"
- **Years**: 1970 to present
- **Rate Limiting**: 3 parallel requests, 30-50s delays
- **Progress Saving**: Automatic checkpointing after each year
- **Deduplication**: URL-based duplicate detection
- **Citation Tracking**: Extracts citation counts from Google Scholar

## Automated Updates

A cron job is configured to update the database monthly. See `CRON_SETUP.md` for details.

## Current Status

- **280 articles** from 2024-2025 (already collected)
- **16 curated papers** in reading list
- **Historical data** (1970-2023) scheduled to scrape after rate limit cooldown

## Contributing

This is a research project maintained by Savant Lab. Feel free to fork and adapt for your own research needs.
