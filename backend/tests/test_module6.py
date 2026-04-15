import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from modules.llm.prompt_builder import build_synthesis_prompt, SYSTEM_PROMPT
from modules.llm.generator import LLMGenerator
from modules.rag.query import RagRetriever

def test_prompt_builder():
    quant_context = {
        'summary': {'cas': 65, 'cas_label': 'STRONG_POSITIVE', 'dci_pct': 85.0, 'confidence_band': 'HIGH'},
        'qsd_result': {'divergence_flag': True, 'divergence_note': 'QSD indicates narrative lag.'}
    }
    
    retriever = RagRetriever()
    chunks = retriever.retrieve_top_k("What is the outlook?", top_k=2, company_filter="INFY")
    
    prompt = build_synthesis_prompt("Analyze the outlook for INFY.", quant_context, chunks, "deep")
    
    assert "Composite Alpha Score (CAS): 65" in prompt
    assert "WARNING: Quant-Sentiment Divergence Detected" in prompt
    assert "INFY-FY24-AR" in prompt
    assert "Analyze the outlook for INFY." in prompt
    assert "NO PRICE TARGETS" in SYSTEM_PROMPT
    assert "NO RECOMMENDATIONS" in SYSTEM_PROMPT

    print("Test passed: prompt_builder successfully structures quant and rag context.")

if __name__ == "__main__":
    test_prompt_builder()
