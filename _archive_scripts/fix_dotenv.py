import os

with open('automation/master_daily.py', 'r') as f:
    content = f.read()

content = content.replace('import psycopg2', 'from dotenv import load_dotenv\nload_dotenv()\nimport psycopg2')

with open('automation/master_daily.py', 'w') as f:
    f.write(content)
