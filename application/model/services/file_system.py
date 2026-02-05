import os
import json
import logging
from typing import List, Dict, Any
from application.model.utilities.exceptions import FileSystemError

logger = logging.getLogger(__name__)

class FileSystemService:
    """Handle all file system operations"""
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.ensure_directory(base_path)
        
    def ensure_directory(self, path: str) -> None:
        """Create directory if it doesn't exist"""
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {str(e)}")
            raise FileSystemError(f"Failed to create directory: {str(e)}")
        
    def get_course_directories(self) -> List[str]:
        """Get list of course directories"""
        return [d for d in os.listdir(self.base_path) 
                if os.path.isdir(os.path.join(self.base_path, d))]
                
    def get_reflection_folders(self, course_path: str) -> List[str]:
        """Get list of reflection folders for a course"""
        return sorted([d for d in os.listdir(course_path) 
                      if d.startswith('ref') and os.path.isdir(os.path.join(course_path, d))])
                      
    def get_reflection_files(self, folder_path: str, course_name: str) -> Dict[str, str]:
        """Get reflection and grades files from a folder"""
        files = {}
        for f in os.listdir(folder_path):
            if not f.endswith('.csv'):
                continue
                
            ref_num = os.path.basename(folder_path).replace('ref', '')
            if f == f"{course_name}_ref{ref_num}.csv":
                files['reflection'] = f
            elif f == f"{course_name}_grades_ref{ref_num}.csv":
                files['grades'] = f
                
        return files
        
    def save_csv_file(self, path: str, content: bytes) -> None:
        """Save uploaded CSV file"""
        try:
            with open(path, 'wb') as f:
                f.write(content)
            logger.info(f"Saved CSV file: {path}")
        except Exception as e:
            logger.error(f"Failed to save CSV file {path}: {str(e)}")
            raise FileSystemError(f"Failed to save CSV file: {str(e)}")
            
    def save_json_file(self, path: str, data: Any) -> None:
        """Save JSON data to file"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=4) 