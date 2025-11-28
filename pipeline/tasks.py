#!/usr/bin/env python3
"""
d6tflow pipeline for mental rotation research.

This pipeline manages the workflow from data collection to analysis and visualization.
"""

import d6tflow
import luigi
import pandas as pd
import json
import glob
import os
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Configuration
class Config:
    """Pipeline configuration."""
    DATA_DIR = Path("data")
    RESULTS_DIR = Path("results")
    NOTEBOOKS_DIR = Path("notebooks")
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    NOTEBOOKS_DIR.mkdir(exist_ok=True)


# ============================================================================
# Data Collection Tasks
# ============================================================================

class ScrapeArticles(d6tflow.tasks.TaskPickle):
    """
    Scrape mental rotation articles from Google Scholar.
    
    This task is manual - it checks if data exists rather than running scraper
    (to avoid rate limiting issues).
    """
    year_start = luigi.IntParameter(default=1970)
    year_end = luigi.IntParameter(default=2025)
    
    def run(self):
        """Check for existing scraped data."""
        # Find most recent complete dataset
        complete_files = glob.glob(str(Config.DATA_DIR / 'mental_rotation_complete_*.json'))
        
        if not complete_files:
            raise FileNotFoundError(
                "No scraped data found. Please run: mental-rotation-scrape\n"
                f"Or run: python scripts/scrape_async.py"
            )
        
        latest_file = max(complete_files, key=os.path.getmtime)
        
        with open(latest_file, 'r') as f:
            articles = json.load(f)
        
        # Save metadata about the scrape
        metadata = {
            'file': latest_file,
            'articles_count': len(articles),
            'timestamp': datetime.now().isoformat(),
            'year_range': (self.year_start, self.year_end)
        }
        
        self.save(metadata)
        print(f"✓ Loaded {len(articles)} articles from {os.path.basename(latest_file)}")


