class ReflectionAnalysisError(Exception):
    """Base exception for reflection analysis application"""
    pass

class FileSystemError(ReflectionAnalysisError):
    """Raised when file system operations fail"""
    pass

class DataProcessingError(ReflectionAnalysisError):
    """Raised when data processing operations fail"""
    pass

class ValidationError(ReflectionAnalysisError):
    """Raised when data validation fails"""
    pass 