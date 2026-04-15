"""Fix pgvector column from 1536 → 384 dims for HuggingFace embeddings."""
from dotenv import load_dotenv
load_dotenv(".env")
from core.database import get_cursor

with get_cursor() as cur:
    cur.execute("""
        SELECT atttypmod
        FROM pg_attribute
        WHERE attrelid = 'document_chunks'::regclass
          AND attname = 'embedding'
    """)
    row = cur.fetchone()
    print("Current encoded dim:", row)

    # Drop IVFFlat index (required before altering column type)
    cur.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding_ivfflat")
    print("Dropped IVFFlat index")

    # Alter column
    cur.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(384)")
    print("Altered embedding column to vector(384)")

    # Recreate IVFFlat index for 384-dim cosine
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_ivfflat
        ON document_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10)
    """)
    print("Recreated IVFFlat index")

print("Done — pgvector dimension is now 384")
