import os
from dotenv import load_dotenv
load_dotenv()

from modules.chat.router import _build_context_block
from modules.ingestion.company_loader import load_company
import json
ctx = load_company('Infosys')
ctx_block = _build_context_block(ctx, target_year='2024')
print('=== CONTEXT BLOCK ===\n' + ctx_block)
