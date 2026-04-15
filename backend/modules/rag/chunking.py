"""
EREBUS · Semantic Chunking
===========================
Splits financial documents into meaningful chunks for embedding.
Preserves context: financial tables, MD&A sections, risk factors.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """A semantic chunk of text with metadata."""
    text: str
    chunk_id: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0


class SemanticChunker:
    """
    Financial document chunker that respects document structure.
    
    Strategies:
        - Section-aware: Splits on headers (MD&A, Risk Factors, Notes)
        - Table-preserving: Keeps financial tables together
        - Overlap: 10% overlap between chunks for context continuity
    """
    
    # Section header patterns (case-insensitive)
    SECTION_PATTERNS = [
        r"(?i)^(?:#+\s*)?(management'?s?\s+discussion|md&a)",
        r"(?i)^(?:#+\s*)?(risk\s+factors|principal\s+risks)",
        r"(?i)^(?:#+\s*)?(financial\s+statements?|balance\s+sheet|income\s+statement)",
        r"(?i)^(?:#+\s*)?(notes\s+to\s+(?:the\s+)?financial)",
        r"(?i)^(?:#+\s*)?(auditor'?s?\s+report)",
        r"(?i)^(?:#+\s*)?(quarterly\s+results?|earnings\s+release)",
        r"(?i)^(?:#+\s*)?(business\s+overview|company\s+description)",
    ]
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        preserve_sections: bool = True,
        preserve_tables: bool = True,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_sections = preserve_sections
        self.preserve_tables = preserve_tables
    
    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> List[TextChunk]:
        """
        Split document into semantic chunks.
        
        Args:
            text: Document text
            metadata: Document-level metadata (company, year, type)
            doc_id: Unique document identifier
            
        Returns:
            List of TextChunk objects
        """
        metadata = metadata or {}
        
        # Step 1: Detect and extract tables (keep them whole)
        tables = self._extract_tables(text) if self.preserve_tables else []
        text_without_tables = self._mask_tables(text, tables)
        
        # Step 2: Split into sections (if preserve_sections)
        if self.preserve_sections:
            sections = self._split_by_sections(text_without_tables)
        else:
            sections = [{"title": "", "content": text_without_tables}]
        
        # Step 3: Chunk each section
        chunks = []
        chunk_index = 0
        doc_id = doc_id or self._generate_doc_id(metadata)
        
        for section in sections:
            section_chunks = self._chunk_text(
                text=section["content"],
                section_title=section.get("title", ""),
                metadata=metadata,
                doc_id=doc_id,
                start_index=chunk_index,
            )
            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)
        
        # Step 4: Add table chunks (separate chunks for tables)
        for table_idx, table_data in enumerate(tables):
            chunk = TextChunk(
                text=table_data["text"],
                chunk_id=f"{doc_id}_table_{table_idx}",
                chunk_index=chunk_index + table_idx,
                metadata={
                    **metadata,
                    "chunk_type": "table",
                    "section": "financial_table",
                    "table_caption": table_data.get("caption", ""),
                },
                token_count=self._count_tokens(table_data["text"]),
            )
            chunks.append(chunk)
        
        logger.info(f"[Chunking] Created {len(chunks)} chunks from document")
        return chunks
    
    def _split_by_sections(self, text: str) -> List[Dict[str, str]]:
        """Split text by section headers."""
        sections = []
        lines = text.split("\n")
        
        current_title = "Introduction"
        current_content = []
        
        for line in lines:
            # Check if line is a section header
            is_header = False
            for pattern in self.SECTION_PATTERNS:
                if re.match(pattern, line.strip()):
                    # Save previous section
                    if current_content:
                        sections.append({
                            "title": current_title,
                            "content": "\n".join(current_content),
                        })
                    current_title = line.strip()
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Save final section
        if current_content:
            sections.append({
                "title": current_title,
                "content": "\n".join(current_content),
            })
        
        return sections if sections else [{"title": "", "content": text}]
    
    def _chunk_text(
        self,
        text: str,
        section_title: str,
        metadata: Dict[str, Any],
        doc_id: str,
        start_index: int,
    ) -> List[TextChunk]:
        """Chunk text with overlap."""
        words = text.split()
        chunks = []
        
        if not words:
            return chunks
        
        # Use word-based chunking for better semantic boundaries
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunk = TextChunk(
                text=chunk_text,
                chunk_id=f"{doc_id}_chunk_{start_index + len(chunks)}",
                chunk_index=start_index + len(chunks),
                metadata={
                    **metadata,
                    "chunk_type": "text",
                    "section": section_title,
                    "word_count": len(chunk_words),
                    "position": i / len(words) if words else 0,
                },
                token_count=self._count_tokens(chunk_text),
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_tables(self, text: str) -> List[Dict[str, str]]:
        """
        Extract tables from text.
        Handles markdown tables, ASCII tables, and CSV-style data.
        """
        tables = []
        
        # Pattern 1: Markdown tables
        markdown_table_pattern = r"\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+"
        for match in re.finditer(markdown_table_pattern, text, re.MULTILINE):
            tables.append({
                "text": match.group(),
                "caption": self._extract_caption(text, match.start()),
                "type": "markdown",
            })
        
        # Pattern 2: CSV/numeric tables (rows of numbers)
        numeric_table_pattern = r"(?:^|\n)(?:[\d,.\s]+\n){3,}"
        for match in re.finditer(numeric_table_pattern, text, re.MULTILINE):
            tables.append({
                "text": match.group(),
                "caption": self._extract_caption(text, match.start()),
                "type": "numeric",
            })
        
        return tables
    
    def _extract_caption(self, text: str, position: int, context_lines: int = 3) -> str:
        """Extract table caption from surrounding text."""
        lines = text[:position].split("\n")
        context = lines[-context_lines:] if len(lines) >= context_lines else lines
        for line in reversed(context):
            if any(kw in line.lower() for kw in ["table", "exhibit", "figure", "statement"]):
                return line.strip()[:100]
        return ""
    
    def _mask_tables(self, text: str, tables: List[Dict[str, str]]) -> str:
        """Replace tables with placeholder to avoid splitting them."""
        for table in tables:
            text = text.replace(table["text"], f"[TABLE:{len(table['text'])}]")
        return text
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (4 chars ≈ 1 token for English)."""
        return len(text) // 4
    
    def _generate_doc_id(self, metadata: Dict[str, Any]) -> str:
        """Generate unique document ID from metadata."""
        import hashlib
        from datetime import datetime
        
        key = f"{metadata.get('company_id', 'unknown')}_{metadata.get('filename', 'unknown')}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(key.encode()).hexdigest()[:12]


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[TextChunk]:
    """Convenience function for basic chunking."""
    chunker = SemanticChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_document(text, metadata)