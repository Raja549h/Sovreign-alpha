import os
import re

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    content = content.replace('import sqlite3, json', 'import json')
    content = content.replace('import sqlite3', '')
    content = content.replace('sqlite3.Connection', 'any')
    if orig != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

clean_file(r'billing\meter.py')
clean_file(r'dashboard\app.py')
clean_file(r'dashboard\schemas.py')
clean_file(r'backtesting\backtest_90day.py')
clean_file(r'backtesting\reanalyze_buy_metrics.py')

print("Cleanup done.")
