import os
from dotenv import load_dotenv
from pathlib import Path

# Find .env file - look in project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
print(f"DEBUG: Looking for .env at: {env_path}")
print(f"DEBUG: .env file exists: {env_path.exists()}")

loaded = load_dotenv(env_path)
print(f"DEBUG: dotenv loaded: {loaded}")

from openai import OpenAI
from application.model.models.reflection import Reflection
import pandas as pd
from application.model.utilities.json_handler import JSONViewer

#from data import reflection

# Lazy client initialization to ensure env vars are loaded
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        # Show first 10 chars to debug format issues
        if api_key:
            print(f"DEBUG: API key starts with: {api_key[:10]}...")
            print(f"DEBUG: API key length: {len(api_key)}")
        else:
            print("DEBUG: OPENAI_API_KEY is NOT SET")
        _client = OpenAI(api_key=api_key)
    return _client


class Model:
    models = ["gpt-4o-mini", "o4-mini-2025-04-16", "gpt-4o", "gpt-3.5-turbo"]

    @staticmethod
    def prompt(instructions, user_response, model=models[0], temp=0.7, max_tokens=500, top_p=1, json=True):
        # Some preview models (e.g. gpt-4o-mini, o4-mini-2025-04-16) expect the parameter name
        # `max_completion_tokens` instead of `max_tokens`.
        token_param_name = "max_tokens"
        if any(key in model for key in ["o4-mini", "gpt-4o-mini"]):
            token_param_name = "max_completion_tokens"

        completion_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"{instructions}"},
                {"role": "user", "content": f"{user_response}"},
            ],
            "response_format": {"type": "json_object"} if json else None,
        }

        # Some preview models accept only default temperature/top_p. Add them only when allowed
        if not any(key in model for key in ["o4-mini", "gpt-4o-mini"]):
            completion_kwargs["temperature"] = temp
            completion_kwargs["top_p"] = top_p

        completion_kwargs[token_param_name] = max_tokens

        response = get_client().chat.completions.create(**completion_kwargs)

        print(response.choices[0].message.content)
        return response.choices[0].message.content


class PromptConfig:
    def __init__(self, path_to_prompt):
        """
        Initializes the PromptConfig instance.

        Parameters:
        - path_to_prompt (str): The file path to the prompt JSON file.
        """
        self.prompt_path = path_to_prompt
        self.refs = None

    '''
    @TODO: Reconfigure this to be part of the reflections module
    '''
    def create_ref_objects(self, ref_path, num_entries=None):
        """
        Creates reflection objects from a CSV file and stores them in the instance.

        Parameters:
        - ref_path (str): The file path to the CSV file containing reflections.
        - num_entries (int, optional): The maximum number of entries to read from the CSV file.
          If not provided, all entries are read.

        Returns:
        - List[Reflection]: A list of Reflection objects created from the CSV rows.
        """
        df = pd.read_csv(ref_path)

        # Limit the number of entries if num_entries is provided
        if num_entries is not None:
            df = df.head(num_entries)  # Take the first num_entries rows

        refs = [Reflection(row) for _, row in df.iterrows()]
        self.refs = refs

        return refs

    def run_prompt_on_individual_refs(self, refs, model="gpt-4o", temp=0.7, max_tokens=500, top_p=1, json=True):
        """
        Runs a prompt on each reflection object and generates outputs.

        Parameters:
        - num_entries (int, optional): The maximum number of entries to process.
          If not provided, all entries in self.refs are processed.
        - model (str, optional): The model to use for generating outputs (default is "gpt-4o").
        - temp (float, optional): The temperature parameter for controlling randomness in output (default is 0.7).
        - max_tokens (int, optional): The maximum number of tokens to generate in the output (default is 500).
        - top_p (float, optional): The top-p sampling parameter (default is 1).
        - json (bool, optional): Whether to return the response in JSON format (default is True).

        Returns:
        - List[str]: A list of outputs generated from the prompts.
        """
        # Check if refs is None
        if refs is None:
            print("No reflection objects found. Please create reference objects first.")
            return  # Exit if no reflection objects

        # Prepare prompt
        prompt = JSONViewer(os.path.join(self.prompt_path)).display_json()
        print(prompt)

        # Generate outputs
        outputs = []
        print("TROUBLESHOOT", refs.__str__())
        for ref in refs:
            try:
                print(ref.id)
                print(ref)
                print("Using this reflection:\n", ref.console_output(), "\n------")
                op = Model.prompt(prompt, ref, model=model, temp=temp, max_tokens=max_tokens, top_p=top_p, json=json)

                outputs.append(op)
            except Exception as e:
                raise RuntimeError(
                    f"Topic analysis request failed after {len(outputs)} of {len(refs)} "
                    f"reflections: {e}"
                ) from e

        print("Sample Outputs")
        for output in outputs:
            print(output)

        return outputs

