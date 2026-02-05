# Controller Layer

The controller layer handles external API integrations, data validation, and utility functions for the Reflection Analysis System.

## Components

### `gpt_api.py` ✅ **ACTIVELY USED**
**Status**: Core functionality for topic analysis
**Purpose**: Handles OpenAI GPT API integration for:
- Topic classification of student reflections
- Batch processing of reflection data
- Prompt management and configuration

**Used by**:
- `application/model/services/topic_classification.py`
- `application/model/services/data_processing.py`

**Key Classes**:
- `Model`: Handles GPT API calls with proper parameter handling
- `PromptConfig`: Manages prompt templates and batch processing

### `utilities/` ✅ **ACTIVELY USED**
**Status**: Essential utilities for data processing and validation

**Files**:
- **`file_validator.py`**: CSV file validation and integrity checking
- **`id_column_fixer.py`**: Fixes ID column inconsistencies in data files
- **`reflection_converter.py`**: Converts various reflection file formats to standardized DataFrames
- **`output_compiler.py`**: Handles label counting and output compilation

**Used by**: Multiple view components and data processing services

### `grr/` ⚠️ **READY FOR FUTURE USE**
**Status**: Fully implemented but currently unused
**Purpose**: Generated Reflection Response system for automated student feedback

**Components**:
- **`response.py`**: Core response generation logic
- **`response_prompt.json`**: Response template configuration
- **`README.md`**: Detailed documentation of the system

**Future Potential**: Student dashboard feedback, automated follow-ups, instructor response suggestions

## Architecture Notes

- **Active Components**: `gpt_api.py` and `utilities/` are essential for current instructor mode functionality
- **Future Components**: `grr/` system is ready for integration when automated response features are needed
- **Dependencies**: All components use standard Python libraries and OpenAI API
- **Error Handling**: Comprehensive error handling and logging throughout

## Usage Guidelines

1. **For Current Functionality**: Use `gpt_api.py` and `utilities/` as normal
2. **For Future Features**: The `grr/` system is ready for integration
3. **For Development**: All components follow consistent error handling and logging patterns
4. **For Deployment**: Ensure OpenAI API keys are properly configured for GPT functionality
