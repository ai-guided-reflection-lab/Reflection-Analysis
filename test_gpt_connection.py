#!/usr/bin/env python3
"""
Test script to troubleshoot GPT API connection errors.
This script tests the same functionality as the main application but with enhanced debugging.
"""

import os
import sys
import time
import traceback
from openai import OpenAI
import pandas as pd

# Add the application directory to the path so we can import modules
sys.path.append('/Users/nicolewiktor/Desktop/Research/2025/ADAEdu')

try:
    from application.model.models.reflection import Reflection
    from application.model.utilities.json_handler import JSONViewer
    print("✅ Successfully imported application modules")
except ImportError as e:
    print(f"❌ Failed to import application modules: {e}")
    print("This test will continue with basic OpenAI testing only")

def test_environment_setup():
    """Test if the environment is properly configured"""
    print("\n" + "="*50)
    print("TESTING ENVIRONMENT SETUP")
    print("="*50)
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OpenAI API key found: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else 'short_key'}")
    else:
        print("❌ OpenAI API key not found in environment variables")
        print("Please set OPENAI_API_KEY environment variable")
        return False
    
    # Test OpenAI client initialization
    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized successfully")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        return False

def test_basic_api_connection(client):
    """Test basic API connection with a simple prompt"""
    print("\n" + "="*50)
    print("TESTING BASIC API CONNECTION")
    print("="*50)
    
    try:
        print("Making basic API call...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in JSON format."}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=100,
            temperature=0.7
        )
        
        print("✅ Basic API call successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Basic API call failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_model_class_functionality(client):
    """Test the Model class functionality from the original script"""
    print("\n" + "="*50)
    print("TESTING MODEL CLASS FUNCTIONALITY")
    print("="*50)
    
    class TestModel:
        models = ["gpt-4o-mini", "o4-mini-2025-04-16", "gpt-4o", "gpt-3.5-turbo"]

        @staticmethod
        def prompt(instructions, user_response, model="gpt-4o-mini", temp=0.7, max_tokens=500, top_p=1, json=True):
            print(f"Testing with model: {model}")
            print(f"Instructions length: {len(instructions)}")
            print(f"User response type: {type(user_response)}")
            print(f"User response preview: {str(user_response)[:200]}...")
            
            # Some preview models expect different parameter names
            token_param_name = "max_tokens"
            if any(key in model for key in ["o4-mini", "gpt-4o-mini"]):
                token_param_name = "max_completion_tokens"
                print(f"Using {token_param_name} for model {model}")

            completion_kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": f"{instructions}"},
                    {"role": "user", "content": f"{user_response}"},
                ],
                "response_format": {"type": "json_object"} if json else None,
            }

            # Some preview models accept only default temperature/top_p
            if not any(key in model for key in ["o4-mini", "gpt-4o-mini"]):
                completion_kwargs["temperature"] = temp
                completion_kwargs["top_p"] = top_p
                print(f"Added temperature: {temp}, top_p: {top_p}")

            completion_kwargs[token_param_name] = max_tokens
            
            print("Making API call with parameters:")
            print(f"  Model: {completion_kwargs['model']}")
            print(f"  Messages: {len(completion_kwargs['messages'])} messages")
            print(f"  Response format: {completion_kwargs.get('response_format')}")
            print(f"  {token_param_name}: {completion_kwargs[token_param_name]}")
            
            try:
                response = client.chat.completions.create(**completion_kwargs)
                print("✅ Model class API call successful!")
                result = response.choices[0].message.content
                print(f"Response preview: {result[:200]}...")
                return result
                
            except Exception as e:
                print(f"❌ Model class API call failed: {e}")
                print(f"Error type: {type(e).__name__}")
                print(f"Traceback: {traceback.format_exc()}")
                raise
    
    # Test with simple data
    try:
        test_instructions = "You are a helpful assistant. Respond in JSON format with a 'test' field."
        test_user_input = "This is a test message"
        
        result = TestModel.prompt(test_instructions, test_user_input)
        return True
        
    except Exception as e:
        print(f"❌ Model class test failed: {e}")
        return False

