from typing import Dict, Optional
from app.data.reflection import Reflection
from app.logic.gpt_api import Model
import json
import os

class GeneratedReflectionResponse:
    """Handles generation of responses to student reflections with grade consideration"""
    
    # Grade thresholds for different status levels
    GRADE_THRESHOLDS = {
        "Good Standing": 80.0,
        "Needs Improvement": 70.0,
        # Below 70 will be "Urgent Attention"
    }
    
    def __init__(self, reflection: Reflection, grade: float, prompt_path: str):
        """
        Initialize the response generator
        
        Args:
            reflection (Reflection): Student's reflection object
            grade (float): Student's current grade
            prompt_path (str): Path to the prompt template file
        """
        if not isinstance(reflection, Reflection):
            raise ValueError("Invalid reflection object provided")
        
        if not isinstance(grade, (int, float)):
            raise ValueError("Grade must be a number")
            
        if not prompt_path or not os.path.exists(prompt_path):
            raise ValueError("Invalid prompt path provided")
            
        self.reflection = reflection
        self.grade = float(grade)
        self.prompt_path = prompt_path
        self.status = self._determine_status()
    
    def _determine_status(self) -> str:
        """Determine student's status based on grade"""
        if self.grade >= self.GRADE_THRESHOLDS["Good Standing"]:
            return "Good Standing"
        elif self.grade >= self.GRADE_THRESHOLDS["Needs Improvement"]:
            return "Needs Improvement"
        return "Urgent Attention"
    
    def _build_context(self) -> Dict:
        """Build context dictionary for response generation"""
        if not self.reflection or not hasattr(self.reflection, 'questions') or not self.reflection.questions:
            raise ValueError("Reflection has no content")
            
        context = {
            "status": self.status,
            "reflection_text": str(self.reflection),
            "num_questions": len(self.reflection.questions)
        }
        
        # Add topic analysis data if available
        if hasattr(self.reflection, 'topic_analysis'):
            context["topic_analysis"] = {
                "main_topic": self.reflection.topic_analysis.get('topic', ''),
                "resolution_status": self.reflection.topic_analysis.get('resolution_status', ''),
                "sentiment": self.reflection.topic_analysis.get('sentiment', ''),
                "key_concerns": self.reflection.topic_analysis.get('key_concerns', [])
            }
        
        # Add missing assignments to context if available
        context["missing_assignments"] = self.reflection.missing_assignments if hasattr(self.reflection, 'missing_assignments') else []
        
        return context
    
    def generate_response(self, model: str = "gpt-4o", temperature: float = 0.7) -> Dict:
        """
        Generate a response based on reflection and grade
        
        Args:
            model (str): GPT model to use
            temperature (float): Temperature for response generation
            
        Returns:
            Dict: Response containing feedback and recommendations
        """
        try:
            # Build context for the prompt
            context = self._build_context()
            
            # Load prompt template
            with open(self.prompt_path, 'r') as f:
                prompt_template = json.load(f)
            
            # Add JSON requirement to the instructions
            instructions = (
                "You must respond with a valid JSON object. "
                "The response should follow this structure:\n"
                "{\n"
                '    "feedback": "string with general feedback",\n'
                '    "recommendations": ["array of specific recommendations"],\n'
                '    "next_steps": "string with immediate actions",\n'
                '    "follow_up_question": "string with a specific follow-up question for the student"\n'
                "}\n\n"
                f"{json.dumps(prompt_template)}"
            )
            
            # Get GPT response
            response = Model.prompt(
                instructions=instructions,
                user_response=json.dumps(context),
                model=model,
                temp=temperature
            )
            
            # Parse response
            if isinstance(response, str):
                response = json.loads(response)
            
            # Add metadata to response after generation
            response.update({
                "student_id": self.reflection.id,
                "grade": self.grade,
                "status": self.status
            })
            
            return response
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return {
                "error": str(e),
                "student_id": self.reflection.id,
                "grade": self.grade,
                "status": self.status
            }
    
    @staticmethod
    def format_response(response: Dict) -> str:
        """Format the response for display"""
        if "error" in response:
            return f"Error generating response: {response['error']}"
        
        formatted = []
        # First add student info and status
        formatted.append(f"Student ID: {response['student_id']}")
        formatted.append(f"Status: {response['status']}")
        formatted.append(f"Current Grade: {response['grade']}%")
        
        # Add missing assignments section if present
        if "missing_assignments" in response and response["missing_assignments"]:
            formatted.append("\n📚 Missing Assignments:")
            for assignment in response["missing_assignments"]:
                formatted.append(f"• {assignment}")
        
        # Add notice after status info
        formatted.append("\n📝 Note to Student:")
        formatted.append("We want to help you succeed in this course! While this feedback is generated to be helpful, "
                        "it may not be perfect. Please respond to the follow-up question below - your instructor will "
                        "read your response and follow up as needed.")
        formatted.append("-" * 50)  # Add separator
        
        if "feedback" in response:
            formatted.append("\n💭 Feedback:")
            formatted.append(response["feedback"])
        
        # Move follow-up question right after feedback
        if "follow_up_question" in response:
            formatted.append("\n❓ Follow-up Question:")
            formatted.append(response["follow_up_question"])
            formatted.append("\nPlease take a moment to respond to this question. "
                            "Your instructor will review your response.")
        
        if "recommendations" in response:
            formatted.append("\n📋 Recommendations:")
            for rec in response["recommendations"]:
                formatted.append(f"• {rec}")
        
        if "next_steps" in response:
            formatted.append("\n👉 Next Steps:")
            formatted.append(response["next_steps"])
        
        return "\n".join(formatted)
