import urllib.request
import json
import sys

url = "https://api.github.com/repos/Raja549h/Sovreign-alpha/actions/runs?per_page=1"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    if data['workflow_runs']:
        run = data['workflow_runs'][0]
        print(f"Status: {run['status']}, Conclusion: {run['conclusion']}, URL: {run['html_url']}")
    else:
        print("No workflow runs found.")
except Exception as e:
    print(f"Error: {e}")