def create_sample_reflection():
    """Create a sample reflection object for testing"""
    print("\n" + "="*50)
    print("CREATING SAMPLE REFLECTION DATA")
    print("="*50)
    
    # Create sample data that mimics what would come from a CSV
    sample_data = {
        'ID': 'testuser@example.com',
        'StartDate': '2025-01-01',
        'reflection_number': 1,
        'Q1': 'What challenges did you face this week?',
        'A1': 'I had difficulty understanding the API concepts and implementing them in my project. The documentation was confusing.',
        'Q2': 'How did you overcome these challenges?',
        'A2': 'I watched some YouTube videos and asked for help from my classmates.',
        'grade_assignment1': 85,
        'grade_quiz1': 92
    }
    
    try:
        reflection = Reflection(sample_data)
        print(f"✅ Sample reflection created successfully")
        print(f"Reflection ID: {reflection.id}")
        print(f"Number of questions: {len(reflection.questions)}")
        print(f"Console output preview:")
        print(reflection.console_output()[:300] + "..." if len(reflection.console_output()) > 300 else reflection.console_output())
        return reflection
        
    except Exception as e:
        print(f"❌ Failed to create sample reflection: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

def test_with_sample_reflection(client, reflection):
    """Test the full workflow with a sample reflection"""
    print("\n" + "="*50)
    print("TESTING WITH SAMPLE REFLECTION DATA")
    print("="*50)
    
    if not reflection:
        print("❌ No reflection data available for testing")
        return False
    
    # Load the actual prompt from the application
    try:
        prompt_path = "/Users/nicolewiktor/Desktop/Research/2025/ADAEdu/application/model/prompts/topic_analysis.json"
        prompt = JSONViewer(prompt_path).display_json()
        print(f"✅ Loaded prompt from {prompt_path}")
        print(f"Prompt length: {len(prompt)} characters")
        
    except Exception as e:
        print(f"❌ Failed to load prompt: {e}")
        # Use a simple test prompt instead
        prompt = """You are a helpful assistant. Analyze the following student reflection and respond in JSON format with:
        {
            "primary_labels_selected": ["python_and_coding"],
            "resolution_primary_labels": ["unresolved"],
            "urgency": "medium",
            "reflection_summary": "Student is having difficulty with API concepts.",
            "instructor_suggestions": "Consider providing additional API examples."
        }"""
        print("Using fallback test prompt")
    
    # Test the API call with the reflection data
    try:
        print("Making API call with reflection data...")
        print(f"Reflection data being sent: {str(reflection)[:200]}...")
        
        # Use the same Model class logic
        token_param_name = "max_completion_tokens"  # for gpt-4o-mini
        model = "gpt-4o-mini"
        
        completion_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": str(reflection)},
            ],
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 500,
        }
        
        response = client.chat.completions.create(**completion_kwargs)
        result = response.choices[0].message.content
        
        print("✅ Full workflow test successful!")
        print(f"Analysis result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Additional debugging for connection errors
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            print("\n🔍 CONNECTION ERROR DEBUGGING:")
            print("1. Check your internet connection")
            print("2. Verify OpenAI API status: https://status.openai.com/")
            print("3. Check if your API key has sufficient credits")
            print("4. Try with a different model (gpt-3.5-turbo)")
            
        return False

def test_network_connectivity():
    """Test basic network connectivity"""
    print("\n" + "="*50)
    print("TESTING NETWORK CONNECTIVITY")
    print("="*50)
    
    import socket
    import urllib.request
    
    # Test basic internet connectivity
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("✅ Basic internet connectivity: OK")
    except OSError:
        print("❌ Basic internet connectivity: FAILED")
        return False
    
    # Test OpenAI API endpoint accessibility
    try:
        response = urllib.request.urlopen("https://api.openai.com", timeout=10)
        print("✅ OpenAI API endpoint accessible")
        return True
    except Exception as e:
        print(f"❌ OpenAI API endpoint not accessible: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 GPT API CONNECTION TROUBLESHOOTING SCRIPT")
    print("This script will test various aspects of the GPT API connection")
    print("to help identify the source of connection errors.\n")
    
    # Test 1: Environment setup
    client = test_environment_setup()
    if not client:
        print("\n❌ Environment setup failed. Cannot continue with API tests.")
        return
    
    # Test 2: Network connectivity
    if not test_network_connectivity():
        print("\n❌ Network connectivity issues detected.")
        return
    
    # Test 3: Basic API connection
    if not test_basic_api_connection(client):
        print("\n❌ Basic API connection failed. Check your API key and OpenAI service status.")
        return
    
    # Test 4: Model class functionality
    if not test_model_class_functionality(client):
        print("\n❌ Model class functionality test failed.")
        return
    
    # Test 5: Sample reflection creation and testing
    try:
        reflection = create_sample_reflection()
        if reflection:
            if test_with_sample_reflection(client, reflection):
                print("\n✅ All tests passed! The GPT API connection is working correctly.")
                print("The issue might be with specific data or timing in your main application.")
            else:
                print("\n❌ Full workflow test failed. Check the detailed error messages above.")
        else:
            print("\n⚠️  Could not create sample reflection, but basic API tests passed.")
    except Exception as e:
        print(f"\n❌ Error during reflection testing: {e}")
    
    print("\n" + "="*50)
    print("TROUBLESHOOTING SUMMARY")
    print("="*50)
    print("If basic tests pass but your main application fails:")
    print("1. Check the specific data being sent to the API")
    print("2. Verify the reflection data format and content")
    print("3. Check for any rate limiting issues")
    print("4. Ensure the prompt file is accessible and valid")
    print("5. Look for any network timeouts during batch processing")

if __name__ == "__main__":
    main()
