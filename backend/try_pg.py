import os
from dotenv import load_dotenv
load_dotenv()
from modules.rag.vector_store import get_vector_store
store = get_vector_store()
print('Total chunks in PGVector:', store.count())
print('TCS chunks in PGVector:', store.count('TCS'))
