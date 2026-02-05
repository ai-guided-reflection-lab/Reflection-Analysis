import streamlit as st
import os
from typing import Optional
from application.config.settings import Settings
from application.model.services.file_system import FileSystemService
from application.model.services.data_processing import DataProcessingService
from application.model.services.state_management import StateManager
from application.view.components.course_view import CourseView
from application.view.components.reflection_view import ReflectionView

class ReflectionWorkflow:
    """Main workflow controller for the reflection analysis application"""
    def __init__(self):
        # Initialize services
        self.settings = Settings()
        self.fs_service = FileSystemService(self.settings.BASE_PATH)
        self.data_processor = DataProcessingService()
        self.state_manager = StateManager()
        
        # Initialize UI components
        self.course_view = CourseView(
            self.fs_service,
            self.data_processor,
            self.state_manager
        )
        self.reflection_view = ReflectionView(
            self.fs_service,
            self.data_processor,
            self.state_manager
        )
        
    def run(self):
        """Run the main workflow"""
        st.title(self.settings.UI_TITLES['main'])
        
        # Add comprehensive usage instructions
        self.show_usage_instructions()
        
        # Course Management Section
        st.header(self.settings.UI_TITLES['course'])
        current_course = self.handle_course_section()
        
        # Reflection Management Section
        if current_course:
            st.header(self.settings.UI_TITLES['reflection'])
            self.handle_reflection_section(current_course)
            
    def handle_course_section(self) -> Optional[str]:
        """Handle the course management section"""
        return self.course_view.show_course_selection()
        
    def handle_reflection_section(self, course_name: str) -> None:
        """Handle the reflection management section"""
        self.reflection_view.show_reflection_selection(course_name)
        
    def show_usage_instructions(self):
        """Display comprehensive usage instructions for the application"""
        with st.expander("📚 How to Use This Application", expanded=True):
            st.markdown("""
            ## 🚀 Getting Started Guide
            
            This **Reflection Analysis System** helps instructors analyze student reflection data and generate insights. 
            Follow these steps to get started:
            """)
            
            # Step-by-step instructions
            st.markdown("""
            ### 📋 Step-by-Step Instructions
            
            **1. Select a Course** 📚
            - Choose a course from the dropdown menu below
            - If no courses appear, you may need to add course data to the system
            - Each course should have its own folder in the reflections directory
            
            **2. Choose Reflection Period** 📅
            - After selecting a course, choose a reflection period (e.g., Reflection 1, Reflection 2)
            - The system will load the corresponding reflection and grade data
            - Make sure both reflection and grade files exist for the selected period
            
            **3. Navigate to Analysis Tab** 📊
            - Once a course and reflection are selected, go to the **Analysis** tab
            - The system will automatically load and analyze the selected data
            - View topic analysis results and student insights
            
            **4. Use Data Cleaning Tools** 🧹
            - If you need to process or convert reflection data, use the **Data Cleaning** tab
            - Convert between different reflection formats
            - Clean and prepare data for analysis
            """)
            
            # Data requirements
            st.markdown("""
            ### 📁 Data Requirements
            
            **Course Structure:**
            ```
            application/model/reflections/
            ├── COURSE_NAME_1/
            │   ├── ref1/
            │   │   ├── COURSE_NAME_1_ref1.csv          # Student reflections
            │   │   ├── COURSE_NAME_1_grades_ref1.csv   # Student grades
            │   │   └── results/                        # Analysis results
            │   ├── ref2/
            │   └── ref3/
            └── COURSE_NAME_2/
                ├── ref1/
                └── ref2/
            ```
            
            **Required File Formats:**
            - **Reflection CSV:** Must contain student reflection text and identifiers
            - **Grades CSV:** Must contain student grades and identifiers
            - **File Naming:** Follow the pattern `{course_name}_ref{number}.csv`
            """)
            
            # Features overview
            st.markdown("""
            ### 🎯 Available Features
            
            **📊 Analysis Tab:**
            - **Topic Analysis:** Identify key themes in student reflections
            - **Student Profiles:** Individual student insights and progress tracking
            - **Class Aggregates:** Overall class performance and trends
            
            **🧹 Data Cleaning Tab:**
            - **Reflection Converter:** Convert between different reflection formats
            - **Data Validation:** Check data integrity and completeness
            - **Format Standardization:** Ensure consistent data structure
            
            **📈 Reports:**
            - **HTML Reports:** Download comprehensive analysis reports
            - **Anonymized Options:** Generate reports with student privacy protection
            - **Customizable Views:** Focus on specific aspects of the data
            """)
            
            # Tips and best practices
            st.markdown("""
            ### 💡 Tips for Best Results
            
            **Data Quality:**
            - Ensure reflection files contain meaningful text content
            - Verify that student identifiers match between reflection and grade files
            - Check for missing or corrupted data before analysis
            
            **Analysis Workflow:**
            - Start with the Workflow tab to set up your data
            - Use the Analysis tab for insights and reports
            - Export results for sharing or further analysis
            - Use anonymized reports when sharing with stakeholders
            
            **Troubleshooting:**
            - If no data appears, check file paths and naming conventions
            - Ensure CSV files are properly formatted and encoded
            - Verify that course and reflection folders exist
            """)
            
            # Quick actions
            st.markdown("""
            ### ⚡ Quick Actions
            
            **Ready to Start?**
            - Select a course from the dropdown below
            - Choose a reflection period
            - Navigate to the Analysis tab to view results
            
            **Need Help?**
            - Check the data requirements above
            - Verify your file structure matches the expected format
            - Ensure all required files are present and accessible
            """)
            
            st.success("🎉 **Ready to analyze your reflection data!** Start by selecting a course below.") 