import streamlit as st
from typing import Dict, Any, Optional

class StateManager:
    """Manage Streamlit session state"""
    @staticmethod
    def set_course(course_name: str) -> None:
        st.session_state.current_course_folder = course_name
        
    @staticmethod
    def set_reflection(folder: str, files: Dict[str, str]) -> None:
        st.session_state.current_reflection_folder = folder
        st.session_state.reflection_files = files
        
    @staticmethod
    def get_current_state() -> Dict[str, Any]:
        return {
            'course': st.session_state.get('current_course_folder'),
            'reflection_folder': st.session_state.get('current_reflection_folder'),
            'reflection_files': st.session_state.get('reflection_files')
        }
        
    @staticmethod
    def clear_reflection_state() -> None:
        if 'current_reflection_folder' in st.session_state:
            del st.session_state.current_reflection_folder
        if 'reflection_files' in st.session_state:
            del st.session_state.reflection_files 