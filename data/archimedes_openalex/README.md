# Archimedes OpenAlex Citation Network Data

This directory contains citation network data extracted from the OpenAlex API via the Archimedes research integrity system.

## Datasets

### 1. `shepard_metzler_1971_citations_clean.json`
- **Papers**: 6,097
- **Source**: Papers citing Shepard, R. N., & Metzler, J. (1971). Mental rotation of three-dimensional objects. *Science, 171*(3972), 701-703.
- **Date Range**: 1972+ (papers published after the foundational work)

### 2. `vandenberg_kuse_1978_citations_clean.json`
- **Papers**: 2,534
- **Source**: Papers citing Vandenberg, S. G., & Kuse, A. R. (1978). Mental rotations, a group test of three-dimensional spatial visualization. *Perceptual and Motor Skills, 47*(2), 599-604.
- **Date Range**: 1979+ (papers published after the foundational work)

### 3. `overlap_citations_clean.json`
- **Papers**: 797
- **Source**: Papers citing BOTH Shepard & Metzler (1971) AND Vandenberg & Kuse (1978)
- **Significance**: High-impact papers that reference both foundational works in mental rotation research

## Total Dataset
- **Unique Papers**: 6,581 (after deduplication by DOI/title)
- **Filters Applied**:
  - Published 1972 or later
  - Excluded medical/clinical papers (pulmonary, radiology, CT scans, etc.)
  - Cognitive science and psychology focus

## Data Structure

Each paper contains:
```json
{
  "id": "OpenAlex ID",
  "doi": "DOI",
  "title": "Paper title",
  "year": 2024,
  "cited_by_count": 42,
  "authors": ["Author 1", "Author 2"],
  "journal": "Journal name",
  "concepts": ["concept1", "concept2"],
  "source_dataset": "shepard_metzler_citations|vandenberg_kuse_citations|overlap_citations"
}
```

## Use Cases

1. **Citation Network Analysis**: Map influence of foundational papers across 50+ years
2. **Topic Modeling**: Identify research clusters and trends in mental rotation literature
3. **Contamination Detection**: Track propagation of methodological issues through citation networks
4. **Author Network Analysis**: Identify key researchers and collaboration patterns
5. **Impact Assessment**: Measure influence of foundational works over time

## Archimedes System

This data was collected as part of the **Archimedes** research integrity system, which:
- Identifies contamination in citation networks
- Tracks invalidation cascades from flawed foundational papers
- Provides funding impact calculations
- Generates visualizations of research landscape evolution

## Integration

This data is integrated with:
- Mental Rotation Research pipeline (this repo)
- Savantlab Portfolio Flask app (visualizations and API)
- Archimedes contamination detection system

## Data Source

**OpenAlex API**: https://openalex.org/
- Open access scholarly metadata
- Citation counts and relationships
- Author and institution information
- Concept tagging for topic analysis

## Updates

Last updated: 2025-12-30
Next planned update: Historical scrape back to 1972 in progress
