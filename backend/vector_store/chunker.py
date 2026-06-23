"""
Knowledge Base Chunker — splits markdown files into semantic chunks.

Strategy:
  1. Split on ## and ### headings (preserving hierarchy)
  2. Keep chunks between 200-800 tokens (~500-2000 chars)
  3. Each chunk stores: text, source file, heading path, category
"""

import os
import re
from typing import List, Dict, Optional


class KnowledgeBaseChunker:
    """Chunks markdown knowledge base files into semantic segments."""

    # Approximate: 1 token ≈ 4 characters for English text
    CHARS_PER_TOKEN = 4
    MIN_CHUNK_CHARS = 800    # ~200 tokens
    MAX_CHUNK_CHARS = 3200   # ~800 tokens
    TARGET_CHUNK_CHARS = 2000  # ~500 tokens

    def __init__(self, kb_root: str):
        self.kb_root = kb_root

    def chunk_all(self) -> List[Dict]:
        """
        Walk the knowledge base and chunk every .md file.
        Returns a list of chunk dicts.
        """
        all_chunks = []
        for dirpath, _, filenames in os.walk(self.kb_root):
            for fname in filenames:
                if not fname.endswith(".md"):
                    continue
                if fname in ("README.md", "INDEX.md"):
                    continue
                filepath = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(filepath, self.kb_root)
                chunks = self.chunk_file(filepath, rel_path)
                all_chunks.extend(chunks)

        # Deduplicate near-identical chunks
        return self._deduplicate(all_chunks)

    def chunk_file(self, filepath: str, rel_path: str = "") -> List[Dict]:
        """Chunk a single markdown file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []

        if not rel_path:
            rel_path = os.path.basename(filepath)

        # Determine category from path (first directory)
        category = rel_path.split(os.sep)[0] if os.sep in rel_path else "general"

        # Split into sections by headings
        sections = self._split_by_headings(content)

        chunks = []
        heading_stack = []  # Track heading hierarchy

        for section in sections:
            level = section.get("level", 0)
            heading = section.get("heading", "")
            text = section.get("text", "").strip()

            if not text:
                continue

            # Update heading stack
            if level <= 1:
                heading_stack = [heading] if heading else []
            elif level == 2:
                heading_stack = heading_stack[:1] + [heading] if heading else heading_stack[:1]
            else:
                heading_stack = heading_stack[:level-1] + [heading] if heading else heading_stack[:level-1]

            heading_path = " > ".join(h for h in heading_stack if h)

            # Split long sections into sub-chunks
            sub_chunks = self._split_long_text(text, heading_path)

            for sc_text, sc_heading in sub_chunks:
                chunks.append({
                    "text": sc_text,
                    "source_file": rel_path,
                    "heading_path": sc_heading or heading_path,
                    "category": category,
                    "char_count": len(sc_text),
                })

        return chunks

    def _split_by_headings(self, text: str) -> List[Dict]:
        """Split markdown text by ## and ### headings."""
        sections = []
        # Find all heading positions
        heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(text))

        if not matches:
            # No headings — treat whole text as one section
            sections.append({"level": 0, "heading": "", "text": text})
            return sections

        # Pre-heading content
        if matches[0].start() > 0:
            pre_text = text[:matches[0].start()].strip()
            if pre_text:
                sections.append({"level": 0, "heading": "", "text": pre_text})

        for i, match in enumerate(matches):
            level = len(match.group(1))  # number of # chars
            heading = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()

            sections.append({
                "level": level,
                "heading": heading,
                "text": section_text,
            })

        return sections

    def _split_long_text(
        self, text: str, heading_path: str
    ) -> List[tuple]:
        """Split long text into target-sized chunks at paragraph boundaries."""
        if len(text) <= self.MAX_CHUNK_CHARS:
            return [(text, heading_path)]

        chunks = []
        paragraphs = re.split(r"\n\n+", text)
        current = ""
        current_heading = heading_path

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if this paragraph looks like a sub-heading
            if re.match(r"^\*\*[\w\s]+\*\*:?\s*$", para) or re.match(r"^[\w\s]+:$", para):
                # Treat as a sub-heading for context
                current_heading = f"{heading_path} | {para.strip('*: ')}"
                if current:
                    chunks.append((current.strip(), current_heading))
                current = para + "\n\n"
                continue

            if len(current) + len(para) > self.MAX_CHUNK_CHARS:
                if current:
                    chunks.append((current.strip(), current_heading))
                # If a single paragraph is too long, split by sentences
                if len(para) > self.MAX_CHUNK_CHARS:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    sent_chunk = ""
                    for sent in sentences:
                        if len(sent_chunk) + len(sent) > self.MAX_CHUNK_CHARS:
                            if sent_chunk:
                                chunks.append((sent_chunk.strip(), current_heading))
                            sent_chunk = sent
                        else:
                            sent_chunk += " " + sent if sent_chunk else sent
                    if sent_chunk:
                        current = sent_chunk + "\n\n"
                    else:
                        current = ""
                else:
                    current = para + "\n\n"
            else:
                current += para + "\n\n"

        if current.strip():
            chunks.append((current.strip(), current_heading))

        return chunks

    def _deduplicate(self, chunks: List[Dict]) -> List[Dict]:
        """Remove near-duplicate chunks (Jaccard similarity > 0.9)."""
        if len(chunks) <= 1:
            return chunks

        # Simple approach: deduplicate by normalized text prefix
        seen = set()
        unique = []
        for chunk in chunks:
            # Use first 100 chars as fingerprint
            fingerprint = re.sub(r"\s+", " ", chunk["text"][:100].lower().strip())
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique.append(chunk)

        return unique
