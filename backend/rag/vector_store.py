"""
ChromaDB Persistent Vector Store Subsystem for Retrieval Lens
Indexes relevant post embeddings for semantic vector search & RAG retrieval.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Persistent ChromaDB client for post indexing and similarity retrieval."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.chroma_dir = os.path.join(data_dir, "chroma_db")
        
        mapped_path = os.path.join(data_dir, "final_tagged_dataset_mapped.json")
        final_path = os.path.join(data_dir, "final_tagged_dataset.json")
        if os.path.exists(mapped_path):
            self.tagged_file = mapped_path
        elif os.path.exists(final_path):
            self.tagged_file = final_path
        else:
            self.tagged_file = os.path.join(data_dir, "tagged_posts.json")
        
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.chroma_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="retrieval_lens_posts",
            metadata={"description": "Google Photos Retrieval Discovery Engine relevant posts"}
        )

    def build_or_refresh_index(self, force_refresh: bool = False) -> int:
        """Indexes all relevant post records from data/final_tagged_dataset_mapped.json."""
        if not os.path.exists(self.tagged_file):
            logger.warning(f"Tagged file not found at {self.tagged_file}")
            return 0

        if force_refresh:
            try:
                self.client.delete_collection(name="retrieval_lens_posts")
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name="retrieval_lens_posts",
                metadata={"description": "Google Photos Retrieval Discovery Engine relevant posts"}
            )

        existing_count = self.collection.count()
        if existing_count > 0 and not force_refresh:
            logger.info(f"ChromaDB index already populated with {existing_count} records.")
            return existing_count

        with open(self.tagged_file, "r", encoding="utf-8") as f:
            tagged_data = json.load(f)

        relevant_posts = [p for p in tagged_data if p.get("taxonomy", {}).get("relevant") is True]
        if not relevant_posts:
            logger.warning("No relevant post records found to index.")
            return 0

        documents = []
        metadatas = []
        ids = []

        for p in relevant_posts:
            post_id = p.get("post_id")
            title = p.get("title", "")
            raw_text = p.get("raw_text", "")
            full_text = f"{title}\n{raw_text}".strip()
            
            tax = p.get("taxonomy", {})
            quote = tax.get("quote", title[:100] if title else raw_text[:100])

            documents.append(full_text)
            metadatas.append({
                "post_id": post_id,
                "source": p.get("source", "unknown"),
                "url": p.get("url") or "",
                "created_at": p.get("created_at", "2024-01-01"),
                "quote": quote,
                "quote_verified": tax.get("quote_verified", False),
                "target_type": tax.get("target_type", "other"),
                "failure_step": tax.get("failure_step", "no_or_wrong_results")
            })
            ids.append(post_id)

        # Batch upsert into Chroma in chunks of 500
        batch_size = 500
        total_items = len(ids)
        for i in range(0, total_items, batch_size):
            end_idx = min(i + batch_size, total_items)
            self.collection.upsert(
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
            logger.info(f"ChromaDB batch indexed {end_idx}/{total_items} documents...")

        new_count = self.collection.count()
        logger.info(f"ChromaDB index populated with {new_count} relevant post documents.")
        return new_count

    def query_similar(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-N semantically similar post records for a query."""
        if self.collection.count() == 0:
            self.build_or_refresh_index()

        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count())
        )

        matched_records = []
        if results and results.get("metadatas"):
            metas = results["metadatas"][0]
            docs = results["documents"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(metas)

            for meta, doc, dist in zip(metas, docs, distances):
                matched_records.append({
                    "post_id": meta.get("post_id"),
                    "source": meta.get("source"),
                    "url": meta.get("url"),
                    "created_at": meta.get("created_at"),
                    "quote": meta.get("quote"),
                    "quote_verified": meta.get("quote_verified", False),
                    "target_type": meta.get("target_type"),
                    "failure_step": meta.get("failure_step"),
                    "matched_text": doc,
                    "distance": dist
                })

        return matched_records
