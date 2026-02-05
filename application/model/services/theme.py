from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Theme:
    name: str
    explanation: str
    sentiment: str
    impact: str
    examples: List[str]
    related_topics: List[str]
    relationship_context: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'explanation': self.explanation,
            'sentiment': self.sentiment,
            'impact': self.impact,
            'examples': self.examples,
            'related_topics': self.related_topics,
            'relationship_context': self.relationship_context
        } 