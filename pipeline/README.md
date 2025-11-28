# Data Science Pipelines

This directory contains d6tflow-based data science pipelines for mental rotation research.

## Overview

Two complementary pipelines:

1. **`tasks.py`**: Data analysis pipeline
   - Data cleaning and preprocessing
   - Statistical analysis
   - Visualization generation

2. **`ml_tasks.py`**: Machine learning pipeline
   - Text preprocessing (TF-IDF)
   - Feature engineering
   - Topic modeling (LDA)
   - Citation prediction
   - Paper clustering
   - LLM prompt generation

## Installation

Install pipeline dependencies:

```bash
pip install d6tflow scikit-learn pyarrow
```

Or use requirements.txt:

```bash
pip install -r requirements.txt
```

## Quick Start

### Run Full Analysis Pipeline

```bash
python pipeline/tasks.py
```

This executes:
- ✅ Load and clean article data
- ✅ Compute statistics
- ✅ Identify top cited papers
- ✅ Extract keywords
- ✅ Analyze authors
- ✅ Generate visualizations

### Run ML Pipeline

```bash
python pipeline/ml_tasks.py
```

This executes:
- ✅ Preprocess text (TF-IDF vectorization)
- ✅ Engineer features
- ✅ Train topic model (LDA)
- ✅ Train citation predictor
- ✅ Cluster papers
- ✅ Generate LLM prompts

## Pipeline Architecture

### d6tflow Benefits

- **Dependency Management**: Automatic task dependency resolution
- **Incremental Builds**: Only runs tasks when inputs change
- **Caching**: Results are cached and reused
- **Parameter Tracking**: Task parameters are versioned

### Task Dependencies

```
Analysis Pipeline (tasks.py):
============================
ScrapeArticles
    └─> CleanArticles
            ├─> ComputeBasicStats
            ├─> IdentifyTopCited
            ├─> ExtractKeywords
            ├─> AnalyzeAuthors
            └─> GenerateVisualizations
                    └─> RunFullPipeline

ML Pipeline (ml_tasks.py):
==========================
CleanArticles (from tasks.py)
    └─> PreprocessText
            └─> EngineerFeatures
                    ├─> TrainTopicModel ───┐
                    ├─> TrainCitationPredictor
                    └─> ClusterPapers ──────┴─> GeneratePaperSummaryPrompts
                            └─> GenerateResearchSynthesisPrompt
                                    └─> RunMLPipeline
```

## Running Individual Tasks

### Analysis Tasks

```python
import d6tflow
from pipeline.tasks import *

# Run specific task
d6tflow.run(ComputeBasicStats())

# Run with parameters
d6tflow.run(IdentifyTopCited(n_papers=50))

# Check if task is complete
task = ExtractKeywords()
print(task.complete())  # True if already run

# Force re-run (invalidate cache)
d6tflow.invalidate_downstream(CleanArticles())
d6tflow.run(ComputeBasicStats())
```

### ML Tasks

```python
import d6tflow
from pipeline.ml_tasks import *

# Train topic model with 15 topics
d6tflow.run(TrainTopicModel(n_topics=15))

# Cluster papers into 7 groups
d6tflow.run(ClusterPapers(n_clusters=7))

# Generate prompts for 20 papers
d6tflow.run(GeneratePaperSummaryPrompts(n_papers=20))
```

## Output Files

### Data Files (`data/`)

**Analysis Pipeline:**
- `articles_cleaned.parquet` - Cleaned article data
- `scraping_progress.json` - Scraper progress tracking

**ML Pipeline:**
- `tfidf_vectorizer.pkl` - Trained TF-IDF vectorizer
- `tfidf_matrix.npy` - TF-IDF feature matrix
- `features_engineered.npy` - Combined feature matrix
- `topic_model.pkl` - LDA topic model
- `citation_predictor.pkl` - Random Forest model
- `cluster_model.pkl` - K-means clustering model
- `pca_model.pkl` - PCA for visualization
- `articles_clustered.parquet` - Articles with cluster labels

### Results (`results/`)

**Analysis Pipeline:**
- `top_N_cited.csv` - Top cited papers
- `keywords_frequency.csv` - Keyword counts
- `top_authors.csv` - Most prolific authors
- `pipeline_analysis_overview.png` - Visualization dashboard

**ML Pipeline:**
- `llm_prompts.json` - Generated prompts for paper analysis
- `synthesis_prompts.json` - Meta-analysis prompts

## Task Reference

### Analysis Pipeline Tasks

#### `ScrapeArticles`
Checks for existing scraped data.

**Parameters:**
- `year_start` (int): Start year (default: 1970)
- `year_end` (int): End year (default: 2025)

#### `CleanArticles`
Cleans and normalizes data.

**Outputs:**
- Removes duplicates
- Converts citations to int
- Parses years
- Sorts by citations

#### `ComputeBasicStats`
Calculates statistics.

