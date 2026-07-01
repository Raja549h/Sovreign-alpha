import os, glob

base = 'C:/Users/lokes/Downloads/project/sovereign-alpha/'
files = glob.glob(base + '**/*.py', recursive=True)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    if 'from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, logger' in content:
        content = content.replace('from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, logger', 'from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, logger')
        changed = True
    elif 'from config import LLM_API_KEY' in content:
        content = content.replace('from config import LLM_API_KEY', 'from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL')
        changed = True

    if 'from openai import OpenAI' in content:
        content = content.replace('from openai import OpenAI', 'from openai import OpenAI')
        changed = True

    if 'OPENAI_AVAILABLE' in content:
        content = content.replace('OPENAI_AVAILABLE', 'OPENAI_AVAILABLE')
        changed = True

    if 'LLM_API_KEY' in content:
        content = content.replace('LLM_API_KEY', 'LLM_API_KEY')
        changed = True

    if 'self.groq_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)' in content:
        content = content.replace('self.groq_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)', 'self.groq_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)')
        changed = True
    
    if 'client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)' in content:
        content = content.replace('client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)', 'client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)')
        changed = True

    if 'model=LLM_MODEL' in content:
        content = content.replace('model=LLM_MODEL', 'model=LLM_MODEL')
        changed = True
        
    if 'model=\"llama-3.3-70b-versatile\"' in content:
        content = content.replace('model=\"llama-3.3-70b-versatile\"', 'model=LLM_MODEL')
        changed = True

    if changed:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated', file)
