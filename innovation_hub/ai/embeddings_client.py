"""
OpenAI Embeddings Client
Handles text embedding generation for RAG system
"""

import os
from typing import List
from openai import OpenAI


class EmbeddingsClient:
    """Client for generating embeddings using OpenAI API"""

    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"  # Cost-effective, good quality
        print(f"✅ Embeddings client initialized with model: {self.model}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"❌ Error generating batch embeddings: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        # text-embedding-3-small returns 1536 dimensions
        return 1536
