from modules.rag.query import RagRetriever
import logging
logging.basicConfig(level=logging.DEBUG)
r = RagRetriever()
chunks = r._search('Generate a comprehensive analysis of Tata Consultancy Services across all areas based on documents', top_k=5, company_id='TCS', min_similarity=0.0)
print('score for first:', chunks[0]['similarity'] if chunks else 'none')
