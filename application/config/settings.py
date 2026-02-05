import os
from dataclasses import dataclass, field
from typing import Dict, Set

@dataclass
class Settings:
    """Application settings and constants"""
    # Base paths
    BASE_PATH: str = os.path.join("application", "model", "reflections")
    
    # File patterns
    FILE_PATTERNS: Dict[str, str] = field(default_factory=lambda: {
        'reflection': "{course_name}_ref{ref_num}.csv",
        'grades': "{course_name}_grades_ref{ref_num}.csv"
    })
    
    # Folder patterns
    FOLDER_PATTERN: str = "ref{num}"
    
    # UI Settings
    UI_TITLES: Dict[str, str] = field(default_factory=lambda: {
        'main': "Reflection Analysis System",
        'course': "Course Management",
        'reflection': "Reflection Management"
    })
    
    # CSV Settings
    CSV_SKIP_ROWS: int = 2
    REQUIRED_COLUMNS: Set[str] = field(default_factory=lambda: {'Student', 'SIS Login ID'}) 