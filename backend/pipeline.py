"""
Three-Step Pipeline — task routing + knowledge retrieval + agent execution.

Step 1: AgentRouter coarse scoring (5-factor weighted)
Step 2: LLM fine-ranking (semantic re-rank of top candidates)
Step 3: Vector search for relevant knowledge base context
Step 4: Assemble augmented context
Step 5: Execute agent with augmented context

Provides both sync prepare (1-2) and async execute (3-5) phases.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional

from shared.models import (
    RouterResult,
    AgentSuggestion,
    ExecuteAgentRequest,
    LLMConfigRequest,
)

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Orchestrates the full routing → retrieval → execution pipeline.

    Usage:
      # Phase 1: Prepare (routing + knowledge retrieval)
      prepare_result = await pipeline.prepare(task_description, llm_config)

      # User reviews and selects an agent

      # Phase 2: Execute
      exec_result = await pipeline.execute(
          project_id, node_id, agent_name, user_instruction,
          llm_config, prepare_result.context_chunks
      )
    """

    def __init__(
        self,
        agent_router,
        vector_db,
        kb_root: str,
    ):
        self.agent_router = agent_router
        self.vector_db = vector_db
        self.kb_root = kb_root
        self._embedding_client = None
        self._embedding_api_key: Optional[str] = None

    # ── Phase 1: Prepare ───────────────────────────────────────────

    async def prepare(
        self,
        text_instruction: str,
        llm_config: Optional[LLMConfigRequest] = None,
        uploaded_files: Optional[List[str]] = None,
        file_contents: Optional[Dict[str, str]] = None,
        max_suggestions: int = 5,
        top_k_chunks: int = 8,
    ) -> Dict[str, Any]:
        """
        Steps 1-2: Route the task and retrieve relevant knowledge.

        Returns:
          - suggestions: ranked agent suggestions
          - knowledge_chunks: relevant KB chunks for context
          - detected_domains: domains detected in the task
          - llm_rerank_info: LLM re-ranking metadata (if applied)
        """
        # Step 1+2: Route (coarse + LLM fine-rank)
        route_result = await self.agent_router.route(
            text_instruction=text_instruction,
            uploaded_files=uploaded_files or [],
            file_contents=file_contents or {},
            llm_config=llm_config,
        )

        # Step 3: Vector search for relevant knowledge
        knowledge_chunks = await self._retrieve_knowledge(
            task_text=text_instruction,
            domains=route_result.detected_domains,
            top_k=top_k_chunks,
            llm_config=llm_config,
        )

        # Build knowledge context summary
        knowledge_summary = self._build_knowledge_summary(knowledge_chunks)

        return {
            "suggestions": [
                {
                    "agent_name": s.agent_name,
                    "domain": s.domain,
                    "confidence": s.confidence,
                    "reason": s.reason,
                    "required_skills": s.required_skills,
                }
                for s in route_result.suggestions[:max_suggestions]
            ],
            "knowledge_chunks": knowledge_chunks,
            "knowledge_summary": knowledge_summary,
            "detected_domains": route_result.detected_domains,
            "parsed_metadata": route_result.parsed_metadata,
            "fan_out_plan": [
                {
                    "sub_task_id": f.sub_task_id,
                    "description": f.description,
                    "agent_name": f.agent_name,
                    "domain": f.domain,
                    "confidence": f.confidence,
                }
                for f in route_result.fan_out_plan
            ],
        }

    # ── Phase 2: Execute ───────────────────────────────────────────

    async def execute(
        self,
        project_id: str,
        node_id: str,
        agent_name: str,
        user_instruction: str,
        llm_config: Optional[LLMConfigRequest] = None,
        knowledge_chunks: Optional[List[Dict[str, Any]]] = None,
        context_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Steps 4-5: Execute the selected agent with augmented context.

        Builds an enriched instruction that includes knowledge base context
        and submits the task to the agent runtime.
        """
        from shared.state import get_service

        # Augment user instruction with knowledge context
        augmented_instruction = self._augment_instruction(
            user_instruction=user_instruction,
            knowledge_chunks=knowledge_chunks or [],
        )

        # Build execution request
        agent_runtime = get_service("agent_runtime")
        if not agent_runtime:
            raise RuntimeError("Agent runtime not available")

        manifest = get_service("manifest")
        if not manifest:
            raise RuntimeError("Manifest not available")

        agent_info = manifest.get_agent(agent_name)
        if not agent_info:
            raise ValueError(f"Agent '{agent_name}' not found")

        from sdk_adapter.yaml_converter import YAMLConverter
        converter = YAMLConverter()
        agent_domain = manifest.get_agent_domain(agent_name)
        workflow_steps = converter.agent_config_to_workflow_steps({
            "name": agent_name,
            "domain": agent_domain,
            "capabilities": manifest.get_agent_capabilities(agent_name),
        })

        req = ExecuteAgentRequest(
            project_id=project_id,
            node_id=node_id,
            agent_name=agent_name,
            context_files=context_files or [],
            user_instruction=augmented_instruction,
            llm_config=llm_config or LLMConfigRequest(),
        )

        agent_runtime.submit_task(req, workflow_steps)

        return {
            "status": "started",
            "node_id": node_id,
            "agent_name": agent_name,
            "steps": len(workflow_steps),
            "augmented_instruction": augmented_instruction[:500],
        }

    # ── Knowledge Retrieval ─────────────────────────────────────────

    async def _retrieve_knowledge(
        self,
        task_text: str,
        domains: List[str],
        top_k: int = 8,
        llm_config: Optional[LLMConfigRequest] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge chunks via vector search (preferred)
        or keyword fallback.
        """
        # Try vector search if embedding client is available
        embedding_client = await self._get_embedding_client(llm_config)

        if embedding_client and self.vector_db:
            try:
                query_emb = await embedding_client.embed_single(task_text[:2000])
                if query_emb:
                    # Search across all categories, then filter
                    results = self.vector_db.search(
                        query_embedding=query_emb,
                        top_k=top_k * 2,
                        min_similarity=0.25,
                    )
                    # Boost results from detected domains
                    for r in results:
                        if r.get("category") in domains:
                            r["similarity"] = min(1.0, r["similarity"] * 1.15)
                    results.sort(key=lambda x: -x["similarity"])
                    return results[:top_k]
            except Exception as e:
                logger.warning(f"Vector search failed, using keyword fallback: {e}")

        # Keyword fallback
        if self.vector_db:
            keywords = self._extract_search_keywords(task_text, domains)
            return self.vector_db.search_by_keywords(
                keywords=keywords,
                top_k=top_k,
            )

        return []

    def _extract_search_keywords(
        self, task_text: str, domains: List[str]
    ) -> List[str]:
        """Extract meaningful keywords from task text for search."""
        import re
        # Extract quoted phrases
        phrases = re.findall(r'"([^"]+)"', task_text)
        # Extract capitalized terms (likely standards, tools, etc.)
        caps = re.findall(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b', task_text)
        # Domain names as keywords
        domain_keywords = [d.replace("-", " ") for d in domains]
        # ISO standards
        standards = re.findall(r'ISO\s+\d+[\w-]*', task_text, re.IGNORECASE)
        # Named entities (capitalized multi-word)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', task_text)

        all_keywords = phrases + caps + domain_keywords + standards + entities
        # Deduplicate
        seen = set()
        unique = []
        for kw in all_keywords:
            kw_lower = kw.lower().strip()
            if kw_lower not in seen and len(kw_lower) > 2:
                seen.add(kw_lower)
                unique.append(kw)

        return unique[:20]

    async def _get_embedding_client(self, llm_config=None):
        """Get or create the embedding client (uses OpenAI by default)."""
        from vector_store.embedding import EmbeddingClient

        # Determine API key for embeddings
        api_key = None
        if llm_config:
            if hasattr(llm_config, "api_key"):
                api_key = llm_config.api_key
            # If using non-OpenAI provider for LLM, still try OpenAI for embeddings
            # but prefer the configured LLM provider if it supports embeddings

        if not api_key:
            return None

        if self._embedding_api_key != api_key:
            try:
                if self._embedding_client:
                    await self._embedding_client.close()
            except Exception:
                pass
            self._embedding_client = EmbeddingClient(api_key=api_key)
            self._embedding_api_key = api_key

        return self._embedding_client

    # ── Context Assembly ────────────────────────────────────────────

    def _build_knowledge_summary(
        self, chunks: List[Dict[str, Any]]
    ) -> str:
        """Build a human-readable summary of retrieved knowledge."""
        if not chunks:
            return "No relevant knowledge base context found."

        lines = ["## Relevant Knowledge Base Context\n"]
        by_category = {}
        for c in chunks:
            cat = c.get("category", "general")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(c)

        for cat, cat_chunks in by_category.items():
            lines.append(f"### {cat.replace('-', ' ').title()}")
            for c in cat_chunks[:3]:
                src = c.get("source_file", "")
                heading = c.get("heading_path", "")
                sim = c.get("similarity", 0)
                lines.append(f"- **{heading or src}** (relevance: {sim:.2f})")
            lines.append("")

        return "\n".join(lines)

    def _augment_instruction(
        self,
        user_instruction: str,
        knowledge_chunks: List[Dict[str, Any]],
    ) -> str:
        """Augment user instruction with knowledge base context."""
        if not knowledge_chunks:
            return user_instruction

        context_parts = []
        total_chars = 0
        max_context_chars = 4000

        for chunk in knowledge_chunks:
            text = chunk.get("chunk_text", "")
            if total_chars + len(text) > max_context_chars:
                # Truncate last chunk
                remaining = max_context_chars - total_chars
                if remaining > 200:
                    context_parts.append(text[:remaining] + "...")
                break
            context_parts.append(text)
            total_chars += len(text)

        context_text = "\n\n---\n\n".join(context_parts)

        return (
            f"## Task\n{user_instruction}\n\n"
            f"## Reference Knowledge (from automotive knowledge base)\n"
            f"{context_text}\n\n"
            f"## Instructions\n"
            f"Use the reference knowledge above to inform your analysis. "
            f"Reference specific standards and practices where applicable."
        )


# ── Prebuild: Embed all knowledge base chunks at startup ────────────

async def prebuild_vector_store(
    kb_root: str,
    db_path: str,
    embedding_api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Prebuild the vector store by chunking all knowledge base files,
    generating embeddings, and storing them in the database.

    Called during app startup (lifespan). Skips if no API key is available
    or if the database already contains chunks.
    """
    if not embedding_api_key:
        logger.info("No embedding API key configured; skipping vector store prebuild.")
        return None

    from vector_store.chunker import KnowledgeBaseChunker
    from vector_store.embedding import EmbeddingClient
    from vector_store.vector_db import VectorDB

    if not os.path.isdir(kb_root):
        logger.warning(f"Knowledge base not found at {kb_root}")
        return None

    # Check if already built
    db = VectorDB(db_path)
    try:
        db.connect()
        stats = db.get_stats()
        if stats["total_chunks"] > 0:
            logger.info(
                f"Vector store already built: {stats['total_chunks']} chunks "
                f"across {len(stats['categories'])} categories"
            )
            db.close()
            return stats
        db.close()
    except Exception:
        pass

    logger.info("Building vector store from knowledge base...")

    try:
        # Step 1: Chunk
        chunker = KnowledgeBaseChunker(kb_root)
        chunks = chunker.chunk_all()
        logger.info(f"  Chunked: {len(chunks)} segments")

        if not chunks:
            return None

        # Step 2: Embed
        client = EmbeddingClient(api_key=embedding_api_key)
        texts = [c["text"] for c in chunks]

        embeddings = await client.embed(texts)
        await client.close()
        logger.info(f"  Embedded: {len(embeddings)} vectors")

        # Step 3: Store
        db = VectorDB(db_path)
        db.connect()
        db.insert(chunks, embeddings)
        stats = db.get_stats()
        db.close()

        logger.info(
            f"Vector store built: {stats['total_chunks']} chunks "
            f"across {len(stats['categories'])} categories"
        )
        return stats

    except Exception as e:
        logger.error(f"Vector store prebuild failed: {e}")
        return None
