import os
import re

directories = ['c:/Users/lokes/Downloads/project/sovereign-alpha']

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        
        # Specific replacements to preserve DB columns but replace variables
        new_content = new_content.replace('MISTRAL_API_KEY', 'MISTRAL_API_KEY')
        new_content = new_content.replace('MISTRAL_MODEL', 'MISTRAL_MODEL')
        new_content = new_content.replace('MISTRAL_CLASSIFY_PROMPT', 'MISTRAL_CLASSIFY_PROMPT')
        new_content = new_content.replace('MISTRAL_VALIDATION_PROMPT', 'MISTRAL_VALIDATION_PROMPT')
        
        new_content = new_content.replace('mistral_client', 'mistral_client')
        new_content = new_content.replace('mistral_key', 'mistral_key')
        new_content = new_content.replace('_classify_via_mistral', '_classify_via_mistral')
        new_content = new_content.replace('_mistral_web_search', '_mistral_web_search')
        new_content = new_content.replace('mistral_confidence', 'mistral_confidence')
        
        # In thesis_evolution_engine: client = Mistral(api_key=...) -> client = OpenAI(api_key=..., base_url="https://api.mistral.ai/v1")
        new_content = new_content.replace('from openai import OpenAI
            client = OpenAI(api_key=mistral_key, base_url="https://api.mistral.ai/v1")', 'from openai import OpenAI\n            client = OpenAI(api_key=mistral_key, base_url="https://api.mistral.ai/v1")')
        new_content = new_content.replace('from openai import OpenAI
            client = OpenAI(api_key=mistral_key, base_url="https://api.mistral.ai/v1")', 'client = OpenAI(api_key=mistral_key, base_url="https://api.mistral.ai/v1")')
        
        # Replace remaining generic mentions but carefully
        new_content = new_content.replace('mistral-web-search', 'mistral-web-search')
        new_content = new_content.replace('Mistral API', 'Mistral API')
        new_content = new_content.replace('Mistral web search', 'Mistral web search')
        new_content = new_content.replace('Mistral-powered', 'Mistral-powered')
        new_content = new_content.replace('using Mistral', 'using Mistral')
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    except Exception as e:
        pass

for root, _, files in os.walk(directories[0]):
    if '.git' in root or '__pycache__' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith(('.py', '.env', '.example', '.html', '.md', '.json', '.txt')):
            replace_in_file(os.path.join(root, file))
