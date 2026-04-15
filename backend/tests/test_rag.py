import sys
sys.path.insert(0, 'backend')

from modules.rag.chunking import chunk_page
from modules.rag.parser import clean_text
from modules.rag.vector_store import FAISSDocumentStore
import tempfile

# --- Test 1: chunking ---
fake_page = {
    'doc_id': 'INFY-FY24-AR',
    'company_id': 'INFY',
    'year': 'FY24',
    'page': 1,
    'text': 'A' * 1500
}
chunks = chunk_page(fake_page)
assert len(chunks) == 3, "Expected 3 chunks, got " + str(len(chunks))
assert chunks[0]['chunk_id'] == 'INFY-FY24-AR_p1_0'
assert chunks[0]['company_id'] == 'INFY'
assert chunks[0]['year'] == 'FY24'
assert chunks[0]['page'] == 1
print("chunking.py PASS  - " + str(len(chunks)) + " chunks, schema OK")

# --- Test 2: parser clean_text ---
cleaned = clean_text('  Hello\x00   World\n\n\n\nfoo  ')
assert '\x00' not in cleaned
print("parser.py clean_text PASS - " + repr(cleaned[:30]))

# --- Test 3: vector_store add / search / save / load ---
store = FAISSDocumentStore(dimension=4)
fake_chunks = [
    {
        'chunk_id': 'c1', 'company_id': 'INFY', 'year': 'FY24',
        'doc_id': 'INFY-FY24-AR', 'page': 1, 'chunk_text': 'abc',
        'embedding': [1.0, 0.0, 0.0, 0.0]
    },
    {
        'chunk_id': 'c2', 'company_id': 'INFY', 'year': 'FY24',
        'doc_id': 'INFY-FY24-AR', 'page': 2, 'chunk_text': 'def',
        'embedding': [0.0, 1.0, 0.0, 0.0]
    },
]
added = store.add_documents(fake_chunks)
assert added == 2

results = store.search([1.0, 0.0, 0.0, 0.0], top_k=1)
assert results[0]['chunk_id'] == 'c1'
print("vector_store.py add+search PASS - top: " + results[0]['chunk_id'])

with tempfile.TemporaryDirectory() as tmpdir:
    store.save_index(tmpdir)
    store2 = FAISSDocumentStore(dimension=4)
    store2.load_index(tmpdir)
    assert store2.total_chunks == 2
    results2 = store2.search([1.0, 0.0, 0.0, 0.0], top_k=1)
    assert results2[0]['chunk_id'] == 'c1'
    print("vector_store.py save+load PASS - " + str(store2.total_chunks) + " vectors restored")

print("")
print("ALL RAG SMOKE TESTS PASSED")
