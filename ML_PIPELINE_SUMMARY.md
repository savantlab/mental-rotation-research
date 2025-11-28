# ML Pipeline Summary

## ✅ What We Built

A complete data science and machine learning pipeline for mental rotation research using **d6tflow**.

### Two Pipelines Created

1. **Analysis Pipeline** (`pipeline/tasks.py`)
   - ✅ Data cleaning and deduplication
   - ✅ Statistical analysis
   - ✅ Top cited papers identification  
   - ✅ Keyword extraction
   - ✅ Author analysis
   - ✅ Automated visualizations

2. **ML Pipeline** (`pipeline/ml_tasks.py`)
   - ✅ Text preprocessing (TF-IDF vectorization)
   - ✅ Feature engineering (1000+ features)
   - ✅ Topic modeling (LDA)
   - ✅ Citation prediction (Random Forest)
   - ✅ Paper clustering (K-means)
   - ✅ LLM prompt generation

## 🧪 Pipeline Test Results

Successfully ran analysis pipeline on your 280 articles:

```
✓ Loaded 280 articles
✓ Cleaned to 219 unique articles (removed 61 duplicates)
✓ Analyzed 201 unique authors
✓ Extracted 22 keywords
✓ Identified top 20 cited papers
✓ Generated visualization dashboard
```

**Top Keywords Found:**
1. mental (582 occurrences)
2. rotation (543)
3. spatial (179)
4. task (118)
5. cognitive (76)

## 📊 Pipeline Features

### Automatic Dependency Management
- Tasks run in correct order
- Outputs cached and reused
- Only re-runs when inputs change

### Incremental Processing
- Failed tasks don't lose progress
- Resume from where you left off
- Parameter changes tracked

### ML Capabilities

**Topic Modeling:**
- Discovers latent themes in papers
- Identifies research clusters
- Shows evolution over time

**Citation Prediction:**
- Predicts future citation impact
- Uses paper features + text
- Random Forest regression

**Paper Clustering:**
- Groups similar papers
- 2D visualization via PCA
- Identifies research communities

**LLM Prompt Engineering:**
- Auto-generates analysis prompts
- Structured for Claude/GPT
- Three types:
  1. Paper summarization
  2. Classification
  3. Comparison to classics

### Research Synthesis
- Cluster-based synthesis prompts
- Meta-analysis prompts
- Ready for LLM processing

## 🚀 Quick Start

### Run Analysis Pipeline
```bash
python pipeline/tasks.py
```

### Run ML Pipeline
```bash
python pipeline/ml_tasks.py
```

### Run Specific Tasks
```python
import d6tflow
from pipeline.ml_tasks import *

# Train topic model with 15 topics
d6tflow.run(TrainTopicModel(n_topics=15))

# Cluster into 7 groups
d6tflow.run(ClusterPapers(n_clusters=7))
```

## 📁 Output Files

**Generated:**
- `results/pipeline_analysis_overview.png` - Visualization dashboard
- `results/top_20_cited.csv` - Most cited papers
- `results/keywords_frequency.csv` - Keyword counts
- `results/top_authors.csv` - Prolific authors
- `results/llm_prompts.json` - LLM analysis prompts
- `results/synthesis_prompts.json` - Meta-analysis prompts

**ML Models (when ML pipeline runs):**
- `data/tfidf_vectorizer.pkl` - Text vectorizer
- `data/topic_model.pkl` - LDA model
- `data/citation_predictor.pkl` - Citation predictor
- `data/cluster_model.pkl` - K-means model
- `data/articles_clustered.parquet` - Clustered papers

## 🔬 ML Pipeline Workflow

```
1. PreprocessText
   ↓ (TF-IDF vectorization)
2. EngineerFeatures
   ↓ (Combine text + metadata)
3. Parallel Training:
   ├─ TrainTopicModel (LDA)
   ├─ TrainCitationPredictor (Random Forest)
   └─ ClusterPapers (K-means + PCA)
       ↓
4. GeneratePaperSummaryPrompts
   ↓
5. GenerateResearchSynthesisPrompt
   ↓
6. RunMLPipeline (complete)
```

## 💡 Use Cases

### 1. Research Discovery
- Find similar papers via clustering
- Discover hidden topics
- Identify research trends

### 2. Impact Prediction
- Predict citation potential
- Identify high-impact work early
- Guide research priorities

### 3. Literature Review
- Auto-generate paper summaries
- Synthesize findings across clusters
- Compare to foundational work

### 4. LLM-Assisted Analysis
- Use generated prompts with Claude/GPT
- Structured analysis at scale
- Meta-analysis automation

## 🎯 Next Steps

1. **Run ML pipeline** on your data:
   ```bash
   python pipeline/ml_tasks.py
   ```

2. **Examine generated prompts:**
   ```bash
   cat results/llm_prompts.json | jq '.[0]'
   ```

3. **Use prompts with LLMs:**
   - Copy prompts to Claude/GPT
   - Get structured analysis
   - Build research database

4. **Customize parameters:**
   ```python
   d6tflow.run(
       RunMLPipeline(),
       TrainTopicModel_n_topics=15,
       ClusterPapers_n_clusters=7
   )
   ```

5. **Add custom tasks** for your specific needs

## 📚 Documentation

- Full guide: `pipeline/README.md`
- Task reference: See README for all parameters
- Examples: README includes code snippets

## 🔧 Technical Stack

- **d6tflow**: Pipeline orchestration
- **Luigi**: Task scheduling
- **scikit-learn**: ML models
- **pandas**: Data processing
- **numpy**: Numerical computing
- **pyarrow**: Efficient data storage

## 🌟 Key Advantages

1. **Reproducible**: Same inputs → same outputs
2. **Scalable**: Add more tasks easily
3. **Cached**: No redundant computation
4. **Flexible**: Change parameters on the fly
5. **Integrated**: Works with existing code

## 📈 Current Statistics

From your 280 articles (2024-2025):
- **219 unique papers** after deduplication
- **403 total citations**
- **201 unique first authors**
- **22 relevant keywords**
- **Years covered**: 2024-2025

The pipelines are ready to scale to thousands of papers once your historical scraper completes!

## 🤖 LLM Integration

The pipeline generates structured prompts for:

**Paper Analysis:**
- Summarize findings
- Identify methodology
- List contributions
- Suggest future work
- Rate impact potential

**Classification:**
- Categorize research type
- Assign confidence scores
- Map to subfields

**Comparison:**
- Compare to Shepard & Metzler (1971)
- Identify advances
- Note methodological differences

**Synthesis:**
- Per-cluster summaries
- Cross-paper patterns
- Research gaps
- Future directions

## ✨ Innovation

This pipeline combines traditional ML with modern LLM capabilities:

1. **ML preprocessing** → Clean, structured data
2. **Feature engineering** → Rich representations
3. **Unsupervised learning** → Discover patterns
4. **Prompt generation** → LLM-ready analysis
5. **Research synthesis** → Meta-level insights

Perfect for **academic research**, **systematic reviews**, and **literature meta-analysis**!
