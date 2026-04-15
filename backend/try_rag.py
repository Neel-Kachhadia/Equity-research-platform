import os
from dotenv import load_dotenv
load_dotenv()
from modules.rag.query import RagRetriever
import logging
logging.basicConfig(level=logging.DEBUG)
r = RagRetriever()
chunks = r.retrieve('Analyze TCS', top_k=5, company_id='TCS', min_similarity=0.10)
print('Retrieved chunks count:', len(chunks))
if chunks:
    print('First chunk:', chunks[0]['text'][:100])
