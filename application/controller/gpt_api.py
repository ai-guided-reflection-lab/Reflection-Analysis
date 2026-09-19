import os
import json as json_lib
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
_clients = {}
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"

def get_client(provider="openai"):
    if provider not in ("openai", "groq"):
        raise ValueError(f"Unsupported AI provider: {provider}")
    key_name = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
    api_key = os.environ.get(key_name, "").strip()
    if not api_key:
        raise ValueError(f"Set {key_name} in the server environment before running analysis.")
    if provider not in _clients:
        base_url = "https://api.groq.com/openai/v1" if provider == "groq" else "https://api.openai.com/v1"
        _clients[provider] = OpenAI(api_key=api_key, base_url=base_url)
    return _clients[provider]


class Model:
    models = ["gpt-4o-mini", "o4-mini-2025-04-16", "gpt-4o", "gpt-3.5-turbo"]

    @staticmethod
    def prompt(instructions, user_response, model=None, temp=0.7, max_tokens=500, top_p=1, json=True, provider="openai", output_schema=None):
        model = model or (os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL) if provider == "groq" else Model.models[0])
        # Some preview models (e.g. gpt-4o-mini, o4-mini-2025-04-16) expect the parameter name
        # `max_completion_tokens` instead of `max_tokens`.
        token_param_name = "max_tokens"
        if provider == "groq" or any(key in model for key in ["o4-mini", "gpt-4o-mini"]):
            token_param_name = "max_completion_tokens"

        if json:
            instructions = f"{instructions}\nReturn only a valid JSON object."
        if output_schema is not None:
            instructions += (
                "\nThe response must match this JSON schema at the top level. "
                "Do not wrap it in fields, output, or another object. "
                "Label arrays must be nonempty with one resolution per primary label. "
                "When no challenge is identified, use the prompt's no-challenge label "
                "(such as 'none'), not an empty array.\n"
                + json_lib.dumps(output_schema)
            )

        completion_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"{instructions}"},
                {"role": "user", "content": f"{user_response}"},
            ],
            "response_format": {"type": "json_object"} if json else None,
        }

        # Some preview models accept only default temperature/top_p. Add them only when allowed
        if provider == "groq" or not any(key in model for key in ["o4-mini", "gpt-4o-mini"]):
            completion_kwargs["temperature"] = temp
            completion_kwargs["top_p"] = top_p

        completion_kwargs[token_param_name] = max_tokens
        if output_schema is not None and provider == "groq" and model in (
            "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"
        ):
            completion_kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "topic_analysis", "strict": True, "schema": output_schema},
            }
        if provider == "groq" and model.startswith("openai/gpt-oss-"):
            completion_kwargs["reasoning_effort"] = "low"

        response = get_client(provider).chat.completions.create(**completion_kwargs)
        if response.choices[0].finish_reason == "length":
            raise ValueError("The model response exceeded the output token limit. Use a shorter prompt or another model.")
        if not response.choices[0].message.content:
            raise ValueError("The model returned an empty response. Please retry or select another model.")

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

    def run_prompt_on_individual_refs(self, refs, model=None, temp=0.7, max_tokens=500, top_p=1, json=True, provider="openai", output_schema=None, output_validator=None):
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
        # Preserve the arrays and objects in the prompt's output example.
        prompt = json_lib.dumps(JSONViewer(self.prompt_path).json_data, indent=2)
        print(prompt)

        # Generate outputs
        outputs = []
        print("TROUBLESHOOT", refs.__str__())
        for ref in refs:
            try:
                print(ref.id)
                print(ref)
                print("Using this reflection:\n", ref.console_output(), "\n------")
                request_prompt = prompt
                for attempt in range(2):
                    op = Model.prompt(request_prompt, ref, model=model or ("gpt-4o" if provider == "openai" else None), temp=temp, max_tokens=max_tokens, top_p=top_p, json=json, provider=provider, output_schema=output_schema)
                    if output_validator is None:
                        break
                    try:
                        output_validator(op)
                        break
                    except ValueError as validation_error:
                        if attempt == 1:
                            raise ValueError(
                                f"Invalid topic output after one retry: {validation_error}"
                            ) from validation_error
                        request_prompt = prompt + (
                            f"\nYour previous response failed validation: {validation_error} "
                            "Generate a new annotation for the same reflection using the required schema."
                        )

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
