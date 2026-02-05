import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import streamlit as st
from itertools import combinations
import math

class PipelineReportBuilder:
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the report builder with classification results
        
        Args:
            df (pd.DataFrame): DataFrame containing at least reflection_id, original_reflection, and topic columns
        """
        self.df = df
        self.topic_pairs = self._get_topic_pairs()
        self.topic_frequencies = self._get_topic_frequencies()
        
    def _get_topic_pairs(self) -> pd.DataFrame:
        """Calculate co-occurrence of topics"""
        # Group by reflection_id to get all topics per reflection
        grouped = self.df.groupby('reflection_id')['topic'].agg(list).reset_index()
        
        # Generate topic pairs
        pairs = []
        for _, row in grouped.iterrows():
            # Get unique combinations of topics in this reflection
            for topic1, topic2 in combinations(set(row['topic']), 2):
                pairs.append({
                    'topic1': min(topic1, topic2),  # Ensure consistent ordering
                    'topic2': max(topic1, topic2),
                    'reflection_id': row['reflection_id']
                })
        
        # Convert to DataFrame and get pair frequencies
        pairs_df = pd.DataFrame(pairs)
        if not pairs_df.empty:
            pair_counts = pairs_df.groupby(['topic1', 'topic2']).size().reset_index(name='frequency')
            return pair_counts
        return pd.DataFrame(columns=['topic1', 'topic2', 'frequency'])

    def _get_topic_frequencies(self) -> pd.Series:
        """Calculate individual topic frequencies"""
        return self.df['topic'].value_counts()

    def create_relationship_graph(self) -> go.Figure:
        """Create an improved, more readable relationship graph"""
        if self.topic_pairs.empty:
            return go.Figure()

        # Calculate frequencies and co-occurrences
        topic_freqs = self.df['topic'].value_counts()
        max_freq = topic_freqs.max()
        
        # Create a more organized layout
        topics = list(topic_freqs.index)
        n_topics = len(topics)
        
        # Create circular layout coordinates
        radius = 1
        angles = [2 * math.pi * i / n_topics for i in range(n_topics)]
        x_coords = [radius * math.cos(angle) for angle in angles]
        y_coords = [radius * math.sin(angle) for angle in angles]
        
        # Create edges (connections between topics)
        edge_traces = []
        max_co_occurrence = self.topic_pairs['frequency'].max()
        
        for _, row in self.topic_pairs.iterrows():
            # Get coordinates for both topics
            idx1 = topics.index(row['topic1'])
            idx2 = topics.index(row['topic2'])
            
            # Calculate line width based on co-occurrence frequency
            width = (row['frequency'] / max_co_occurrence) * 10  # Scale line width
            opacity = (row['frequency'] / max_co_occurrence) * 0.8 + 0.2  # Scale opacity
            
            edge_traces.append(
                go.Scatter(
                    x=[x_coords[idx1], x_coords[idx2]],
                    y=[y_coords[idx1], y_coords[idx2]],
                    mode='lines',
                    line=dict(
                        width=width,
                        color=f'rgba(169, 169, 169, {opacity})'  # Use opacity for visual hierarchy
                    ),
                    hoverinfo='text',
                    hovertext=(f"Connection between {row['topic1']} and {row['topic2']}<br>"
                              f"Co-occurs {row['frequency']} times"),
                    showlegend=False
                )
            )

        # Create nodes (topics)
        node_trace = go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='markers+text',
            marker=dict(
                size=[30 * (freq / max_freq) + 20 for freq in topic_freqs],  # Scale node sizes
                color='lightblue',
                line=dict(width=2, color='darkblue'),
                opacity=0.8
            ),
            text=topics,
            textposition="middle center",
            hoverinfo='text',
            hovertext=[f"{topic}<br>Appears {topic_freqs[topic]} times" for topic in topics]
        )

        # Create figure with improved layout
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title={
                'text': 'Topic Relationships Network',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=20, r=20, t=40),
            height=600,
            width=800,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1.5, 1.5]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1.5, 1.5]
            ),
            plot_bgcolor='white'
        )
        
        # Add a legend explaining the visualization
        fig.add_annotation(
            text=(
                "• Node size indicates topic frequency<br>"
                "• Line thickness shows how often topics appear together<br>"
                "• Darker lines indicate stronger connections"
            ),
            xref="paper", yref="paper",
            x=0, y=-0.1,
            showarrow=False,
            font=dict(size=10),
            align="left"
        )

        return fig

    def create_heatmap(self) -> go.Figure:
        """Create a heatmap of topic co-occurrences"""
        # Pivot the pairs data to create a matrix
        matrix = pd.pivot_table(
            self.topic_pairs, 
            values='frequency',
            index='topic1',
            columns='topic2',
            fill_value=0
        )
        
        # Create heatmap
        fig = px.imshow(
            matrix,
            labels=dict(x="Topic", y="Topic", color="Frequency"),
            title="Topic Co-occurrence Heatmap"
        )
        
        fig.update_layout(
            height=600,
            xaxis_tickangle=-45
        )
        
        return fig

    def get_topic_stats(self) -> pd.DataFrame:
        """Generate statistical summary of topics"""
        stats = pd.DataFrame({
            'Frequency': self.topic_frequencies,
            'Percentage': (self.topic_frequencies / len(self.df) * 100).round(2)
        })
        
        # Add co-occurrence information
        stats['Most Common Pair'] = stats.index.map(self._get_most_common_pair)
        
        return stats
    
    def _get_most_common_pair(self, topic: str) -> str:
        """Find the most common co-occurring topic for a given topic"""
        pairs = self.topic_pairs[
            (self.topic_pairs['topic1'] == topic) | 
            (self.topic_pairs['topic2'] == topic)
        ]
        if pairs.empty:
            return "None"
        
        # Get the other topic in the most frequent pair
        max_pair = pairs.loc[pairs['frequency'].idxmax()]
        other_topic = max_pair['topic2'] if max_pair['topic1'] == topic else max_pair['topic1']
        return f"{other_topic} ({max_pair['frequency']} times)"

    def get_topic_count_per_reflection(self) -> pd.DataFrame:
        """Analyze how many topics each reflection contains"""
        # Count topics per reflection
        topic_counts = self.df.groupby('reflection_id')['topic'].count().value_counts().sort_index()
        
        # Create statistics DataFrame
        stats_df = pd.DataFrame({
            'Number of Topics': topic_counts.index,
            'Number of Reflections': topic_counts.values,
            'Percentage': (topic_counts.values / len(self.df['reflection_id'].unique()) * 100).round(2)
        })
        
        return stats_df

    def create_topic_count_chart(self) -> go.Figure:
        """Create bar chart showing distribution of topic counts per reflection"""
        stats_df = self.get_topic_count_per_reflection()
        
        fig = px.bar(
            stats_df,
            x='Number of Topics',
            y='Number of Reflections',
            text='Percentage',
            title='Distribution of Topics per Reflection',
            labels={'Number of Topics': 'Number of Topics in Reflection',
                    'Number of Reflections': 'Count of Reflections',
                    'Percentage': 'Percentage of Total Reflections'}
        )
        
        fig.update_traces(
            texttemplate='%{text:.1f}%',
            textposition='outside'
        )
        
        fig.update_layout(
            height=400,
            xaxis=dict(tickmode='linear'),
            showlegend=False
        )
        
        return fig

    def get_common_topic_combinations(self) -> pd.DataFrame:
        """Analyze common combinations of topics"""
        # Group by reflection_id to get all topic combinations
        grouped = self.df.groupby('reflection_id')['topic'].agg(list).reset_index()
        
        # Get all combinations of different sizes
        combinations_dict = {}
        for _, row in grouped.iterrows():
            topics = sorted(set(row['topic']))  # Remove duplicates and sort
            n_topics = len(topics)
            topic_str = ' + '.join(topics)
            
            # Add to combinations dictionary
            if n_topics > 1:  # Only include combinations of 2 or more
                combinations_dict[topic_str] = combinations_dict.get(topic_str, 0) + 1
        
        # Convert to DataFrame
        if combinations_dict:
            combos_df = pd.DataFrame([
                {'Combination': k, 'Count': v, 'Number of Topics': len(k.split(' + '))}
                for k, v in combinations_dict.items()
            ])
            
            # Sort by count and number of topics
            combos_df = combos_df.sort_values(['Count', 'Number of Topics'], ascending=[False, True])
            
            # Calculate percentage
            total_reflections = len(grouped)
            combos_df['Percentage'] = (combos_df['Count'] / total_reflections * 100).round(2)
            
            return combos_df
        
        return pd.DataFrame(columns=['Combination', 'Count', 'Number of Topics', 'Percentage'])

    def create_common_combinations_chart(self) -> go.Figure:
        """Create bar chart showing most common topic combinations"""
        combos_df = self.get_common_topic_combinations()
        
        if combos_df.empty:
            return go.Figure()
        
        # Take top 10 combinations for visualization
        top_combos = combos_df.head(10)
        
        fig = px.bar(
            top_combos,
            x='Count',
            y='Combination',
            color='Number of Topics',
            orientation='h',
            title='Top 10 Most Common Topic Combinations',
            labels={'Count': 'Number of Occurrences',
                    'Combination': 'Topic Combination',
                    'Number of Topics': 'Topics in Combination'}
        )
        
        fig.update_layout(
            height=500,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=True
        )
        
        return fig

    def get_sentiment_stats(self) -> pd.DataFrame:
        """Generate sentiment statistics for each topic"""
        if 'topic_sentiment' not in self.df.columns:
            return pd.DataFrame()
        
        def categorize_sentiment(sentiment):
            """Standardize sentiment values"""
            if pd.isna(sentiment) or sentiment == '':
                return 'other'
            
            sentiment = str(sentiment).lower().strip()
            
            if sentiment == 'positive' or sentiment == 'true':
                return 'pos'
            elif sentiment == 'negative' or sentiment == 'false':
                return 'neg'
            elif sentiment == 'neutral':
                return 'neu'
            else:
                return 'other'  # Catches 'mixed', 'neutral/negative', and any other variations
        
        # Create sentiment counts for each topic
        sentiment_stats = []
        for topic in self.topic_frequencies.index:
            topic_data = self.df[self.df['topic'] == topic]
            total = len(topic_data)
            
            # Standardize and count sentiments
            topic_data['standardized_sentiment'] = topic_data['topic_sentiment'].apply(categorize_sentiment)
            sentiment_counts = topic_data['standardized_sentiment'].value_counts()
            
            pos = sentiment_counts.get('pos', 0)
            neu = sentiment_counts.get('neu', 0)
            neg = sentiment_counts.get('neg', 0)
            other = sentiment_counts.get('other', 0)
            
            # Calculate validation total (sum of all clear sentiment counts)
            validation_total = pos + neu + neg  # Excluding 'other' from validation total
            
            sentiment_stats.append({
                'Topic': topic,
                'Totals': total,
                'Pos': pos,
                'Neu': neu,
                'Neg': neg,
                'Other': other,
                'Total Validation': validation_total
            })
        
        # Convert to DataFrame and sort by Totals
        stats_df = pd.DataFrame(sentiment_stats)
        stats_df = stats_df.sort_values('Totals', ascending=False)
        
        return stats_df

    def create_sentiment_heatmap(self) -> go.Figure:
        """Create a heatmap showing sentiment distribution for each topic"""
        sentiment_stats = self.get_sentiment_stats()
        if sentiment_stats.empty:
            return go.Figure()
        
        # Create separate matrices for each sentiment
        topics = sentiment_stats['Topic']
        total_counts = sentiment_stats['Totals']
        
        # Calculate percentages for each sentiment
        pos_pct = (sentiment_stats['Pos'] / total_counts * 100).round(2)
        neu_pct = (sentiment_stats['Neu'] / total_counts * 100).round(2)
        neg_pct = (sentiment_stats['Neg'] / total_counts * 100).round(2)
        
        # Create figure with three subplots (one for each sentiment)
        fig = go.Figure()
        
        # Add positive sentiment (green)
        fig.add_trace(go.Heatmap(
            z=[pos_pct],
            x=topics,
            y=['Positive'],
            colorscale=[[0, 'white'], [1, 'green']],
            showscale=False,
            text=[[f"{x}%" for x in pos_pct]],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False,
            hovertemplate="Topic: %{x}<br>Positive: %{text}<extra></extra>"
        ))
        
        # Add neutral sentiment (gray)
        fig.add_trace(go.Heatmap(
            z=[neu_pct],
            x=topics,
            y=['Neutral'],
            colorscale=[[0, 'white'], [1, 'gray']],
            showscale=False,
            text=[[f"{x}%" for x in neu_pct]],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False,
            hovertemplate="Topic: %{x}<br>Neutral: %{text}<extra></extra>"
        ))
        
        # Add negative sentiment (red)
        fig.add_trace(go.Heatmap(
            z=[neg_pct],
            x=topics,
            y=['Negative'],
            colorscale=[[0, 'white'], [1, 'red']],
            showscale=False,
            text=[[f"{x}%" for x in neg_pct]],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False,
            hovertemplate="Topic: %{x}<br>Negative: %{text}<extra></extra>"
        ))
        
        # Update layout
        fig.update_layout(
            title="Topic Sentiment Distribution (%)",
            height=300,
            xaxis_tickangle=-45,
            yaxis={'categoryorder': 'array', 
                   'categoryarray': ['Negative', 'Neutral', 'Positive']},
            yaxis_title="Sentiment",
            xaxis_title="Topic",
            showlegend=False,
            margin=dict(t=50, l=50, r=50, b=100)
        )
        
        return fig

    def create_sentiment_stacked_bar(self) -> go.Figure:
        """Create a stacked bar chart showing sentiment counts for each topic"""
        sentiment_stats = self.get_sentiment_stats()
        if sentiment_stats.empty:
            return go.Figure()
        
        # Create stacked bar chart
        fig = go.Figure(data=[
            go.Bar(name='Positive', x=sentiment_stats['Topic'], y=sentiment_stats['Pos'], marker_color='green'),
            go.Bar(name='Neutral', x=sentiment_stats['Topic'], y=sentiment_stats['Neu'], marker_color='gray'),
            go.Bar(name='Negative', x=sentiment_stats['Topic'], y=sentiment_stats['Neg'], marker_color='red'),
            go.Bar(name='Other', x=sentiment_stats['Topic'], y=sentiment_stats['Other'], marker_color='purple')
        ])
        
        fig.update_layout(
            barmode='stack',
            title='Topic Sentiment Distribution (Counts)',
            xaxis_tickangle=-45,
            height=400,
            legend_title="Sentiment",
            hovermode='x'
        )
        
        return fig

    def create_sentiment_summary_table(self) -> None:
        """Create and display a formatted sentiment summary table in Streamlit"""
        stats = self.get_sentiment_stats()
        if stats.empty:
            st.info("No sentiment data available")
            return
        
        # Create a styled table
        st.markdown("### QUICK STATS")
        
        # Style the dataframe
        styled_stats = stats.style.format({
            'Totals': '{:,.0f}',
            'Pos': '{:,.0f}',
            'Neu': '{:,.0f}',
            'Neg': '{:,.0f}',
            'Other': '{:,.0f}',
            'Total Validation': '{:,.0f}'
        }).background_gradient(
            subset=['Pos'], cmap='Greens'
        ).background_gradient(
            subset=['Neg'], cmap='Reds'
        ).background_gradient(
            subset=['Neu'], cmap='Greys'
        ).background_gradient(
            subset=['Other'], cmap='Purples'
        )
        
        st.dataframe(styled_stats, use_container_width=True)

    def get_combination_examples(self) -> Dict[str, List[str]]:
        """Get examples for each topic combination that appears more than once"""
        # Group reflections by their combination of topics
        combination_examples = {}
        
        # Group by reflection_id to get all unique combinations
        grouped = self.df.groupby('reflection_id')
        
        for reflection_id, group in grouped:
            # Get unique topics for this reflection
            topics = sorted(group['topic'].unique())
            if len(topics) > 1:  # Only include combinations of 2 or more topics
                combo = ' + '.join(topics)
                
                # Get the reflection text (take first occurrence since it's the same for the reflection_id)
                reflection_text = group['original_reflection'].iloc[0]
                
                if combo in combination_examples:
                    combination_examples[combo].append(reflection_text)
                else:
                    combination_examples[combo] = [reflection_text]
        
        # Filter to only include combinations with more than one example
        return {k: v for k, v in combination_examples.items() if len(v) > 1}

    def get_combination_sentiments(self) -> pd.DataFrame:
        """Analyze sentiment distribution for topic combinations"""
        # Group by reflection_id to get combinations and their sentiments
        combination_sentiments = []
        
        grouped = self.df.groupby('reflection_id')
        for reflection_id, group in grouped:
            # Get unique topics for this reflection
            topics = sorted(group['topic'].unique())
            if len(topics) > 1:  # Only include combinations of 2 or more topics
                combo = ' + '.join(topics)
                
                # Get sentiments for this combination
                sentiments = group['topic_sentiment'].apply(lambda x: str(x).lower().strip())
                
                # Count sentiments
                pos = sum(1 for s in sentiments if s in ['positive', 'true'])
                neu = sum(1 for s in sentiments if s == 'neutral')
                neg = sum(1 for s in sentiments if s in ['negative', 'false'])
                other = len(sentiments) - (pos + neu + neg)
                
                combination_sentiments.append({
                    'Combination': combo,
                    'Pos': pos,
                    'Neu': neu,
                    'Neg': neg,
                    'Other': other,
                    'Total': len(topics)
                })
        
        # Convert to DataFrame and aggregate by combination
        if combination_sentiments:
            df = pd.DataFrame(combination_sentiments)
            agg_df = df.groupby('Combination').agg({
                'Pos': 'sum',
                'Neu': 'sum',
                'Neg': 'sum',
                'Other': 'sum',
                'Total': 'count'  # This becomes the count of occurrences
            }).reset_index()
            
            # Calculate percentages
            for col in ['Pos', 'Neu', 'Neg', 'Other']:
                agg_df[f'{col}_pct'] = (agg_df[col] / agg_df['Total'] * 100).round(2)
            
            return agg_df.sort_values('Total', ascending=False)
        
        return pd.DataFrame()

    def create_combination_sentiment_heatmap(self) -> go.Figure:
        """Create a heatmap showing sentiment distribution for topic combinations"""
        combo_sentiments = self.get_combination_sentiments()
        if combo_sentiments.empty:
            return go.Figure()
        
        # Take top 10 combinations by frequency
        top_combos = combo_sentiments.head(10)
        
        # Create figure with three subplots (one for each sentiment)
        fig = go.Figure()
        
        # Add positive sentiment (green)
        fig.add_trace(go.Heatmap(
            z=[top_combos['Pos_pct']],
            x=top_combos['Combination'],
            y=['Positive'],
            colorscale=[[0, 'white'], [1, 'green']],
            showscale=False,
            text=[[f"{x}%" for x in top_combos['Pos_pct']]],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        # Add neutral sentiment (gray)
        fig.add_trace(go.Heatmap(
            z=[top_combos['Neu_pct']],
            x=top_combos['Combination'],
            y=['Neutral'],
            colorscale=[[0, 'white'], [1, 'gray']],
            showscale=False,
            text=[[f"{x}%" for x in top_combos['Neu_pct']]],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        # Add negative sentiment (red)
        fig.add_trace(go.Heatmap(
            z=[top_combos['Neg_pct']],
            x=top_combos['Combination'],
            y=['Negative'],
            colorscale=[[0, 'white'], [1, 'red']],
            showscale=False,
            text=[[f"{x}%" for x in top_combos['Neg_pct']]],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Topic Combination Sentiment Distribution (%)",
            height=300,
            xaxis_tickangle=-45,
            yaxis={'categoryorder': 'array', 
                   'categoryarray': ['Negative', 'Neutral', 'Positive']},
            showlegend=False,
            margin=dict(t=50, l=50, r=50, b=120)
        )
        
        return fig

    def create_combination_sentiment_bars(self) -> go.Figure:
        """Create a stacked bar chart showing sentiment distribution for combinations"""
        combo_sentiments = self.get_combination_sentiments()
        if combo_sentiments.empty:
            return go.Figure()
        
        # Take top 10 combinations
        top_combos = combo_sentiments.head(10)
        
        fig = go.Figure(data=[
            go.Bar(name='Positive', x=top_combos['Combination'], y=top_combos['Pos'], marker_color='green'),
            go.Bar(name='Neutral', x=top_combos['Combination'], y=top_combos['Neu'], marker_color='gray'),
            go.Bar(name='Negative', x=top_combos['Combination'], y=top_combos['Neg'], marker_color='red'),
            go.Bar(name='Other', x=top_combos['Combination'], y=top_combos['Other'], marker_color='purple')
        ])
        
        fig.update_layout(
            barmode='stack',
            title='Topic Combination Sentiment Distribution (Counts)',
            xaxis_tickangle=-45,
            height=400,
            legend_title="Sentiment",
            hovermode='x',
            margin=dict(t=50, l=50, r=50, b=120)
        )
        
        return fig

    def get_combination_detailed_sentiments(self) -> List[Dict]:
        """Get detailed sentiment breakdown for each topic within combinations"""
        # First check if we have sentiment data
        has_sentiment = 'topic_sentiment' in self.df.columns
        
        combination_details = []
        
        # Group by reflection_id to get combinations
        grouped = self.df.groupby('reflection_id')
        for reflection_id, group in grouped:
            # Only process groups with multiple topics
            if len(group['topic'].unique()) > 1:
                combo_data = {
                    'reflection_id': reflection_id,
                    'combination': ' + '.join(sorted(group['topic'].unique())),
                    'topic_sentiments': []
                }
                
                # Get sentiment for each topic in the combination
                for _, row in group.iterrows():
                    if has_sentiment:
                        sentiment = str(row['topic_sentiment']).lower().strip()
                        if sentiment in ['positive', 'true']:
                            sentiment = 'positive'
                        elif sentiment in ['negative', 'false']:
                            sentiment = 'negative'
                        elif sentiment == 'neutral':
                            sentiment = 'neutral'
                        else:
                            sentiment = 'other'
                    else:
                        sentiment = 'unknown'  # Default when no sentiment data available
                    
                    combo_data['topic_sentiments'].append({
                        'topic': row['topic'],
                        'sentiment': sentiment
                    })
                
                combination_details.append(combo_data)
        
        # Process the detailed data into a summary DataFrame
        summary_data = []
        for combo in combination_details:
            combo_str = combo['combination']
            if not any(d['combination'] == combo_str for d in summary_data):
                all_instances = [c for c in combination_details if c['combination'] == combo_str]
                topics = combo_str.split(' + ')
                topic_sentiment_summary = {}
                
                for topic in topics:
                    topic_sentiments = []
                    for instance in all_instances:
                        for ts in instance['topic_sentiments']:
                            if ts['topic'] == topic:
                                topic_sentiments.append(ts['sentiment'])
                    
                    total = len(topic_sentiments)
                    if has_sentiment:
                        topic_sentiment_summary[topic] = {
                            'positive': topic_sentiments.count('positive') / total * 100,
                            'neutral': topic_sentiments.count('neutral') / total * 100,
                            'negative': topic_sentiments.count('negative') / total * 100,
                            'other': topic_sentiments.count('other') / total * 100
                        }
                    else:
                        # When no sentiment data is available
                        topic_sentiment_summary[topic] = {
                            'positive': 0,
                            'neutral': 0,
                            'negative': 0,
                            'other': 0,
                            'unknown': 100  # All marked as unknown
                        }
                
                summary_data.append({
                    'combination': combo_str,
                    'occurrence_count': len(all_instances),
                    'topic_sentiments': topic_sentiment_summary,
                    'has_sentiment_data': has_sentiment
                })
        
        return summary_data

    def display_combination_sentiment_analysis(self):
        """Display detailed sentiment analysis for topic combinations"""
        summary_data = self.get_combination_detailed_sentiments()
        
        if not summary_data:
            st.info("No topic combinations found.")
            return
        
        # Sort combinations by occurrence count
        summary_data.sort(key=lambda x: x['occurrence_count'], reverse=True)
        
        # Take top 10 combinations for display
        for idx, combo_data in enumerate(summary_data[:10]):
            with st.expander(f"{combo_data['combination']} ({combo_data['occurrence_count']} occurrences)"):
                # Create a clear table showing sentiment breakdown per topic
                topics = combo_data['combination'].split(' + ')
                
                # Create a more readable table
                st.write("Sentiment breakdown for each topic in this combination:")
                
                # Create columns for the table header
                cols = st.columns([3, 1, 1, 1, 1])
                cols[0].markdown("**Topic**")
                cols[1].markdown("**Positive**")
                cols[2].markdown("**Neutral**")
                cols[3].markdown("**Negative**")
                cols[4].markdown("**Other**")
                
                # Add a separator line
                st.markdown("---")
                
                # Display data for each topic
                for topic in topics:
                    sentiment_dist = combo_data['topic_sentiments'][topic]
                    
                    # Create row with colored backgrounds for sentiment percentages
                    cols = st.columns([3, 1, 1, 1, 1])
                    cols[0].write(topic)
                    
                    # Helper function to create colored percentage text
                    def format_percentage(value, color):
                        if value > 0:
                            return f"<span style='color: {color}; font-weight: bold;'>{value:.1f}%</span>"
                        return f"{value:.1f}%"
                    
                    # Display percentages with colors
                    cols[1].markdown(format_percentage(sentiment_dist['positive'], 'green'), unsafe_allow_html=True)
                    cols[2].markdown(format_percentage(sentiment_dist['neutral'], 'gray'), unsafe_allow_html=True)
                    cols[3].markdown(format_percentage(sentiment_dist['negative'], 'red'), unsafe_allow_html=True)
                    cols[4].markdown(format_percentage(sentiment_dist['other'], 'purple'), unsafe_allow_html=True)
                    
                    # Add a light separator between topics
                    st.markdown("---")
                
                # Add a summary visualization
                st.write("Visual breakdown:")
                
                # Create a more readable bar chart
                fig = go.Figure()
                
                # Add bars for each sentiment type
                x_positions = list(range(len(topics)))
                
                # Add bars for each sentiment with consistent colors
                fig.add_trace(go.Bar(
                    name='Positive',
                    x=x_positions,
                    y=[combo_data['topic_sentiments'][topic]['positive'] for topic in topics],
                    marker_color='green',
                    text=[f"{combo_data['topic_sentiments'][topic]['positive']:.1f}%" for topic in topics],
                    textposition='auto'
                ))
                
                fig.add_trace(go.Bar(
                    name='Neutral',
                    x=x_positions,
                    y=[combo_data['topic_sentiments'][topic]['neutral'] for topic in topics],
                    marker_color='gray',
                    text=[f"{combo_data['topic_sentiments'][topic]['neutral']:.1f}%" for topic in topics],
                    textposition='auto'
                ))
                
                fig.add_trace(go.Bar(
                    name='Negative',
                    x=x_positions,
                    y=[combo_data['topic_sentiments'][topic]['negative'] for topic in topics],
                    marker_color='red',
                    text=[f"{combo_data['topic_sentiments'][topic]['negative']:.1f}%" for topic in topics],
                    textposition='auto'
                ))
                
                fig.update_layout(
                    barmode='group',
                    xaxis=dict(
                        ticktext=topics,
                        tickvals=x_positions,
                        tickangle=-45
                    ),
                    yaxis=dict(title='Percentage'),
                    height=400,
                    margin=dict(t=30, l=30, r=30, b=100),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                # Add unique key when displaying the chart
                st.plotly_chart(
                    fig, 
                    use_container_width=True,
                    key=f"combo_sentiment_chart_{idx}"  # Added unique key using combination index
                )
                
                # Add a text summary
                st.write("**Quick Summary:**")
                for topic in topics:
                    sentiment_dist = combo_data['topic_sentiments'][topic]
                    dominant_sentiment = max(
                        ['positive', 'neutral', 'negative'], 
                        key=lambda x: sentiment_dist[x]
                    )
                    st.write(f"• {topic}: Predominantly {dominant_sentiment.upper()} "
                            f"({sentiment_dist[dominant_sentiment]:.1f}%)")

def display_report(file_path: str):
    """Display the report in Streamlit"""
    try:
        # Load the data
        df = pd.read_csv(file_path)
        st.write("Loaded DataFrame columns:", df.columns.tolist())  # Debug info
        
        # Check if we have the minimum required data
        if 'topic' not in df.columns:
            st.error("The selected file doesn't have a 'topic' column which is required for analysis")
            return
            
        # If reflection_id is missing, create it
        if 'reflection_id' not in df.columns:
            df['reflection_id'] = range(1, len(df) + 1)
            
        # If original_reflection is missing, use a placeholder
        if 'original_reflection' not in df.columns:
            df['original_reflection'] = "Reflection text not available"
        
        # Initialize report builder
        report = PipelineReportBuilder(df)
        
        # Display topic statistics
        st.subheader("Topic Statistics")
        st.dataframe(report.get_topic_stats())
        
        # Display topic count statistics
        st.subheader("Topics per Reflection Analysis")
        topic_count_stats = report.get_topic_count_per_reflection()
        st.dataframe(topic_count_stats)
        st.plotly_chart(report.create_topic_count_chart(), 
                       use_container_width=True, 
                       key="topic_count_chart")
        
        # Display common combinations
        st.subheader("Common Topic Combinations")
        combinations_df = report.get_common_topic_combinations()
        if not combinations_df.empty:
            st.dataframe(combinations_df)
            
            # Display combination charts
            st.plotly_chart(report.create_common_combinations_chart(), 
                           use_container_width=True,
                           key="combinations_chart")
            
            # Add sentiment analysis for combinations
            st.subheader("Topic Combination Sentiment Analysis")
            st.write("Expand each combination to see detailed sentiment breakdown for each topic:")
            report.display_combination_sentiment_analysis()
        else:
            st.info("No multi-topic combinations found in the reflections.")
        
        # Add sentiment analysis section with enhanced visibility
        st.markdown("---")
        st.header("Sentiment Analysis")
        
        # Display the quick stats table
        report.create_sentiment_summary_table()
        
        # Create columns for sentiment visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(report.create_sentiment_heatmap(), 
                          use_container_width=True,
                          key="sentiment_heatmap")
            
        with col2:
            st.plotly_chart(report.create_sentiment_stacked_bar(), 
                          use_container_width=True,
                          key="sentiment_stacked_bar")
        
        # Add sentiment insights
        sentiment_stats = report.get_sentiment_stats()
        if not sentiment_stats.empty:
            st.subheader("Sentiment Insights")
            
            # Calculate overall sentiment distribution
            total_pos = sentiment_stats['Pos'].sum()
            total_neu = sentiment_stats['Neu'].sum()
            total_neg = sentiment_stats['Neg'].sum()
            total_all = total_pos + total_neu + total_neg
            
            # Display insights in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Positive Sentiment", 
                         f"{(total_pos/total_all*100):.1f}%",
                         f"{total_pos} responses")
                
            with col2:
                st.metric("Neutral Sentiment", 
                         f"{(total_neu/total_all*100):.1f}%",
                         f"{total_neu} responses")
                
            with col3:
                st.metric("Negative Sentiment", 
                         f"{(total_neg/total_all*100):.1f}%",
                         f"{total_neg} responses")
        
        # Display relationship visualizations
        st.subheader("Topic Relationships")
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(report.create_relationship_graph(), 
                          use_container_width=True,
                          key="relationship_graph")
            
        with col2:
            st.plotly_chart(report.create_heatmap(), 
                          use_container_width=True,
                          key="topic_heatmap")
        
        # Display example reflections for topics
        st.markdown("---")
        st.header("Example Reflections")
        
        # Create tabs for single topics and combinations
        single_tab, combo_tab = st.tabs(["Single Topics", "Topic Combinations"])
        
        with single_tab:
            if 'original_reflection' in df.columns and not df['original_reflection'].equals("Reflection text not available"):
                selected_topic = st.selectbox(
                    "Select a topic to view examples:", 
                    report.topic_frequencies.index,
                    key="single_topic_select"
                )
                
                if selected_topic:
                    examples = df[df['topic'] == selected_topic]['original_reflection'].head(3)
                    for i, example in enumerate(examples, 1):
                        with st.expander(f"Example {i}"):
                            st.write(example)
                            
        with combo_tab:
            # Get combinations with examples
            combo_examples = report.get_combination_examples()
            
            if combo_examples:
                # Create a list of combinations with their counts
                combo_options = [
                    f"{combo} ({len(examples)} examples)" 
                    for combo, examples in combo_examples.items()
                ]
                
                selected_combo = st.selectbox(
                    "Select a topic combination to view examples:",
                    combo_options,
                    key="combo_select"
                )
                
                if selected_combo:
                    # Extract the actual combination from the selection
                    combo = selected_combo.split(" (")[0]
                    examples = combo_examples[combo]
                    
                    # Display examples
                    st.write(f"Showing examples for combination: **{combo}**")
                    for i, example in enumerate(examples, 1):
                        with st.expander(f"Example {i}"):
                            st.write(example)
                            
                    # Add some statistics
                    total_reflections = len(df['reflection_id'].unique())
                    combo_count = len(examples)
                    percentage = (combo_count / total_reflections) * 100
                    
                    st.info(f"This combination appears in {combo_count} reflections "
                           f"({percentage:.1f}% of total reflections)")
            else:
                st.info("No topic combinations with multiple examples found.")
    
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")
