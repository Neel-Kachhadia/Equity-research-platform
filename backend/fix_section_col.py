"""Fix DB schema: widen section column from VARCHAR(100) to VARCHAR(500)."""
from dotenv import load_dotenv
load_dotenv(".env")
from core.database import get_cursor

with get_cursor() as cur:
    cur.execute("""
        ALTER TABLE document_chunks
        ALTER COLUMN section TYPE VARCHAR(500)
    """)
    print("Widened section column to VARCHAR(500)")

print("Done")
