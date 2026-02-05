from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TopicClassification:
    name: str
    topic_explanation: str
    selection_explanation: str
    confidence_score: float
    evidence: str
    sentiment_match: bool
    sentiment_explanation: str

@dataclass
class ClassificationResult:
    reflection_id: int
    original_reflection: str
    topics: List[TopicClassification]
    topic_interactions: dict
    unique_aspects: str
    classification_summary: str

    def to_dataframe_rows(self) -> List[dict]:
        """Convert the classification result to a list of dictionary rows for DataFrame creation"""
        rows = []
        for topic in self.topics:
            rows.append({
                'reflection_id': self.reflection_id,
                'original_reflection': self.original_reflection,
                'topic': topic.name,
                'topic_explanation': topic.topic_explanation,
                'selection_explanation': topic.selection_explanation,
                # ... other fields ...
            })
        return rows 