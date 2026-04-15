import urllib.request, json
data = json.dumps({'question': 'Generate a comprehensive analysis of Tata Consultancy Services across all areas based on documents', 'llm_provider': 'groq', 'company_id': 'TCS', 'history': []}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/chat', data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
ans = json.loads(resp.read().decode('utf-8')).get('answer', '')
with open('rag_test_results.md', 'w', encoding='utf-8') as f:
    f.write('# Generated RAG Response for TCS\n\n')
    f.write(ans)
print('Done!')