@d6tflow.requires(ScrapeArticles)
class LoadReadingList(d6tflow.tasks.TaskPickle):
    """Load curated reading list."""
    
    def run(self):
        """Load reading list JSON."""
        reading_list_file = Path('reading_list.json')
        
        if not reading_list_file.exists():
            raise FileNotFoundError("reading_list.json not found")
        
        with open(reading_list_file, 'r') as f:
            data = json.load(f)
        
        metadata = {
            'papers_count': len(data['reading_list']),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(metadata)
        print(f"✓ Loaded {len(data['reading_list'])} papers from reading list")


# ============================================================================
# Data Processing Tasks
# ============================================================================

@d6tflow.requires(ScrapeArticles)
class CleanArticles(d6tflow.tasks.TaskPickle):
    """
    Clean and normalize article data.
    
    - Convert citations to integers
    - Parse years
    - Remove duplicates
    - Handle missing values
    """
    
    def run(self):
        """Clean article data."""
        # Load scraped data
        scrape_meta = self.input().load()
        
        with open(scrape_meta['file'], 'r') as f:
            articles = json.load(f)
        
        df = pd.DataFrame(articles)
        
        # Clean citations
        df['citations'] = pd.to_numeric(df['citations'], errors='coerce').fillna(0).astype(int)
        
        # Clean years
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['pub_year'] = df['year']
        
        # Remove duplicates by URL
        df_clean = df.drop_duplicates(subset=['url'], keep='first')
        duplicates_removed = len(df) - len(df_clean)
        
        # Sort by citations descending
        df_clean = df_clean.sort_values('citations', ascending=False).reset_index(drop=True)
        
        # Save metadata
        metadata = {
            'total_articles': len(df_clean),
            'duplicates_removed': duplicates_removed,
            'year_range': (int(df_clean['pub_year'].min()), int(df_clean['pub_year'].max())),
            'total_citations': int(df_clean['citations'].sum()),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(metadata)
        
        # Also save cleaned dataframe
        output_file = Config.DATA_DIR / 'articles_cleaned.parquet'
        df_clean.to_parquet(output_file, index=False)
        
        print(f"✓ Cleaned {len(df_clean)} articles")
        print(f"  Removed {duplicates_removed} duplicates")
        print(f"  Year range: {metadata['year_range']}")


# ============================================================================
# Analysis Tasks
# ============================================================================

@d6tflow.requires(CleanArticles)
class ComputeBasicStats(d6tflow.tasks.TaskPickle):
    """Compute basic statistics on articles."""
    
    def run(self):
        """Calculate statistics."""
        # Load cleaned data
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        stats = {
            'total_articles': len(df),
            'total_citations': int(df['citations'].sum()),
            'mean_citations': float(df['citations'].mean()),
            'median_citations': float(df['citations'].median()),
            'max_citations': int(df['citations'].max()),
            'year_range': (int(df['pub_year'].min()), int(df['pub_year'].max())),
            'years_covered': int(df['search_year'].nunique()),
            'articles_per_year': df.groupby('search_year').size().to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(stats)
        
        print(f"\n{'='*70}")
        print("BASIC STATISTICS")
        print(f"{'='*70}")
        print(f"Total articles: {stats['total_articles']}")
        print(f"Total citations: {stats['total_citations']:,}")
        print(f"Mean citations: {stats['mean_citations']:.1f}")
        print(f"Median citations: {stats['median_citations']:.0f}")
        print(f"Year range: {stats['year_range']}")


@d6tflow.requires(CleanArticles)
class IdentifyTopCited(d6tflow.tasks.TaskPickle):
    """Identify top cited papers."""
    
    n_papers = luigi.IntParameter(default=20)
    
    def run(self):
        """Find top cited papers."""
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        top = df.nlargest(self.n_papers, 'citations')[
            ['title', 'authors', 'pub_year', 'citations', 'url']
        ]
        
        # Convert to dict for saving
        top_papers = top.to_dict('records')
        
        result = {
            'n_papers': self.n_papers,
            'papers': top_papers,
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(result)
        
        # Also save CSV
        output_file = Config.RESULTS_DIR / f'top_{self.n_papers}_cited.csv'
        top.to_csv(output_file, index=False)
        
        print(f"\n✓ Identified top {self.n_papers} cited papers")
        print(f"  Saved to: {output_file}")


@d6tflow.requires(CleanArticles)
class ExtractKeywords(d6tflow.tasks.TaskPickle):
    """Extract and count keywords from titles and abstracts."""
    
    min_count = luigi.IntParameter(default=5)
    
    def run(self):
        """Extract keywords."""
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        # Combine titles and abstracts
        all_text = ' '.join(df['title'].fillna('') + ' ' + df['abstract'].fillna(''))
        all_text = all_text.lower()
        
        # Predefined keywords of interest
        keywords = [
            'spatial', 'cognitive', 'rotation', 'mental', 'imagery',
            'visuospatial', 'task', 'performance', 'gender', 'sex',
            'brain', 'fmri', 'neural', 'training', 'ability',
            'object', '3d', 'three-dimensional', 'parietal',
            'working memory', 'age', 'children', 'development',
            'aphantasia', 'attention', 'capacity', 'perception'
        ]
        
        keyword_counts = {}
        for kw in keywords:
            count = all_text.count(kw)
            if count >= self.min_count:
                keyword_counts[kw] = count
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            'keywords': dict(sorted_keywords),
            'total_keywords': len(sorted_keywords),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(result)
        
        # Save CSV
        output_file = Config.RESULTS_DIR / 'keywords_frequency.csv'
        pd.DataFrame(sorted_keywords, columns=['keyword', 'count']).to_csv(output_file, index=False)
        
        print(f"\n✓ Extracted {len(sorted_keywords)} keywords")
        print(f"  Top 5: {sorted_keywords[:5]}")


@d6tflow.requires(CleanArticles)
class AnalyzeAuthors(d6tflow.tasks.TaskPickle):
    """Analyze author patterns."""
    
    top_n = luigi.IntParameter(default=15)
    
    def run(self):
        """Analyze authors."""
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        # Extract first authors
        import re
        first_authors = []
        for authors in df['authors']:
            if authors and authors != 'N/A':
                first = re.split(r',|and', str(authors))[0].strip()
                if first:
                    first_authors.append(first)
        
        # Count occurrences
        from collections import Counter
        author_counts = Counter(first_authors)
        
        top_authors = author_counts.most_common(self.top_n)
        
        result = {
            'top_authors': top_authors,
            'total_unique_authors': len(author_counts),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(result)
        
        # Save CSV
        output_file = Config.RESULTS_DIR / 'top_authors.csv'
        pd.DataFrame(top_authors, columns=['author', 'papers']).to_csv(output_file, index=False)
        
        print(f"\n✓ Analyzed {len(author_counts)} unique first authors")
        print(f"  Top author: {top_authors[0][0]} ({top_authors[0][1]} papers)")


# ============================================================================
# Visualization Tasks
# ============================================================================

@d6tflow.requires(ComputeBasicStats, IdentifyTopCited, ExtractKeywords)
class GenerateVisualizations(d6tflow.tasks.TaskPickle):
    """Generate all visualizations."""
    
    def run(self):
        """Create visualizations."""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        sns.set_style('whitegrid')
        
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        # Create 2x2 subplot
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Articles by search year
        year_counts = df['search_year'].value_counts().sort_index()
        axes[0, 0].bar(year_counts.index, year_counts.values, color='steelblue')
        axes[0, 0].set_xlabel('Search Year')
        axes[0, 0].set_ylabel('Number of Articles')
        axes[0, 0].set_title('Articles Collected by Search Year')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Citation distribution
        axes[0, 1].hist(df['citations'].dropna(), bins=30, color='coral', edgecolor='black')
        axes[0, 1].set_xlabel('Citation Count')
        axes[0, 1].set_ylabel('Number of Articles')
        axes[0, 1].set_title('Distribution of Citations')
        axes[0, 1].set_yscale('log')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Top 15 most cited
        top15 = df.nlargest(15, 'citations')[['title', 'citations']].copy()
        top15['short_title'] = top15['title'].str[:40] + '...'
        axes[1, 0].barh(range(len(top15)), top15['citations'], color='green')
        axes[1, 0].set_yticks(range(len(top15)))
        axes[1, 0].set_yticklabels(top15['short_title'], fontsize=8)
        axes[1, 0].set_xlabel('Citations')
        axes[1, 0].set_title('Top 15 Most Cited Articles')
        axes[1, 0].invert_yaxis()
        axes[1, 0].grid(True, alpha=0.3, axis='x')
        
        # 4. Keywords frequency (top 20)
        keywords_data = self.input()[2].load()
        keywords = list(keywords_data['keywords'].items())[:20]
        if keywords:
            kw_df = pd.DataFrame(keywords, columns=['keyword', 'count'])
            axes[1, 1].barh(range(len(kw_df)), kw_df['count'], color='purple')
            axes[1, 1].set_yticks(range(len(kw_df)))
            axes[1, 1].set_yticklabels(kw_df['keyword'], fontsize=8)
            axes[1, 1].set_xlabel('Frequency')
            axes[1, 1].set_title('Top 20 Keywords in Titles/Abstracts')
            axes[1, 1].invert_yaxis()
            axes[1, 1].grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        output_file = Config.RESULTS_DIR / 'pipeline_analysis_overview.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        result = {
            'visualization_file': str(output_file),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(result)
        
        print(f"\n✓ Generated visualizations")
        print(f"  Saved to: {output_file}")


# ============================================================================
# Master Task
# ============================================================================

@d6tflow.requires(ComputeBasicStats, IdentifyTopCited, ExtractKeywords, AnalyzeAuthors, GenerateVisualizations)
class RunFullPipeline(d6tflow.tasks.TaskPickle):
    """
    Master task that runs the complete pipeline.
    
    Usage:
        python pipeline/tasks.py
        
    Or programmatically:
        import d6tflow
        from pipeline.tasks import RunFullPipeline
        d6tflow.run(RunFullPipeline())
    """
    
    def run(self):
        """Generate final report."""
        stats = self.input()[0].load()
        top_cited = self.input()[1].load()
        keywords = self.input()[2].load()
        authors = self.input()[3].load()
        viz = self.input()[4].load()
        
        report = {
            'pipeline_complete': True,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_articles': stats['total_articles'],
                'total_citations': stats['total_citations'],
                'year_range': stats['year_range'],
                'top_cited_papers': len(top_cited['papers']),
                'keywords_extracted': keywords['total_keywords'],
                'unique_authors': authors['total_unique_authors'],
                'visualization': viz['visualization_file']
            }
        }
        
        self.save(report)
        
        print(f"\n{'='*70}")
        print("PIPELINE COMPLETE")
        print(f"{'='*70}")
        print(f"✓ Processed {stats['total_articles']} articles")
        print(f"✓ Generated {keywords['total_keywords']} keyword frequencies")
        print(f"✓ Identified {len(top_cited['papers'])} top cited papers")
        print(f"✓ Analyzed {authors['total_unique_authors']} unique authors")
        print(f"✓ Created visualization: {viz['visualization_file']}")
        print(f"\nResults saved to: {Config.RESULTS_DIR}/")
        print(f"{'='*70}")


if __name__ == '__main__':
    # Run the full pipeline
    d6tflow.run(RunFullPipeline())
