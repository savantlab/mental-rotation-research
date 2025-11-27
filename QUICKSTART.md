# Quick Start Guide

Get up and running with mental-rotation-research in 5 minutes.

## Installation

```bash
# Clone the repository
git clone git@github.com:savantlab/mental-rotation-research.git
cd mental-rotation-research

# Install the package
pip install -e .
```

## Verify Installation

Check that the CLI commands are available:

```bash
mental-rotation-scrape --help
mental-rotation-analyze --help
mental-rotation-reading --help
```

## Basic Usage

### 1. View the Reading List

See the curated collection of important papers:

```bash
mental-rotation-reading list
```

### 2. Analyze Existing Data

The repository includes 280 articles from 2024-2025. Analyze them:

```bash
mental-rotation-analyze
```

This will:
- Print statistics about the dataset
- Show top cited articles
- Identify common authors and venues
- Extract keyword frequencies
- Generate visualizations in `results/`

### 3. View Analysis Notebook

For interactive exploration:

```bash
jupyter notebook notebooks/analysis_2024_2025.ipynb
```

### 4. Scrape More Data (Optional)

**⚠️ Warning**: Google Scholar has strict rate limits. The scraper is already scheduled to run automatically.

To scrape specific years:

```bash
# Test with a small range first
mental-rotation-scrape --year-start 2023 --year-end 2023
```

### 5. Use as a Python Library

Create a script like this:

```python
from scripts.manage_reading_list import load_reading_list
from scripts.analyze_data import load_latest_data

# Load reading list
data = load_reading_list()
print(f"Reading list has {len(data['reading_list'])} papers")

# Load dataset
df = load_latest_data()
print(f"Dataset has {len(df)} articles")

# Find papers about specific topics
fmri_papers = df[df['title'].str.contains('fmri', case=False, na=False)]
print(f"Found {len(fmri_papers)} fMRI-related papers")
```

See `examples/example_usage.py` for more examples.

## Next Steps

- **Add papers to reading list**: `mental-rotation-reading add "Title" "Authors" "URL"`
- **Run full analysis**: Edit and run the Jupyter notebooks
- **Explore the data**: Check `data/` directory for JSON files
- **Customize scraping**: Edit `scripts/scrape_async.py` to change search queries

## Common Issues

### "No dataset found" Error

The analysis tools need data to work with. Either:
1. Wait for the scheduled scraper to complete (check `atq` for scheduled jobs)
2. Run `mental-rotation-scrape` manually (be careful of rate limits)

### Rate Limiting

If you see "Rate limited" messages:
- The scraper automatically saves progress and waits 24 hours
- Don't try to bypass rate limits - it can lead to temporary blocks
- The scheduled cron job handles this automatically

### Package Not Found

If CLI commands aren't working:
```bash
# Reinstall in editable mode
pip install -e .

# Or add to PATH manually
export PATH="$PATH:$(python -m site --user-base)/bin"
```

## Getting Help

- Check the main README for detailed documentation
- Look at example scripts in `examples/`
- Review existing notebooks in `notebooks/`
- Check `CRON_SETUP.md` for automation details

## Project Status

- ✅ 280 articles collected (2024-2025)
- ✅ 16 papers in curated reading list
- ⏳ Historical data (1970-2023) scheduled for collection
- ✅ Monthly auto-updates configured
