# Generated Reflection Response (GRR) System

## Overview
The GRR system is designed to automatically generate personalized responses to student reflections based on their content and current academic standing. This system analyzes student reflections and generates appropriate feedback, recommendations, and follow-up questions.

## Current Status
**⚠️ This functionality is currently unused in the application but is fully implemented and ready for future integration.**

## Features
- **Grade-Based Status Assessment**: Automatically categorizes students into:
  - Good Standing (≥80%)
  - Needs Improvement (70-79%)
  - Urgent Attention (<70%)

- **Contextual Response Generation**: Creates responses based on:
  - Student's reflection content
  - Current academic performance
  - Topic analysis results (if available)
  - Missing assignments

- **Structured Output**: Generates JSON responses with:
  - Personalized feedback
  - Specific recommendations
  - Next steps for improvement
  - Follow-up questions

## Components

### `response.py`
Contains the `GeneratedReflectionResponse` class that:
- Analyzes student reflections and grades
- Determines academic status
- Builds context for response generation
- Generates personalized feedback using GPT models

### `response_prompt.json`
Template file containing the prompt structure for generating responses. The prompt guides the AI to create:
- Contextual feedback based on grade and reflection content
- Actionable recommendations
- Specific next steps
- Engaging follow-up questions

## How It Works
1. **Input**: Student reflection object + current grade + prompt template
2. **Analysis**: System determines student's academic status
3. **Context Building**: Creates comprehensive context including:
   - Reflection content
   - Topic analysis results
   - Missing assignments
   - Academic standing
4. **Response Generation**: Uses GPT to create personalized feedback
5. **Output**: Structured JSON response ready for student consumption

## Future Integration Points
This system could be integrated into:
- **Student Dashboard**: Show personalized feedback after reflection submission
- **Instructor Tools**: Generate response suggestions for manual review
- **Automated Follow-up**: Send scheduled check-ins based on reflection analysis
- **Progress Tracking**: Monitor student improvement over time

## Technical Requirements
- OpenAI API access
- Student reflection data
- Grade information
- Topic analysis results (optional)

## Example Usage
```python
from application.controller.grr.response import GeneratedReflectionResponse

# Create response generator
response_gen = GeneratedReflectionResponse(
    reflection=student_reflection,
    grade=85.5,
    prompt_path="path/to/prompt.json"
)

# Generate personalized response
response = response_gen.generate_response(
    model="gpt-4o",
    temperature=0.7
)
```

## Notes
- Currently not imported or used by any active application components
- All functionality is implemented and tested
- Ready for integration when the feature is needed
- Can be easily extended with additional response types or analysis features
