#!/usr/bin/env python3
"""
Machine Learning pipeline for mental rotation research.

Features:
- Text preprocessing and feature engineering
- Topic modeling
- Citation prediction
- Paper classification
- LLM prompt engineering for paper analysis
"""

import d6tflow
import luigi
import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.tasks import CleanArticles, Config


# ============================================================================
# Preprocessing Tasks
# ============================================================================

@d6tflow.requires(CleanArticles)
class PreprocessText(d6tflow.tasks.TaskPickle):
    """
    Preprocess text data for ML.
    
    - Tokenization
    - Stopword removal
    - Lemmatization
    - TF-IDF vectorization
    """
    
    max_features = luigi.IntParameter(default=1000)
    
    def run(self):
        """Preprocess text data."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        import re
        
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        # Combine title and abstract
        df['full_text'] = df['title'].fillna('') + ' ' + df['abstract'].fillna('')
        
        # Basic text cleaning
        def clean_text(text):
            # Lowercase
            text = text.lower()
            # Remove special characters but keep spaces
            text = re.sub(r'[^a-z0-9\s]', ' ', text)
            # Remove extra whitespace
            text = ' '.join(text.split())
            return text
        
        df['text_clean'] = df['full_text'].apply(clean_text)
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words='english',
            ngram_range=(1, 2),  # unigrams and bigrams
            min_df=2,
            max_df=0.8
        )
        
        tfidf_matrix = vectorizer.fit_transform(df['text_clean'])
        feature_names = vectorizer.get_feature_names_out()
        
        # Save preprocessed data
        output = {
            'tfidf_matrix_shape': tfidf_matrix.shape,
            'feature_names': feature_names.tolist(),
            'n_documents': len(df),
            'vocabulary_size': len(feature_names),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(output)
        
        # Save vectorizer and matrix
        import pickle
        with open(Config.DATA_DIR / 'tfidf_vectorizer.pkl', 'wb') as f:
            pickle.dump(vectorizer, f)
        
        np.save(Config.DATA_DIR / 'tfidf_matrix.npy', tfidf_matrix.toarray())
        
        print(f"\n✓ Preprocessed {len(df)} documents")
        print(f"  TF-IDF matrix: {tfidf_matrix.shape}")
        print(f"  Vocabulary: {len(feature_names)} features")


@d6tflow.requires(PreprocessText)
class EngineerFeatures(d6tflow.tasks.TaskPickle):
    """
    Engineer features for ML models.
    
    - Citation-based features
    - Temporal features
    - Text length features
    - Author features
    """
    
    def run(self):
        """Create feature matrix."""
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        # Load TF-IDF matrix
        tfidf_matrix = np.load(Config.DATA_DIR / 'tfidf_matrix.npy')
        
        # Create additional features
        features = pd.DataFrame()
        
        # Citation features
        features['citations'] = df['citations']
        features['log_citations'] = np.log1p(df['citations'])
        features['has_citations'] = (df['citations'] > 0).astype(int)
        
        # Temporal features
        features['pub_year'] = df['pub_year'].fillna(df['pub_year'].median())
        features['years_since_pub'] = 2025 - features['pub_year']
        features['is_recent'] = (features['pub_year'] >= 2020).astype(int)
        
        # Text features
        df['title_length'] = df['title'].fillna('').str.len()
        df['abstract_length'] = df['abstract'].fillna('').str.len()
        features['title_length'] = df['title_length']
        features['abstract_length'] = df['abstract_length']
        features['has_abstract'] = (df['abstract_length'] > 0).astype(int)
        
        # Author features
        df['n_authors'] = df['authors'].fillna('').str.count(',') + 1
        features['n_authors'] = df['n_authors']
        
        # Normalize features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Combine with TF-IDF
        combined_features = np.hstack([tfidf_matrix, features_scaled])
        
        # Save
        np.save(Config.DATA_DIR / 'features_engineered.npy', combined_features)
        np.save(Config.DATA_DIR / 'features_metadata.npy', features_scaled)
        
        import pickle
        with open(Config.DATA_DIR / 'feature_scaler.pkl', 'wb') as f:
            pickle.dump(scaler, f)
        
        output = {
            'n_samples': combined_features.shape[0],
            'n_features': combined_features.shape[1],
            'tfidf_features': tfidf_matrix.shape[1],
            'metadata_features': features.shape[1],
            'feature_names': features.columns.tolist(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(output)
        
        print(f"\n✓ Engineered {combined_features.shape[1]} features")
        print(f"  TF-IDF: {tfidf_matrix.shape[1]}")
        print(f"  Metadata: {features.shape[1]}")


# ============================================================================
# ML Model Tasks
# ============================================================================

@d6tflow.requires(EngineerFeatures)
class TrainTopicModel(d6tflow.tasks.TaskPickle):
    """
    Train topic model using Latent Dirichlet Allocation.
    
    Discovers latent topics in the paper corpus.
    """
    
    n_topics = luigi.IntParameter(default=10)
    
    def run(self):
        """Train LDA topic model."""
        from sklearn.decomposition import LatentDirichletAllocation
        import pickle
        
        # Load TF-IDF matrix
        tfidf_matrix = np.load(Config.DATA_DIR / 'tfidf_matrix.npy')
        
        # Load vectorizer for feature names
        with open(Config.DATA_DIR / 'tfidf_vectorizer.pkl', 'rb') as f:
            vectorizer = pickle.load(f)
        
        # Train LDA
        lda = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=42,
            max_iter=20,
            learning_method='online',
            n_jobs=-1
        )
        
        topic_distributions = lda.fit_transform(tfidf_matrix)
        
        # Get top words per topic
        feature_names = vectorizer.get_feature_names_out()
        n_top_words = 10
        
        topics = {}
        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-n_top_words:][::-1]
            top_words = [feature_names[i] for i in top_indices]
            topics[f'topic_{topic_idx}'] = top_words
        
        # Save model
        with open(Config.DATA_DIR / 'topic_model.pkl', 'wb') as f:
            pickle.dump(lda, f)
        
        np.save(Config.DATA_DIR / 'topic_distributions.npy', topic_distributions)
        
        output = {
            'n_topics': self.n_topics,
            'topics': topics,
            'perplexity': lda.perplexity(tfidf_matrix),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(output)
        
        print(f"\n✓ Trained topic model with {self.n_topics} topics")
        print(f"  Perplexity: {output['perplexity']:.2f}")
        print(f"\n  Sample topics:")
        for i, (topic_name, words) in enumerate(list(topics.items())[:3]):
            print(f"    {topic_name}: {', '.join(words[:5])}")


@d6tflow.requires(EngineerFeatures)
class TrainCitationPredictor(d6tflow.tasks.TaskPickle):
    """
    Train model to predict citation counts.
    
    Uses paper features to predict future citation impact.
    """
    
    def run(self):
        """Train citation prediction model."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, r2_score
        import pickle
        
        # Load features
        X = np.load(Config.DATA_DIR / 'features_engineered.npy')
        
        # Load targets (log-transformed citations)
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        y = np.log1p(df['citations'].values)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        
        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
        
        # Feature importance
        feature_meta = self.input().load()
        importance_indices = np.argsort(model.feature_importances_)[-10:][::-1]
        
        # Save model
        with open(Config.DATA_DIR / 'citation_predictor.pkl', 'wb') as f:
            pickle.dump(model, f)
        
        output = {
            'train_r2': float(train_r2),
            'test_r2': float(test_r2),
            'test_rmse': float(test_rmse),
            'n_features': X.shape[1],
            'n_samples': X.shape[0],
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(output)
        
        print(f"\n✓ Trained citation predictor")
        print(f"  Train R²: {train_r2:.3f}")
        print(f"  Test R²: {test_r2:.3f}")
        print(f"  Test RMSE: {test_rmse:.3f}")


@d6tflow.requires(EngineerFeatures)
class ClusterPapers(d6tflow.tasks.TaskPickle):
    """
    Cluster papers by similarity.
    
    Uses K-means clustering on paper features.
    """
    
    n_clusters = luigi.IntParameter(default=5)
    
    def run(self):
        """Cluster papers."""
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA
        import pickle
        
        # Load features
        X = np.load(Config.DATA_DIR / 'features_engineered.npy')
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        
        # K-means clustering
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)
        
        # PCA for visualization
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X)
        
        # Add clusters to dataframe
        df['cluster'] = clusters
        df['pca_1'] = X_pca[:, 0]
        df['pca_2'] = X_pca[:, 1]
        
        # Analyze clusters
        cluster_stats = []
        for i in range(self.n_clusters):
            cluster_papers = df[df['cluster'] == i]
            stats = {
                'cluster': i,
                'size': len(cluster_papers),
                'mean_citations': float(cluster_papers['citations'].mean()),
                'mean_year': float(cluster_papers['pub_year'].mean()),
                'top_papers': cluster_papers.nlargest(3, 'citations')['title'].tolist()
            }
            cluster_stats.append(stats)
        
        # Save
        df.to_parquet(Config.DATA_DIR / 'articles_clustered.parquet', index=False)
        
        with open(Config.DATA_DIR / 'cluster_model.pkl', 'wb') as f:
            pickle.dump(kmeans, f)
        
        with open(Config.DATA_DIR / 'pca_model.pkl', 'wb') as f:
            pickle.dump(pca, f)
        
        output = {
            'n_clusters': self.n_clusters,
            'cluster_stats': cluster_stats,
            'inertia': float(kmeans.inertia_),
            'explained_variance': pca.explained_variance_ratio_.tolist(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(output)
        
        print(f"\n✓ Clustered papers into {self.n_clusters} groups")
        print(f"  Inertia: {kmeans.inertia_:.2f}")
        for stat in cluster_stats:
            print(f"  Cluster {stat['cluster']}: {stat['size']} papers, "
                  f"avg {stat['mean_citations']:.0f} citations")


# ============================================================================
# LLM Prompt Engineering Tasks
# ============================================================================

@d6tflow.requires(CleanArticles, TrainTopicModel)
class GeneratePaperSummaryPrompts(d6tflow.tasks.TaskPickle):
    """
    Generate prompts for LLM-based paper summarization.
    
    Creates structured prompts for analyzing papers with LLMs.
    """
    
    n_papers = luigi.IntParameter(default=10)
    
    def run(self):
        """Generate prompts for paper analysis."""
        df = pd.read_parquet(Config.DATA_DIR / 'articles_cleaned.parquet')
        topic_data = self.input()[1].load()
        
        # Select diverse papers (top cited, recent, different topics)
        top_cited = df.nlargest(self.n_papers // 2, 'citations')
        recent = df[df['pub_year'] >= 2023].nlargest(self.n_papers // 2, 'citations')
        selected_papers = pd.concat([top_cited, recent]).drop_duplicates()
        
        prompts = []
        
        for idx, paper in selected_papers.iterrows():
            # Base prompt for summarization
            base_prompt = f"""Analyze this mental rotation research paper:

Title: {paper['title']}
Authors: {paper['authors']}
Year: {paper['pub_year']}
Citations: {paper['citations']}

Abstract:
{paper['abstract'] if pd.notna(paper['abstract']) else 'Not available'}

Tasks:
1. Summarize the main findings in 2-3 sentences
2. Identify the research methodology
3. List key contributions
4. Suggest related research directions
5. Rate the paper's potential impact (1-10)

Format your response as JSON with keys: summary, methodology, contributions, future_work, impact_score"""

            # Classification prompt
            classification_prompt = f"""Classify this paper into research categories:

Title: {paper['title']}
Abstract: {paper['abstract'][:500] if pd.notna(paper['abstract']) else 'Not available'}...

Categories to consider:
- Cognitive neuroscience
- Behavioral studies
- Individual differences
- Training and intervention
- Neuroimaging (fMRI, EEG)
- Computational modeling
- Educational applications
- Clinical applications

Return: Top 3 most relevant categories with confidence scores (0-1)."""

            # Comparison prompt
            comparison_prompt = f"""Compare this paper to the foundational Shepard & Metzler (1971) study:

Paper: {paper['title']}
Year: {paper['pub_year']}

How does it:
1. Build upon or challenge the original findings?
2. Use different methodologies?
3. Extend to new domains?
4. Address limitations?"""

            prompts.append({
                'paper_id': int(idx),
                'title': paper['title'],
                'year': int(paper['pub_year']) if pd.notna(paper['pub_year']) else None,
                'citations': int(paper['citations']),
                'prompts': {
                    'summarization': base_prompt,
                    'classification': classification_prompt,
                    'comparison': comparison_prompt
                }
            })
        
        # Save prompts
        output_file = Config.RESULTS_DIR / 'llm_prompts.json'
        with open(output_file, 'w') as f:
            json.dump(prompts, f, indent=2)
        
        output = {
            'n_prompts': len(prompts),
            'prompt_types': ['summarization', 'classification', 'comparison'],
            'output_file': str(output_file),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(output)
        
        print(f"\n✓ Generated {len(prompts)} paper analysis prompts")
        print(f"  Saved to: {output_file}")
        print(f"  Prompt types: {len(output['prompt_types'])}")


@d6tflow.requires(ClusterPapers)
class GenerateResearchSynthesisPrompt(d6tflow.tasks.TaskPickle):
    """
    Generate meta-analysis prompts for research synthesis.
    
    Creates prompts for LLM to synthesize findings across papers.
    """
    
    def run(self):
        """Generate synthesis prompts."""
        df = pd.read_parquet(Config.DATA_DIR / 'articles_clustered.parquet')
        cluster_data = self.input().load()
        
        # Create cluster summaries
        synthesis_prompts = []
        
        for cluster_id in range(cluster_data['n_clusters']):
            cluster_papers = df[df['cluster'] == cluster_id].nlargest(10, 'citations')
            
            papers_text = "\n\n".join([
                f"{i+1}. {row['title']} ({row['pub_year']}, {row['citations']} citations)\n"
                f"   Abstract: {row['abstract'][:200] if pd.notna(row['abstract']) else 'N/A'}..."
                for i, (_, row) in enumerate(cluster_papers.iterrows())
            ])
            
            prompt = f"""Synthesize findings from this cluster of {len(cluster_papers)} mental rotation papers:

{papers_text}

Synthesis Tasks:
1. Identify common themes and methodologies
2. Summarize key findings and consensus views
3. Note contradictions or debates
4. Identify research gaps
5. Suggest future research directions

Provide a structured synthesis covering these areas."""

            synthesis_prompts.append({
                'cluster_id': cluster_id,
                'n_papers': len(cluster_papers),
                'mean_citations': float(cluster_papers['citations'].mean()),
                'prompt': prompt
            })
        
        # Overall synthesis prompt
        top_papers = df.nlargest(20, 'citations')
        
        meta_prompt = f"""Conduct a meta-analysis of mental rotation research based on {len(df)} papers:

Statistics:
- Total papers: {len(df)}
- Year range: {int(df['pub_year'].min())} - {int(df['pub_year'].max())}
- Total citations: {int(df['citations'].sum()):,}
- Clusters identified: {cluster_data['n_clusters']}

Top 5 most cited papers:
{chr(10).join([f"{i+1}. {row['title']} ({row['citations']} citations)" for i, (_, row) in enumerate(top_papers.head(5).iterrows())])}

Questions:
1. How has the field evolved since Shepard & Metzler (1971)?
2. What are the major theoretical debates?
3. What methodological innovations emerged?
4. What are current frontiers and open questions?
5. What practical applications have been developed?

Provide a comprehensive meta-analysis addressing these questions."""

        synthesis_prompts.append({
            'type': 'meta_analysis',
            'scope': 'full_corpus',
            'prompt': meta_prompt
        })
        
        # Save
        output_file = Config.RESULTS_DIR / 'synthesis_prompts.json'
        with open(output_file, 'w') as f:
            json.dump(synthesis_prompts, f, indent=2)
        
        output = {
            'n_cluster_prompts': cluster_data['n_clusters'],
            'has_meta_prompt': True,
            'output_file': str(output_file),
            'timestamp': datetime.now().isoformat()
        }
        
        self.save(output)
        
        print(f"\n✓ Generated research synthesis prompts")
        print(f"  Cluster prompts: {cluster_data['n_clusters']}")
        print(f"  Meta-analysis prompt: 1")
        print(f"  Saved to: {output_file}")


# ============================================================================
# Master ML Pipeline
# ============================================================================

@d6tflow.requires(
    PreprocessText,
    EngineerFeatures,
    TrainTopicModel,
    TrainCitationPredictor,
    ClusterPapers,
    GeneratePaperSummaryPrompts,
    GenerateResearchSynthesisPrompt
)
class RunMLPipeline(d6tflow.tasks.TaskPickle):
    """
    Run complete ML pipeline.
    
    Usage:
        python pipeline/ml_tasks.py
    """
    
    def run(self):
        """Generate ML pipeline report."""
        preprocess = self.input()[0].load()
        features = self.input()[1].load()
        topics = self.input()[2].load()
        predictor = self.input()[3].load()
        clusters = self.input()[4].load()
        prompts = self.input()[5].load()
        synthesis = self.input()[6].load()
        
        report = {
            'pipeline': 'ml_complete',
            'timestamp': datetime.now().isoformat(),
            'results': {
                'preprocessing': {
                    'documents': preprocess['n_documents'],
                    'vocabulary': preprocess['vocabulary_size']
                },
                'features': {
                    'total_features': features['n_features'],
                    'samples': features['n_samples']
                },
                'topics': {
                    'n_topics': topics['n_topics'],
                    'perplexity': topics['perplexity']
                },
                'citation_prediction': {
                    'test_r2': predictor['test_r2'],
                    'test_rmse': predictor['test_rmse']
                },
                'clustering': {
                    'n_clusters': clusters['n_clusters'],
                    'inertia': clusters['inertia']
                },
                'prompts': {
                    'paper_prompts': prompts['n_prompts'],
                    'synthesis_prompts': synthesis['n_cluster_prompts'] + 1
                }
            }
        }
        
        self.save(report)
        
        print(f"\n{'='*70}")
        print("ML PIPELINE COMPLETE")
        print(f"{'='*70}")
        print(f"✓ Preprocessed {preprocess['n_documents']} documents")
        print(f"✓ Engineered {features['n_features']} features")
        print(f"✓ Discovered {topics['n_topics']} topics")
        print(f"✓ Trained citation predictor (R² = {predictor['test_r2']:.3f})")
        print(f"✓ Clustered papers into {clusters['n_clusters']} groups")
        print(f"✓ Generated {prompts['n_prompts']} LLM prompts")
        print(f"✓ Created {synthesis['n_cluster_prompts']} synthesis prompts")
        print(f"\nModels saved to: {Config.DATA_DIR}/")
        print(f"Prompts saved to: {Config.RESULTS_DIR}/")
        print(f"{'='*70}")


if __name__ == '__main__':
    # Run the ML pipeline
    d6tflow.run(RunMLPipeline())
