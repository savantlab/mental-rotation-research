# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-26

### Added
- Created Python package structure with `setup.py` and `mental_rotation/` package directory
- Implemented CLI tools:
  - `mental-rotation-scrape`: Scrape articles from Google Scholar
  - `mental-rotation-analyze`: Analyze collected data with statistics and visualizations
  - `mental-rotation-reading`: Manage curated reading list
- Added package installation support via pip (`pip install -e .`)
- Created comprehensive README with installation and usage instructions
- Added QUICKSTART.md for new users
- Created MANIFEST.in for package data files
- Added example scripts in `examples/` directory demonstrating library usage
- Included LICENSE file (MIT)

### Changed
- Reorganized project as installable Python package
- Updated README with CLI usage examples and library documentation
- Enhanced package metadata in setup.py

### Existing Features (pre-packaging)
- Async web scraper with rate limiting (3 parallel requests, 30-50s delays)
- Automatic progress saving and resume capability
- Reading list management (16 curated papers)
- Data analysis tools with visualizations
- Jupyter notebooks for interactive analysis
- Monthly automated updates via cron
- 280 articles already collected (2024-2025)
- Rate limit detection and 24-hour cooldown handling

## [Unreleased]

### Planned
- Move scraper, analyzer, and reading list code into proper package modules
- Add unit tests with pytest
- Add type hints throughout codebase
- Create proper API documentation with Sphinx
- Add configuration file support (YAML/JSON)
- Implement data export to multiple formats (CSV, Excel, BibTeX)
- Add search and filtering capabilities to CLI
- Create GitHub Actions for CI/CD
- Publish to PyPI for easier installation

[0.1.0]: https://github.com/savantlab/mental-rotation-research/releases/tag/v0.1.0