**Outputs:**
- Total articles, citations
- Mean/median citations
- Year range
- Articles per year

#### `IdentifyTopCited`
Finds most cited papers.

**Parameters:**
- `n_papers` (int): Number of top papers (default: 20)

#### `ExtractKeywords`
Extracts keyword frequencies.

**Parameters:**
- `min_count` (int): Minimum frequency (default: 5)

#### `AnalyzeAuthors`
Analyzes author patterns.

**Parameters:**
- `top_n` (int): Top N authors (default: 15)

#### `GenerateVisualizations`
Creates 2x2 visualization grid.

### ML Pipeline Tasks

#### `PreprocessText`
TF-IDF vectorization.

**Parameters:**
- `max_features` (int): Max vocabulary size (default: 1000)

**Outputs:**
- TF-IDF matrix
- Cleaned text

#### `EngineerFeatures`
Creates ML feature matrix.

**Features:**
- Citation-based (log citations, has citations)
- Temporal (years since publication, is recent)
- Text (title/abstract length)
- Author count

#### `TrainTopicModel`
Trains LDA topic model.

**Parameters:**
- `n_topics` (int): Number of topics (default: 10)

**Outputs:**
- Topic distributions
- Top words per topic
- Perplexity score

#### `TrainCitationPredictor`
Predicts citation counts.

**Model:** Random Forest Regressor

**Metrics:**
- Train/Test R²
- RMSE

#### `ClusterPapers`
Clusters papers by similarity.

**Parameters:**
- `n_clusters` (int): Number of clusters (default: 5)

**Outputs:**
- Cluster assignments
- PCA coordinates
- Cluster statistics

#### `GeneratePaperSummaryPrompts`
Creates LLM prompts for paper analysis.

**Parameters:**
- `n_papers` (int): Papers to analyze (default: 10)

**Prompt Types:**
- Summarization
- Classification
- Comparison to Shepard & Metzler (1971)

#### `GenerateResearchSynthesisPrompt`
Creates meta-analysis prompts.

**Outputs:**
- Per-cluster synthesis prompts
- Full corpus meta-analysis prompt

## Advanced Usage

### Custom Parameters

```python
# Run with custom configuration
d6tflow.run(
    RunMLPipeline(),
    PreprocessText_max_features=2000,
    TrainTopicModel_n_topics=15,
    ClusterPapers_n_clusters=7
)
```

### Viewing Task Output

```python
# Load task output
task = ComputeBasicStats()
stats = task.output().load()
print(stats)

# Check task status
print(d6tflow.show([RunMLPipeline()]))
```

### Pipeline Visualization

```python
# Show task graph
import d6tflow.viz
d6tflow.viz.to_dot(RunMLPipeline())
```

### Reset Pipeline

```python
# Clear all cached results
d6tflow.invalidate_all()

# Clear specific task
d6tflow.invalidate_downstream(CleanArticles())
```

## Integration with Existing Scripts

The pipelines use your existing data:

- Reads from `data/mental_rotation_complete_*.json`
- Reads `reading_list.json`
- Outputs to `data/` and `results/`

No changes needed to existing workflow!

## Example: Complete ML Workflow

```python
import d6tflow
from pipeline.ml_tasks import *

# Run full ML pipeline
d6tflow.run(RunMLPipeline())

# Load results
topics = TrainTopicModel().output().load()
print(f"Discovered {topics['n_topics']} topics")

# Show topics
for topic_name, words in list(topics['topics'].items())[:3]:
    print(f"{topic_name}: {', '.join(words)}")

# Load clustered data
import pandas as pd
df = pd.read_parquet('data/articles_clustered.parquet')
print(f"Papers clustered into {df['cluster'].nunique()} groups")

# View cluster 0
cluster_0 = df[df['cluster'] == 0]
print(cluster_0[['title', 'citations', 'pub_year']].head())
```

## Troubleshooting

### "No scraped data found"

Run scraper first:
```bash
mental-rotation-scrape
# or
python scripts/scrape_async.py
```

### "Task failed"

Check logs and re-run with invalidation:
```python
d6tflow.invalidate_downstream(FailedTask())
d6tflow.run(FailedTask())
```

### "Out of memory"

Reduce parameters:
```python
d6tflow.run(
    RunMLPipeline(),
    PreprocessText_max_features=500,  # Reduce from 1000
    TrainTopicModel_n_topics=5        # Reduce from 10
)
```

## Next Steps

1. **Run the pipelines** on your 280 collected papers
2. **Examine LLM prompts** in `results/llm_prompts.json`
3. **Use prompts with Claude/GPT** for paper analysis
4. **Iterate on models** with different parameters
5. **Add custom tasks** for your specific research needs

## Resources

- d6tflow docs: https://d6tflow.readthedocs.io/
- Luigi docs: https://luigi.readthedocs.io/
- scikit-learn: https://scikit-learn.org/
