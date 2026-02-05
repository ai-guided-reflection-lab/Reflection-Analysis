class ReflectionAnalysisError(Exception):
    """Base exception for reflection analysis application"""
    pass

class FileSystemError(ReflectionAnalysisError):
    """Exception for file system related errors"""
    pass

class DataProcessingError(ReflectionAnalysisError):
    """Raised when data processing operations fail"""
    pass

class ValidationError(ReflectionAnalysisError):
    """Raised when data validation fails"""
    pass 