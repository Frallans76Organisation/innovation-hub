"""
RAG-Enhanced Service Mapper
Uses semantic search via RAG to find relevant services
"""

import os
from typing import List, Dict, Any, Optional
from .rag_service import RAGService
from .service_mapper import ServiceMapper


class RAGServiceMapper:
    """Enhanced service mapper using RAG for semantic search"""

    def __init__(self, use_rag: bool = True):
        """
        Initialize RAG service mapper

        Args:
            use_rag: Whether to use RAG search (True) or fall back to keyword matching (False)
        """
        self.use_rag = use_rag
        self.rag_service = None
        self.keyword_mapper = ServiceMapper()  # Fallback

        if use_rag:
            try:
                self.rag_service = RAGService(persist_directory="./chroma_db")
                print(f"✅ RAG service mapper initialized ({self.rag_service.collection.count()} documents)")
            except Exception as e:
                print(f"⚠️ Failed to initialize RAG, falling back to keyword matching: {e}")
                self.use_rag = False

    def ensure_services_loaded(self):
        """Ensure services are loaded in at least one system"""
        if self.use_rag and self.rag_service:
            if self.rag_service.collection.count() > 0:
                return True

        # Fall back to keyword mapper
        if not self.keyword_mapper.loaded:
            self.keyword_mapper.load_service_catalog()

        return self.keyword_mapper.loaded

    def map_idea_to_services(
        self,
        idea_description: str,
        idea_title: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Map an idea against existing services using RAG

        Args:
            idea_description: Description of the idea
            idea_title: Title of the idea
            top_k: Number of top matching services to return

        Returns:
            Dictionary with mapping results
        """
        self.ensure_services_loaded()

        # Combine title and description for better matching
        query_text = f"{idea_title}. {idea_description}"

        if self.use_rag and self.rag_service and self.rag_service.collection.count() > 0:
            return self._map_with_rag(query_text, top_k)
        else:
            return self._map_with_keywords(query_text, top_k)

    def _map_with_rag(self, query_text: str, top_k: int) -> Dict[str, Any]:
        """Map using RAG semantic search"""
        try:
            # Search in RAG
            results = self.rag_service.search(query_text, n_results=top_k)

            if not results:
                return self._no_match_result()

            # Process results
            matching_services = []
            for result in results:
                # Calculate similarity score (ChromaDB returns distance, lower is better)
                # Convert distance to similarity score (0-1)
                distance = result.get('distance', 1.0)
                similarity_score = max(0, 1.0 - distance)

                matching_services.append({
                    'name': result['metadata'].get('filename', 'Unknown Service'),
                    'description': result['text'][:200],  # First 200 chars
                    'match_score': similarity_score,
                    'source': 'rag'
                })

            # Get best match
            best_match = matching_services[0]
            best_score = best_match['match_score']

            # Determine recommendation
            if best_score >= 0.7:
                recommendation = "existing_service"
                confidence = best_score
                reasoning = f"Stark matchning ({int(best_score*100)}%) mot befintlig tjänst: {best_match['name']}"
                impact = "low"
            elif best_score >= 0.5:
                recommendation = "develop_existing"
                confidence = 0.7
                reasoning = f"Medel matchning ({int(best_score*100)}%) - kan utveckla befintlig tjänst: {best_match['name']}"
                impact = "medium"
            else:
                recommendation = "new_service"
                confidence = 0.8
                reasoning = f"Låg matchning ({int(best_score*100)}%) - ny tjänst behövs troligen."
                impact = "high"

            return {
                'service_recommendation': recommendation,
                'service_confidence': confidence,
                'service_reasoning': reasoning,
                'matching_services': matching_services[:top_k],
                'development_impact': impact,
                'best_match_score': best_score
            }

        except Exception as e:
            print(f"❌ RAG mapping failed: {e}")
            return self._map_with_keywords(query_text, top_k)

    def _map_with_keywords(self, query_text: str, top_k: int) -> Dict[str, Any]:
        """Fallback: Map using keyword matching"""
        try:
            result = self.keyword_mapper.map_idea_to_services(query_text, top_k=top_k)
            return result
        except Exception as e:
            print(f"❌ Keyword mapping failed: {e}")
            return self._no_match_result()

    def _no_match_result(self) -> Dict[str, Any]:
        """Return default result when no services match"""
        return {
            'service_recommendation': 'new_service',
            'service_confidence': 0.8,
            'service_reasoning': 'Inga tjänster tillgängliga för matchning - ny tjänst behövs troligen.',
            'matching_services': [],
            'development_impact': 'high',
            'best_match_score': 0.0
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the service mapper"""
        stats = {
            'mode': 'rag' if self.use_rag else 'keyword',
            'rag_enabled': self.use_rag
        }

        if self.use_rag and self.rag_service:
            rag_stats = self.rag_service.get_stats()
            stats.update({
                'rag_documents': rag_stats['unique_documents'],
                'rag_chunks': rag_stats['total_chunks']
            })
        else:
            stats.update({
                'keyword_services': len(self.keyword_mapper.services) if self.keyword_mapper.loaded else 0
            })

        return stats
