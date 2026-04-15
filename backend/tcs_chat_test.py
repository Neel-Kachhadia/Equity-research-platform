import json
import urllib.request
data = json.dumps({'question': 'What is the revenue and net income of TCS?', 'llm_provider': 'groq', 'company_id': 'TCS', 'history': []}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/chat', data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
print(resp.read().decode('utf-8'))
