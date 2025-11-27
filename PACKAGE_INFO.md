# Mental Rotation Research - Package Information

## Overview

This project has been converted from a collection of scripts into a proper Python package that can be installed via pip and provides command-line tools for researchers.

## Package Structure

```
mental-rotation-research/
├── mental_rotation/              # Main package
│   ├── __init__.py              # Package initialization (version 0.1.0)
│   └── cli.py                   # Command-line interface entry points
├── scripts/                      # Core functionality (to be refactored into package)
│   ├── scrape_async.py          # Async web scraper
│   ├── analyze_data.py          # Data analysis tools
│   ├── manage_reading_list.py   # Reading list manager
│   └── scrape_reading_list.py   # Paper downloader
├── examples/                     # Usage examples
│   └── example_usage.py         # Demonstrates library usage
├── notebooks/                    # Jupyter notebooks
│   └── analysis_2024_2025.ipynb # Example analysis
├── setup.py                      # Package configuration
├── MANIFEST.in                   # Package data files specification
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── QUICKSTART.md                 # Quick start guide
├── CHANGELOG.md                  # Version history
└── LICENSE                       # MIT License
```

## Installation Methods

### 1. Editable Install (Development)
```bash
git clone git@github.com:savantlab/mental-rotation-research.git
cd mental-rotation-research
pip install -e .
```

### 2. Direct from GitHub
```bash
pip install git+https://github.com/savantlab/mental-rotation-research.git
```

### 3. From Source
```bash
python setup.py install
```

## CLI Commands

After installation, three commands are available globally:

### mental-rotation-scrape
Scrapes mental rotation articles from Google Scholar.

**Options:**
- `--year-start YEAR`: Start year (default: 1970)
- `--year-end YEAR`: End year (default: current year)
- `--max-pages N`: Maximum pages per year (default: 100)
- `--calculate-ranges`: Calculate optimal year ranges without scraping

**Examples:**
```bash
mental-rotation-scrape                              # Full scrape
mental-rotation-scrape --year-start 2020 --year-end 2023
mental-rotation-scrape --calculate-ranges
```

### mental-rotation-analyze
Analyzes collected articles with statistics and visualizations.

**Options:**
- `--data-file PATH`: Path to JSON data file
- `--top-n N`: Number of top cited papers to show (default: 20)

**Examples:**
```bash
mental-rotation-analyze
mental-rotation-analyze --top-n 50
mental-rotation-analyze --data-file data/custom.json
```

### mental-rotation-reading
Manages curated reading list of articles.

**Subcommands:**
- `list [--tag TAG]`: List articles, optionally filtered by tag
- `add TITLE AUTHORS URL [OPTIONS]`: Add article
- `remove INDEX`: Remove article by index
- `download [--url URL] [--index N]`: Download papers
- `export`: Export URLs to text file

**Examples:**
```bash
mental-rotation-reading list
mental-rotation-reading list --tag aphantasia
mental-rotation-reading add "Paper Title" "Author Names" "https://url" --year 2024
mental-rotation-reading remove 5
mental-rotation-reading download --url "https://example.com/paper.pdf"
mental-rotation-reading export
```

## Library Usage

The package can also be used programmatically:

```python
from scripts.manage_reading_list import load_reading_list
from scripts.analyze_data import load_latest_data
import pandas as pd

# Load reading list
data = load_reading_list()
articles = data['reading_list']

# Filter papers
aphantasia_papers = [a for a in articles if 'aphantasia' in a.get('tags', [])]

# Load and analyze dataset
df = load_latest_data()
top_cited = df.nlargest(10, 'citations')
```

See `examples/example_usage.py` for complete examples.

## Dependencies

Core dependencies (auto-installed):
- **aiohttp**: Async HTTP requests
- **beautifulsoup4**: HTML parsing
- **pandas**: Data analysis
- **numpy**: Numerical operations
- **matplotlib**: Visualization
- **seaborn**: Statistical visualizations
- **jupyter**: Interactive notebooks

## Features

### Scraping
- Async parallel requests (3 concurrent)
- Rate limiting (30-50s random delays)
- Automatic progress saving
- Resume capability
- Duplicate detection
- Rate limit detection with 24-hour breaks

### Analysis
- Citation statistics
- Author analysis
- Publication venue tracking
- Keyword extraction
- Automated visualizations
- Export to CSV

### Reading List
- Curated paper collection
- Tag-based organization
- Citation tracking
- Paywall detection
- Auto-download capability
- Multiple export formats

## Current Status

- **Package Version**: 0.1.0
- **Python Support**: 3.8+
- **Installation**: Working via pip
- **CLI Commands**: All functional
- **Data Collection**: 280 articles (2024-2025)
- **Reading List**: 16 curated papers
- **Automation**: Monthly cron job configured

## Future Improvements

### Planned for 0.2.0
1. Refactor scripts into proper package modules:
   - `mental_rotation.scraper`
   - `mental_rotation.analyzer`
   - `mental_rotation.reading_list`

2. Add testing:
   - Unit tests with pytest
   - Integration tests
   - CI/CD with GitHub Actions

3. Add type hints throughout codebase

4. Create API documentation with Sphinx

5. Add configuration file support (YAML/JSON)

6. Implement additional export formats:
   - BibTeX
   - Excel
   - RIS

7. Publish to PyPI

### Long-term Goals
- Web interface for browsing papers
- Integration with reference managers (Zotero, Mendeley)
- Advanced search and filtering
- Collaborative reading lists
- Machine learning for paper recommendations

## Publishing to PyPI

When ready to publish:

```bash
# Build distribution
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

Then users can install via:
```bash
pip install mental-rotation-research
```

## Contributing

This is a research project by Savant Lab. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (when implemented)
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Support

- **Repository**: https://github.com/savantlab/mental-rotation-research
- **Issues**: https://github.com/savantlab/mental-rotation-research/issues
- **Documentation**: README.md, QUICKSTART.md

## Acknowledgments

- Data sourced from Google Scholar
- Built with open-source Python libraries
- Inspired by cognitive science research on mental rotation
