#!/usr/bin/env python3
"""
File Validator for Reflection Analysis System
Ensures that reflection and grade files are correctly placed and contain expected data types.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class FileType(Enum):
    """Enumeration of expected file types"""
    REFLECTION = "reflection"
    GRADES = "grades"
    UNKNOWN = "unknown"
    ERROR = "error"

@dataclass
class ValidationResult:
    """Result of file validation"""
    file_path: str
    expected_type: FileType
    actual_type: FileType
    is_valid: bool
    issues: List[str]
    recommendations: List[str]
    metadata: Dict

class FileValidator:
    """Validates reflection and grade files for correct content and placement"""
    
    def __init__(self):
        self.emotion_keywords = [
            "how do you feel about the course",
            "how do you feel",
            "feel about the course",
            "emotional state",
            "course satisfaction"
        ]
        
        self.reflection_keywords = [
            "reflection",
            "challenge",
            "overcome",
            "experience",
            "learning",
            "feedback",
            "thoughts",
            "what did you learn",
            "biggest challenge"
        ]
        
        self.grade_keywords = [
            "current score",
            "final score",
            "unposted score",
            "assignment",
            "quiz",
            "midterm",
            "final project",
            "extra credit",
            "points possible"
        ]
    
    def validate_file(self, file_path: str, expected_type: FileType) -> ValidationResult:
        """
        Validate a single file to ensure it contains the expected data type.
        
        Args:
            file_path: Path to the file to validate
            expected_type: Expected file type (REFLECTION or GRADES)
            
        Returns:
            ValidationResult object with validation details
        """
        issues = []
        recommendations = []
        metadata = {}
        
        if not os.path.exists(file_path):
            return ValidationResult(
                file_path=file_path,
                expected_type=expected_type,
                actual_type=FileType.ERROR,
                is_valid=False,
                issues=[f"File does not exist: {file_path}"],
                recommendations=["Check file path and ensure file exists"],
                metadata={}
            )
        
        try:
            # Load the file
            df = pd.read_csv(file_path)
            metadata.update({
                'shape': df.shape,
                'columns_count': len(df.columns),
                'rows_count': len(df)
            })
            
            # Check for float columns (potential data corruption)
            float_columns = []
            for col in df.columns:
                if isinstance(col, float):
                    float_columns.append(col)
            
            if float_columns:
                issues.append(f"Found {len(float_columns)} float column names: {float_columns[:3]}{'...' if len(float_columns) > 3 else ''}")
                recommendations.append("Check CSV file for data corruption or malformed headers")
            
            # Analyze column content to determine actual file type
            actual_type = self._determine_file_type(df)
            
            # Check specific content based on expected type
            if expected_type == FileType.REFLECTION:
                self._validate_reflection_file(df, issues, recommendations, metadata)
            elif expected_type == FileType.GRADES:
                self._validate_grades_file(df, issues, recommendations, metadata)
            
            # Check for common issues
            self._check_common_issues(df, issues, recommendations, metadata)
            
            # Determine if file is valid
            is_valid = (actual_type == expected_type and 
                       len([issue for issue in issues if "CRITICAL" in issue]) == 0)
            
            return ValidationResult(
                file_path=file_path,
                expected_type=expected_type,
                actual_type=actual_type,
                is_valid=is_valid,
                issues=issues,
                recommendations=recommendations,
                metadata=metadata
            )
            
        except Exception as e:
            return ValidationResult(
                file_path=file_path,
                expected_type=expected_type,
                actual_type=FileType.ERROR,
                is_valid=False,
                issues=[f"CRITICAL: Error reading file: {str(e)}"],
                recommendations=["Check file format and ensure it's a valid CSV"],
                metadata={}
            )
    
    def _determine_file_type(self, df: pd.DataFrame) -> FileType:
        """Determine the actual file type based on column content"""
        emotion_score = 0
        reflection_score = 0
        grade_score = 0
        
        # Analyze column names
        for col in df.columns:
            if not isinstance(col, str):
                continue
                
            col_lower = col.lower()
            
            # Check for emotion-related columns (strong indicator of reflection data)
            if any(keyword in col_lower for keyword in self.emotion_keywords):
                emotion_score += 5  # Increase weight for emotion columns
            
            # Check for reflection-related columns
            if any(keyword in col_lower for keyword in self.reflection_keywords):
                reflection_score += 2
            
            # Check for grade-related columns (strong indicator of grades data)
            if any(keyword in col_lower for keyword in self.grade_keywords):
                grade_score += 3  # Increase weight for grade columns
            
            # Additional checks for common Canvas gradebook columns
            if any(term in col_lower for term in ['assignment', 'quiz', 'midterm', 'final project', 'extra credit']):
                grade_score += 2
                
            # Check for Canvas-specific gradebook patterns
            if any(pattern in col_lower for pattern in ['unposted', 'sis user id', 'sis login id', 'points possible']):
                grade_score += 2
        
        # Determine type based on scores with clearer thresholds
        if emotion_score >= 5:  # Strong indication of reflection data
            return FileType.REFLECTION
        elif grade_score >= 8:  # Strong indication of grades data
            return FileType.GRADES
        elif reflection_score >= 4 and grade_score < 4:  # Moderate reflection indicators
            return FileType.REFLECTION
        else:
            return FileType.UNKNOWN
    
    def _validate_reflection_file(self, df: pd.DataFrame, issues: List[str], 
                                recommendations: List[str], metadata: Dict):
        """Validate reflection-specific content"""
        
        # Check for emotion column
        emotion_columns = []
        for col in df.columns:
            if isinstance(col, str) and any(keyword in col.lower() for keyword in self.emotion_keywords):
                emotion_columns.append(col)
        
        if not emotion_columns:
            issues.append("CRITICAL: No emotion/feeling columns found in reflection file")
            recommendations.append("Ensure reflection data contains emotion-related questions")
        else:
            metadata['emotion_columns'] = emotion_columns
        
        # Check for student identification
        id_columns = []
        for col in df.columns:
            if isinstance(col, str) and col.lower() in ['id', 'student', 'email', 'user id']:
                id_columns.append(col)
        
        if not id_columns:
            issues.append("WARNING: No clear student identification columns found")
            recommendations.append("Ensure file contains student ID or email columns")
        else:
            metadata['id_columns'] = id_columns
        
        # Check for reflection content
        reflection_columns = []
        for col in df.columns:
            if isinstance(col, str) and any(keyword in col.lower() for keyword in self.reflection_keywords):
                reflection_columns.append(col)
        
        metadata['reflection_columns'] = reflection_columns
        
        if len(reflection_columns) < 2:
            issues.append("WARNING: Limited reflection content columns found")
            recommendations.append("Verify this file contains complete reflection responses")
    
    def _validate_grades_file(self, df: pd.DataFrame, issues: List[str], 
                            recommendations: List[str], metadata: Dict):
        """Validate grades-specific content"""
        
        # Check for grade columns
        grade_columns = []
        for col in df.columns:
            if isinstance(col, str) and any(keyword in col.lower() for keyword in self.grade_keywords):
                grade_columns.append(col)
        
        if not grade_columns:
            issues.append("CRITICAL: No grade-related columns found in grades file")
            recommendations.append("Ensure grades data contains score/assignment columns")
        else:
            metadata['grade_columns'] = grade_columns[:10]  # Limit for display
            metadata['total_grade_columns'] = len(grade_columns)
        
        # Check for student identification
        id_columns = []
        for col in df.columns:
            if isinstance(col, str) and col.lower() in ['id', 'student', 'sis user id', 'sis login id']:
                id_columns.append(col)
        
        if not id_columns:
            issues.append("CRITICAL: No student identification columns found")
            recommendations.append("Ensure grades file contains student ID columns")
        else:
            metadata['id_columns'] = id_columns
        
        # Check if this looks like reflection data in a grades file
        emotion_columns = []
        for col in df.columns:
            if isinstance(col, str) and any(keyword in col.lower() for keyword in self.emotion_keywords):
                emotion_columns.append(col)
        
        if emotion_columns:
            issues.append("CRITICAL: Found emotion/reflection columns in grades file - files may be swapped!")
            recommendations.append("Check if reflection and grades files are correctly named")
    
    def _check_common_issues(self, df: pd.DataFrame, issues: List[str], 
                           recommendations: List[str], metadata: Dict):
        """Check for common data issues"""
        
        # Check for empty file
        if df.empty:
            issues.append("CRITICAL: File is empty")
            recommendations.append("Ensure file contains data")
            return
        
        # Check for very few rows (might indicate header-only file)
        if len(df) <= 2:
            issues.append("WARNING: Very few data rows (may be header-only file)")
            recommendations.append("Verify file contains actual student data")
        
        # Check for suspicious column patterns
        numeric_columns = sum(1 for col in df.columns if isinstance(col, (int, float)))
        if numeric_columns > 5:
            issues.append(f"WARNING: {numeric_columns} numeric column names detected")
            recommendations.append("Check for CSV parsing issues or data corruption")
        
        # Check for test data
        if 'ID' in df.columns:
            test_entries = df[df['ID'].astype(str).str.contains('test', case=False, na=False)]
            if not test_entries.empty:
                metadata['test_entries_count'] = len(test_entries)
                issues.append(f"INFO: Found {len(test_entries)} test entries")
    
    def validate_reflection_directory(self, directory_path: str) -> Dict[str, ValidationResult]:
        """
        Validate all files in a reflection directory.
        
        Args:
            directory_path: Path to the reflection directory (e.g., ref1, ref2)
            
        Returns:
            Dictionary mapping file names to ValidationResult objects
        """
        results = {}
        
        if not os.path.exists(directory_path):
            return results
        
        # Expected file patterns
        dir_name = os.path.basename(directory_path)
        parent_dir = os.path.basename(os.path.dirname(directory_path))
        
        expected_files = {
            f"{parent_dir}_{dir_name}.csv": FileType.REFLECTION,
            f"{parent_dir}_grades_{dir_name}.csv": FileType.GRADES
        }
        
        # Check each expected file
        for filename, expected_type in expected_files.items():
            file_path = os.path.join(directory_path, filename)
            results[filename] = self.validate_file(file_path, expected_type)
        
        # Check for unexpected files
        if os.path.exists(directory_path):
            for filename in os.listdir(directory_path):
                if filename.endswith('.csv') and filename not in expected_files:
                    file_path = os.path.join(directory_path, filename)
                    # Try to determine type automatically
                    temp_result = self.validate_file(file_path, FileType.UNKNOWN)
                    results[f"UNEXPECTED_{filename}"] = temp_result
        
        return results
    
    def generate_validation_report(self, results: Dict[str, ValidationResult]) -> str:
        """Generate a human-readable validation report"""
        
        report = []
        report.append("🔍 FILE VALIDATION REPORT")
        report.append("=" * 60)
        
        valid_files = 0
        total_files = len(results)
        critical_issues = 0
        
        for filename, result in results.items():
            report.append(f"\n📁 {filename}")
            report.append("-" * 40)
            
            # Status
            if result.is_valid:
                report.append("✅ VALID")
                valid_files += 1
            else:
                report.append("❌ INVALID")
            
            # Type information
            report.append(f"Expected: {result.expected_type.value}")
            report.append(f"Actual: {result.actual_type.value}")
            
            # Metadata
            if result.metadata:
                if 'shape' in result.metadata:
                    report.append(f"Shape: {result.metadata['shape']}")
                if 'emotion_columns' in result.metadata:
                    report.append(f"Emotion columns: {len(result.metadata['emotion_columns'])}")
                if 'grade_columns' in result.metadata:
                    report.append(f"Grade columns: {result.metadata.get('total_grade_columns', 0)}")
            
            # Issues
            if result.issues:
                report.append("\n⚠️  Issues:")
                for issue in result.issues:
                    report.append(f"  • {issue}")
                    if "CRITICAL" in issue:
                        critical_issues += 1
            
            # Recommendations
            if result.recommendations:
                report.append("\n💡 Recommendations:")
                for rec in result.recommendations:
                    report.append(f"  • {rec}")
        
        # Summary
        report.append("\n" + "=" * 60)
        report.append("📊 SUMMARY")
        report.append(f"Valid files: {valid_files}/{total_files}")
        report.append(f"Critical issues: {critical_issues}")
        
        if valid_files == total_files and critical_issues == 0:
            report.append("🎉 All files are valid and ready for analysis!")
        elif critical_issues > 0:
            report.append("🔥 Critical issues found - please fix before proceeding")
        else:
            report.append("⚠️  Some issues found - review recommendations")
        
        return "\n".join(report)

# Convenience functions for easy use

def validate_reflection_files(course_name: str, reflection_folder: str) -> str:
    """
    Validate reflection files for a specific course and reflection.
    
    Args:
        course_name: Name of the course (e.g., 'D-ESU5-080')
        reflection_folder: Name of the reflection folder (e.g., 'ref2')
        
    Returns:
        Human-readable validation report
    """
    validator = FileValidator()
    directory_path = os.path.join("application", "model", "reflections", course_name, reflection_folder)
    results = validator.validate_reflection_directory(directory_path)
    return validator.generate_validation_report(results)

def quick_file_check(file_path: str, expected_type: str = "auto") -> bool:
    """
    Quick validation check for a single file.
    
    Args:
        file_path: Path to the file
        expected_type: Expected type ('reflection', 'grades', or 'auto')
        
    Returns:
        True if file is valid, False otherwise
    """
    validator = FileValidator()
    
    if expected_type == "auto":
        # Determine expected type from filename
        filename = os.path.basename(file_path).lower()
        if "grade" in filename:
            expected = FileType.GRADES
        else:
            expected = FileType.REFLECTION
    else:
        expected = FileType.REFLECTION if expected_type == "reflection" else FileType.GRADES
    
    result = validator.validate_file(file_path, expected)
    return result.is_valid 