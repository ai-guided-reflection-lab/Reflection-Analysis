# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

# Must be the first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="Reflection Analysis System",
    page_icon="📊",
    layout="wide"
)

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from application.model.utilities.json_handler import JSONViewer
from application.view.workflow.reflection_workflow import ReflectionWorkflow
from application.view.analysis_UI.topic_analysis import run_topic_analysis_tab
# Batch GPT analysis removed
# Reflection formatter removed
# Theme extraction removed
from application.view.components.reflection_converter_ui import run_reflection_converter_ui

'''
Main structure of the streamlit app.
'''

def main():
    # Initialize session state if needed
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_course_folder = None
        st.session_state.current_reflection_folder = None
        st.session_state.reflection_files = None
    
    # Create tabs
    tabs = st.tabs(["Workflow", "Analysis", "Summarization", "Data Cleaning"])
    
    with tabs[0]:  # Workflow tab
        workflow = ReflectionWorkflow()
        workflow.run()
        
    with tabs[1]:  # Analysis tab
        st.header("Analysis")
        if st.session_state.current_course_folder and st.session_state.current_reflection_folder:
            run_topic_analysis_tab(is_workflow=False)
        else:
            st.info("Please select a course and reflection in the Workflow tab first.")

    from application.view.analysis_UI.summarization import run_summarization_tab
    with tabs[2]:  # Summarization tab
        st.header("Summarization")
        run_summarization_tab()
        
    with tabs[3]:  # Data Cleaning tab
        run_reflection_converter_ui()
        
    # Settings tab removed (no functionality)

if __name__ == "__main__":
    main() 