#!/usr/bin/env python3
"""
Main Streamlit Application Entry Point
======================================

This module serves as the primary entry point for the Reflection Analysis application.
It handles only tab routing and basic application setup.

Usage:
    streamlit run application_v2/main.py

Author: Refactored Application v2
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Callable

# Configure Streamlit page settings (must be first Streamlit command)
st.set_page_config(
    page_title="Reflection Analysis Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def initialize_session_state() -> None:
    """Initialize Streamlit session state with default values."""
    default_state = {
        'app_initialized': True,
        'current_course_folder': None,
        'current_reflection_folder': None,
        'reflection_files': None,
        'user_preferences': {},
        'analysis_cache': {}
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header() -> None:
    """Render the main application header."""
    st.title("🔍 Reflection Analysis Tool")
    st.markdown("""
    A comprehensive platform for analyzing student reflections, extracting themes, 
    and generating insights for educational research and course improvement.
    """)
    st.divider()


def get_tab_components() -> Dict[str, Callable]:
    """
    Import and return all tab component functions.
    
    Returns:
        Dictionary mapping tab names to their component functions
    """
    # Show development message for available components
    st.info("🚧 **Partial Development Mode**: Workflow, Analysis, and Course Information tabs available.")
    
    # Import the course information tab
    try:
        from application_v2.view.streamlit_components.course_information_tab import render_course_information_tab
    except ImportError:
        render_course_information_tab = lambda: st.error("Course Information tab not available")
    
    # Return available tabs
    return {
        "🔄 Workflow": lambda: _render_development_message("Workflow"),
        "📊 Analysis": lambda: _render_development_message("Analysis"),
        "📚 Course Information": render_course_information_tab
    }

def _render_development_status() -> None:
    """Render development status message when components are hidden."""
    st.info("🚧 **Application Under Development**: Components are currently being refactored for improved performance and modularity.")
    
    st.markdown("""
    ## 🔄 Refactoring in Progress
    
    The Reflection Analysis Tool is currently undergoing a comprehensive refactoring to improve:
    - **Modularity**: Better separation of concerns
    - **Performance**: Enhanced speed and reliability  
    - **Maintainability**: Cleaner, more organized code
    - **User Experience**: Improved interface and error handling
    
    ### 📁 Current Status
    - ✅ Main application structure completed
    - 🚧 Individual tab components being refactored
    - 📦 Components temporarily moved to "in progress" folder
    - 🎯 Ready for piece-by-piece development
    
    ### 🛠️ Next Steps
    Components will be restored and enhanced as refactoring progresses.
    """)
    
    with st.expander("🔧 Technical Details"):
        st.code("""
Component Location: application_v2/view/streamlit_components/in progress/
├── workflow_tab.py
├── analysis_tab.py  
└── data_cleaning_tab.py

Status: All components preserved and ready for individual refactoring
Architecture: Clean separation between main app and components
        """)


def _render_development_message(tab_name: str) -> None:
    """Render development message for tabs that are being refactored."""
    st.header(f"🚧 {tab_name} - Ready for Development")
    
    st.info(f"""
    **{tab_name} Component - Available for Refactoring**
    
    This component is ready to be refactored from the original implementation.
    """)
    
    # Try to load the original component if available
    try:
        if tab_name == "Workflow":
            st.markdown("### 🔄 Original Workflow Component")
            from application.view.workflow.reflection_workflow import ReflectionWorkflow
            workflow = ReflectionWorkflow()
            workflow.run()
            
        elif tab_name == "Analysis":
            st.markdown("### 📊 Original Analysis Component")
            # Check if prerequisites are met
            course = st.session_state.get('current_course_folder')
            reflection = st.session_state.get('current_reflection_folder')
            
            if not course or not reflection:
                st.warning("⚠️ **Setup Required**: Please select a course and reflection data in the Workflow tab first.")
                if st.button("🚀 Go to Workflow Setup"):
                    st.session_state.active_tab = 0
                    st.rerun()
            else:
                from application.view.analysis_UI.topic_analysis import run_topic_analysis_tab
                run_topic_analysis_tab(is_workflow=False)
                
    except ImportError as e:
        st.error(f"⚠️ Original {tab_name} module not available")
        st.code(f"Import Error: {e}")
        _render_placeholder_content(tab_name)


def _render_placeholder_content(tab_name: str) -> None:
    """Render placeholder content when original modules aren't available."""
    st.markdown(f"""
    **{tab_name} - Refactoring Information:**
    - Original component location preserved
    - Ready for modular refactoring
    - Component file available in "in progress" folder
    
    **Next Steps:**
    - Extract business logic from UI components
    - Create clean interfaces and separation of concerns
    - Implement proper error handling and validation
    """)
    
    with st.expander("🔧 Refactoring Details"):
        component_file = f"{tab_name.lower().replace(' ', '_')}_tab.py"
        st.code(f"""
Component File: application_v2/view/streamlit_components/in progress/{component_file}
Original Module: Available for reference and extraction
Refactoring Status: Ready for development
Architecture: Clean separation between UI and business logic
        """)


def render_sidebar() -> None:
    """Render basic sidebar with navigation shortcuts."""
    with st.sidebar:
        st.header("🚀 Quick Start")
        
        # Application status
        course = st.session_state.get('current_course_folder')
        reflection = st.session_state.get('current_reflection_folder')
        
        if course and reflection:
            st.success("✅ Ready for Analysis")
            st.write(f"**Course:** {course}")
            st.write(f"**Reflection:** {reflection}")
        elif course:
            st.warning("⚠️ Course Selected")
            st.write(f"**Course:** {course}")
            st.write("Please select reflection data")
        else:
            st.error("❌ Setup Required")
            st.write("Please select course and reflection data")
        
        # Navigation shortcuts
        st.header("📋 Navigation")
        if st.button("📁 Go to Workflow", use_container_width=True):
            st.session_state['active_tab'] = 0
            st.rerun()
        
        if st.button("📊 Go to Analysis", use_container_width=True):
            st.session_state['active_tab'] = 1
            st.rerun()
        
        # System information
        st.header("ℹ️ System Info")
        st.info(f"**Project Root:** `{PROJECT_ROOT}`")


def main() -> None:
    """
    Main application entry point.
    
    Handles only:
    - Session state initialization
    - Header rendering
    - Sidebar rendering
    - Tab routing
    """
    try:
        # Initialize application
        initialize_session_state()
        render_header()
        render_sidebar()
        
        # Get tab components
        tab_components = get_tab_components()
        
        if not tab_components:
            st.error("❌ No tab components available. Please check component imports.")
            return
        
        # Create and render tabs
        tab_names = list(tab_components.keys())
        tabs = st.tabs(tab_names)
        
        # Set active tab from session state
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = 0
        
        # Render each tab using its component
        for i, (tab_name, render_func) in enumerate(tab_components.items()):
            with tabs[i]:
                try:
                    render_func()
                except Exception as e:
                    st.error(f"⚠️ Error in {tab_name} tab: {str(e)}")
                    st.code(f"Error details: {type(e).__name__}: {e}")
                    
                    if st.button(f"🔄 Retry {tab_name}", key=f"retry_{i}"):
                        st.rerun()
        
    except Exception as e:
        st.error("🚨 Critical Application Error")
        st.code(f"Unable to initialize application: {str(e)}")
        
        if st.button("🔄 Retry Initialization"):
            st.rerun()


if __name__ == "__main__":
    main() 