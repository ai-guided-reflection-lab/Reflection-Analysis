from typing import List, Dict, Any, Optional
import pandas as pd
import json
from application.controller.gpt_api import Model, PromptConfig
import plotly.express as px
import plotly.graph_objects as go
import logging

class TopicClassifier:
    """Process and classify reflections based on previously identified topics"""
    
    def __init__(self, topics: List[Dict[str, Any]]):
        """
        Initialize the classifier with a list of topics.
        
        Args:
            topics (List[Dict[str, Any]]): List of topics with their characteristics from topic extraction
                Each topic should have either:
                - topic, frequency, sentiment, example_quotes, implications
                OR
                - theme, frequency, sentiment, example_quotes, implications
        """
        self.logger = logging.getLogger(__name__)
        self.topics = self._process_topics(topics)
        self.classified_data = None
        
    def _process_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and validate the input topics.
        Handles both 'topic' and 'theme' key formats.
        """
        if not topics:
            self.logger.warning("No topics provided for processing")
            return []
            
        processed_topics = []
        for topic_data in topics:
            try:
                # Handle both 'topic' and 'theme' keys
                topic_name = topic_data.get('topic') or topic_data.get('theme')
                if not topic_name:
                    self.logger.warning(f"Missing topic/theme name in data: {topic_data}")
                    continue
                    
                processed_topic = {
                    'name': topic_name,
                    'frequency': self._extract_frequency(topic_data.get('frequency', '')),
                    'sentiment': topic_data.get('sentiment', 'neutral'),
                    'examples': topic_data.get('example_quotes', []),
                    'implications': topic_data.get('implications', '')
                }
                
                # Validate required fields
                if not processed_topic['examples']:
                    self.logger.warning(f"No example quotes for topic: {topic_name}")
                if not processed_topic['implications']:
                    self.logger.warning(f"No implications for topic: {topic_name}")
                    
                processed_topics.append(processed_topic)
                
            except Exception as e:
                self.logger.error(f"Error processing topic data: {str(e)}")
                self.logger.debug(f"Problematic topic data: {topic_data}")
                continue
                
        if not processed_topics:
            self.logger.error("No valid topics were processed")
            
        return processed_topics
        
    def _extract_frequency(self, frequency_str: str) -> int:
        """
        Extract numeric frequency from string like '20 reflections'.
        Returns 0 if no valid number found.
        """
        try:
            # Handle both numeric and string formats
            if isinstance(frequency_str, (int, float)):
                return int(frequency_str)
                
            # Extract digits from string
            digits = ''.join(filter(str.isdigit, str(frequency_str)))
            return int(digits) if digits else 0
            
        except Exception as e:
            self.logger.warning(f"Error extracting frequency from '{frequency_str}': {str(e)}")
            return 0
        
    def classify_reflection(self, reflection_text: str, model: str = "gpt-4o", 
                          temp: float = 0.7, max_tokens: int = 500) -> Dict[str, Any]:
        """
        Classify a single reflection based on the predefined topics.
        
        Args:
            reflection_text (str): The reflection text to classify
            model (str): GPT model to use
            temp (float): Temperature for GPT response
            max_tokens (int): Maximum tokens for GPT response
            
        Returns:
            Dict[str, Any]: Classification results
        """
        if not self.topics:
            self.logger.error("No topics available for classification")
            return {}
            
        try:
            # Prepare classification prompt
            classification_prompt = {
                "task": "Classify this reflection according to the provided topics",
                "topics": [{'name': t['name'], 'sentiment': t['sentiment']} for t in self.topics],
                "reflection": reflection_text
            }
            
            # Get classification from GPT
            result = Model.prompt(
                instructions=classification_prompt,
                user_response=reflection_text,
                model=model,
                temp=temp,
                max_tokens=max_tokens
            )
            
            # Parse result
            if isinstance(result, str):
                result = json.loads(result)
                
            return self._format_classification(result)
            
        except Exception as e:
            self.logger.error(f"Error classifying reflection: {str(e)}")
            return {}
            
    def batch_classify(self, reflections_df: pd.DataFrame, 
                      reflection_col: str = 'Reflection') -> pd.DataFrame:
        """
        Classify multiple reflections in batch.
        
        Args:
            reflections_df (pd.DataFrame): DataFrame containing reflections
            reflection_col (str): Name of column containing reflection text
            
        Returns:
            pd.DataFrame: DataFrame with classification results
        """
        if reflection_col not in reflections_df.columns:
            self.logger.error(f"Column '{reflection_col}' not found in DataFrame")
            return pd.DataFrame()
            
        try:
            classifications = []
            total = len(reflections_df)
            
            for idx, row in reflections_df.iterrows():
                self.logger.info(f"Processing reflection {idx + 1}/{total}")
                reflection_text = row[reflection_col]
                
                if pd.notna(reflection_text):
                    result = self.classify_reflection(reflection_text)
                    result['reflection_id'] = idx
                    classifications.append(result)
                else:
                    self.logger.warning(f"Empty reflection at index {idx}")
                    
            # Create DataFrame from classifications
            classified_df = pd.DataFrame(classifications)
            self.classified_data = classified_df
            
            return classified_df
            
        except Exception as e:
            self.logger.error(f"Error in batch classification: {str(e)}")
            return pd.DataFrame()
            
    def _format_classification(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format the classification result into a standardized structure"""
        formatted = {
            'topics': [],
            'confidence_scores': [],
            'evidence': [],
            'sentiment_matches': [],
            'sentiment_explanations': []
        }
        
        # Process topics from the result
        for topic in result.get('topics', []):
            formatted['topics'].append(topic.get('topic_name', ''))
            formatted['confidence_scores'].append(topic.get('confidence_score', 0.0))
            formatted['evidence'].append(topic.get('evidence', ''))
            formatted['sentiment_matches'].append(topic.get('sentiment_match', False))
            formatted['sentiment_explanations'].append(topic.get('sentiment_explanation', ''))
            
        # Add topic interactions and unique aspects
        formatted['topic_interactions'] = result.get('topic_interactions', {})
        formatted['unique_aspects'] = result.get('unique_aspects', '')
        formatted['classification_summary'] = result.get('classification_summary', '')
        
        return formatted
        
    def get_topic_distribution(self) -> pd.DataFrame:
        """
        Get distribution of topics across all classified reflections.
        
        Returns:
            pd.DataFrame: Topic distribution statistics
        """
        if self.classified_data is None:
            return pd.DataFrame()
            
        try:
            # Explode topics to get one row per topic
            topics_df = self.classified_data.explode('topics')
            
            # Calculate topic frequencies
            topic_counts = topics_df['topics'].value_counts().reset_index()
            topic_counts.columns = ['Topic', 'Count']
            
            # Calculate average confidence scores per topic
            topic_scores = topics_df.groupby('topics')['confidence_scores'].mean().reset_index()
            topic_scores.columns = ['Topic', 'Avg_Confidence']
            
            # Merge counts and scores
            distribution = pd.merge(topic_counts, topic_scores, on='Topic')
            
            return distribution
            
        except Exception as e:
            print(f"Error calculating topic distribution: {e}")
            return pd.DataFrame()
            
    def get_sentiment_analysis(self) -> pd.DataFrame:
        """
        Get sentiment analysis for each topic.
        
        Returns:
            pd.DataFrame: Sentiment analysis statistics
        """
        if self.classified_data is None:
            return pd.DataFrame()
            
        try:
            # Explode topics and corresponding sentiment matches
            sentiment_df = pd.DataFrame({
                'topics': self.classified_data['topics'].explode(),
                'sentiment_matches': self.classified_data['sentiment_matches'].explode()
            })
            
            # Calculate sentiment statistics
            sentiment_stats = sentiment_df.groupby('topics').agg({
                'sentiment_matches': ['count', 'mean']
            }).reset_index()
            
            sentiment_stats.columns = ['Topic', 'Total_Mentions', 'Sentiment_Match_Rate']
            
            return sentiment_stats
            
        except Exception as e:
            print(f"Error calculating sentiment analysis: {e}")
            return pd.DataFrame()
            
    def visualize_topic_distribution(self) -> go.Figure:
        """Create an interactive bar chart of topic distribution"""
        distribution = self.get_topic_distribution()
        if distribution.empty:
            return None
            
        fig = px.bar(
            distribution,
            x='Topic',
            y='Count',
            color='Avg_Confidence',
            title='Topic Distribution with Confidence Scores',
            labels={'Count': 'Number of Reflections', 'Avg_Confidence': 'Average Confidence'},
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=True,
            height=500,
            margin=dict(t=50, l=50, r=50, b=150)
        )
        
        return fig
        
    def visualize_sentiment_distribution(self) -> go.Figure:
        """Create an interactive heatmap of sentiment distribution"""
        sentiment_stats = self.get_sentiment_analysis()
        if sentiment_stats.empty:
            return None
            
        fig = px.scatter(
            sentiment_stats,
            x='Topic',
            y='Sentiment_Match_Rate',
            size='Total_Mentions',
            color='Sentiment_Match_Rate',
            title='Topic Sentiment Analysis',
            labels={
                'Sentiment_Match_Rate': 'Sentiment Match Rate',
                'Total_Mentions': 'Total Mentions'
            },
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=True,
            height=500,
            margin=dict(t=50, l=50, r=50, b=150)
        )
        
        return fig
        
    def get_topic_relationships(self) -> pd.DataFrame:
        """
        Analyze relationships between topics based on co-occurrence.
        
        Returns:
            pd.DataFrame: Topic relationship statistics
        """
        if self.classified_data is None:
            return pd.DataFrame()
            
        try:
            # Create a matrix of topic co-occurrences
            topic_pairs = []
            for _, row in self.classified_data.iterrows():
                topics = row['topics']
                for i, topic1 in enumerate(topics):
                    for topic2 in topics[i+1:]:
                        topic_pairs.append({
                            'Topic1': topic1,
                            'Topic2': topic2,
                            'Interaction': row['topic_interactions'].get('description', ''),
                            'Strength': row['topic_interactions'].get('strength', 'Weak')
                        })
            
            return pd.DataFrame(topic_pairs)
            
        except Exception as e:
            print(f"Error analyzing topic relationships: {e}")
            return pd.DataFrame() 