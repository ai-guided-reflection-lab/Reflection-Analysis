"""
Streamlit Components Package
=============================

This package contains individual tab components for the Reflection Analysis application.
Each component is responsible for rendering a specific tab's functionality.

Active Components:
- course_information_tab: Course and reflection data analysis and exploration

Components in development (located in "in progress" subfolder):
- data_cleaning_tab: Raw data processing and validation

Note: Workflow and Analysis components are handled directly in main.py during refactoring.
"""

__version__ = "2.0.0"
__author__ = "Reflection Analysis Tool Team"

# Import available components
from .course_information_tab import render_course_information_tab

__all__ = [
    'render_course_information_tab'
] 