"""
AI Analysis Service
Coordinates intelligent analysis of innovation ideas using Qwen3 32B
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .openrouter_client import get_ai_client
from .service_mapper import get_service_mapper
from .rag_service_mapper import RAGServiceMapper
from ..database import IdeaStatus, IdeaType, Priority, TargetGroup

@dataclass
class AnalysisResult:
    """Result of AI analysis"""
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[IdeaStatus] = None
    tags: List[str] = None
    sentiment: Optional[str] = None
    confidence_score: float = 0.0
    analysis_notes: Optional[str] = None
    # Service mapping results
    service_recommendation: Optional[str] = None  # "existing_service", "develop_existing", "new_service"
    service_confidence: Optional[float] = None
    service_reasoning: Optional[str] = None
    matching_services: List[Dict] = None
    development_impact: Optional[str] = None  # "low", "medium", "high"

class AIAnalysisService:
    def __init__(self):
        self.categories = {
            1: {"name": "Digital transformation", "keywords": ["digital", "teknologi", "ai", "automation", "system"]},
            2: {"name": "Medborgarservice", "keywords": ["medborgare", "service", "tjänst", "kundtjänst", "användar"]},
            3: {"name": "Miljö och klimat", "keywords": ["miljö", "klimat", "hållbar", "grön", "energi"]},
            4: {"name": "Processer och effektivitet", "keywords": ["process", "effektiv", "förbättr", "optimering", "kostnad"]},
            5: {"name": "Innovation och utveckling", "keywords": ["innovation", "utveckling", "forskning", "ny", "kreativ"]}
        }

    async def analyze_idea_comprehensive(
        self,
        title: str,
        description: str,
        idea_type: str,
        target_group: str
    ) -> AnalysisResult:
        """
        Perform comprehensive analysis of an idea
        """
        context = {
            "title": title,
            "type": idea_type,
            "target_group": target_group
        }

        print(f"🤖 Analyzing idea: '{title}' with Qwen3 32B...")

        try:
            # Run all analyses in parallel for efficiency
            tasks = [
                self._analyze_category(description, context),
                self._analyze_priority(description, context),
                self._generate_tags(description, context),
                self._analyze_sentiment(description, context),
                self._suggest_status(description, context)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            category_result = results[0] if not isinstance(results[0], Exception) else None
            priority_result = results[1] if not isinstance(results[1], Exception) else None
            tags_result = results[2] if not isinstance(results[2], Exception) else []
            sentiment_result = results[3] if not isinstance(results[3], Exception) else None
            status_result = results[4] if not isinstance(results[4], Exception) else None

            # Service mapping analysis (runs separately)
            service_mapping = self._analyze_service_mapping(title, description)

            # Build final result
            analysis = AnalysisResult()

            # Process category
            if category_result:
                category_id, category_name = self._parse_category_result(category_result)
                analysis.category_id = category_id
                analysis.category_name = category_name

            # Process priority
            if priority_result:
                analysis.priority = self._parse_priority_result(priority_result)

            # Process tags
            if tags_result:
                analysis.tags = self._parse_tags_result(tags_result)

            # Process sentiment
            if sentiment_result:
                analysis.sentiment = self._clean_response(sentiment_result)

            # Process status
            if status_result:
                analysis.status = self._parse_status_result(status_result)

            # Process service mapping results
            if service_mapping:
                analysis.service_recommendation = service_mapping.get("recommendation")
                analysis.service_confidence = service_mapping.get("confidence")
                analysis.service_reasoning = service_mapping.get("reasoning")
                analysis.matching_services = service_mapping.get("matching_services", [])

                # Determine development impact based on recommendation
                if analysis.service_recommendation == "new_service":
                    analysis.development_impact = "high"
                elif analysis.service_recommendation == "develop_existing":
                    analysis.development_impact = "medium"
                else:
                    analysis.development_impact = "low"

            # Calculate confidence based on successful analyses
            successful_analyses = sum([
                1 for result in results if not isinstance(result, Exception)
            ])
            analysis.confidence_score = successful_analyses / len(results)

            # Generate analysis notes
            analysis.analysis_notes = self._generate_analysis_notes(analysis, context)

            print(f"✅ Analysis complete: Category={analysis.category_name}, Priority={analysis.priority}, Tags={len(analysis.tags or [])}, Service={analysis.service_recommendation}")

            return analysis

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return AnalysisResult()

    async def _analyze_category(self, text: str, context: Dict) -> Optional[str]:
        """Analyze and suggest category"""
        client = await get_ai_client()
        return await client.analyze_text(text, "categorization", context, structured=True)

    async def _analyze_priority(self, text: str, context: Dict) -> Optional[str]:
        """Analyze and suggest priority"""
        client = await get_ai_client()
        return await client.analyze_text(text, "priority", context, structured=True)

    async def _generate_tags(self, text: str, context: Dict) -> Optional[str]:
        """Generate relevant tags"""
        client = await get_ai_client()
        return await client.analyze_text(text, "tags", context, structured=True)

    async def _analyze_sentiment(self, text: str, context: Dict) -> Optional[str]:
        """Analyze sentiment"""
        client = await get_ai_client()
        return await client.analyze_text(text, "sentiment", context, structured=True)

    async def _suggest_status(self, text: str, context: Dict) -> Optional[str]:
        """Suggest initial status"""
        client = await get_ai_client()
        return await client.analyze_text(text, "status", context, structured=True)

    def _parse_category_result(self, result: str) -> tuple[Optional[int], Optional[str]]:
        """Parse category analysis result"""
        if not result:
            return None, None

        result_clean = self._clean_response(result)

        # Try to extract category ID (1-5)
        category_match = re.search(r'(\d+)', result_clean)
        if category_match:
            category_id = int(category_match.group(1))
            if 1 <= category_id <= 5:
                return category_id, self.categories[category_id]["name"]

        # Fallback: keyword matching
        for cat_id, cat_info in self.categories.items():
            if any(keyword in result_clean.lower() for keyword in cat_info["keywords"]):
                return cat_id, cat_info["name"]

        # Default fallback
        return 5, "Innovation och utveckling"

    def _parse_priority_result(self, result: str) -> Optional[Priority]:
        """Parse priority analysis result"""
        if not result:
            return Priority.MEDIUM

        result_clean = self._clean_response(result).lower()

        if "hög" in result_clean or "high" in result_clean:
            return Priority.HIGH
        elif "låg" in result_clean or "low" in result_clean:
            return Priority.LOW
        else:
            return Priority.MEDIUM

    def _parse_tags_result(self, result: str) -> List[str]:
        """Parse tags from analysis result"""
        if not result:
            return []

        result_clean = self._clean_response(result)

        # Split by comma and clean up
        tags = [tag.strip().lower() for tag in result_clean.split(',')]

        # Filter valid tags (2-20 characters, Swedish characters allowed)
        valid_tags = []
        for tag in tags:
            if 2 <= len(tag) <= 20 and re.match(r'^[a-zåäöA-ZÅÄÖ\s-]+$', tag):
                # Replace spaces with hyphens for consistency
                clean_tag = re.sub(r'\s+', '-', tag.strip())
                if clean_tag and clean_tag not in valid_tags:
                    valid_tags.append(clean_tag)

        return valid_tags[:5]  # Limit to 5 tags

    def _parse_status_result(self, result: str) -> Optional[IdeaStatus]:
        """Parse status suggestion"""
        if not result:
            return IdeaStatus.NEW

        result_clean = self._clean_response(result).lower()

        if "granskning" in result_clean:
            return IdeaStatus.REVIEWING
        elif "godkänd" in result_clean:
            return IdeaStatus.APPROVED
        else:
            return IdeaStatus.NEW

    def _clean_response(self, response: str) -> str:
        """Clean AI response text"""
        if not response:
            return ""

        # Remove common AI response prefixes/suffixes
        cleaned = response.strip()

        # Remove quotes
        cleaned = cleaned.strip('"\'')

        # Remove common prefixes
        prefixes_to_remove = [
            "svaret är:", "svar:", "resultat:", "kategorin är:",
            "prioriteten är:", "taggarna är:", "sentiment:",
            "status:", "kategori:"
        ]

        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()

        return cleaned

    def _analyze_service_mapping(self, title: str, description: str) -> Optional[Dict]:
        """Analyze how idea relates to existing services using RAG"""
        try:
            print("🔍 Analyzing service mapping...")

            # Try RAG-enhanced mapper first
            rag_mapper = RAGServiceMapper(use_rag=True)
            result = rag_mapper.map_idea_to_services(description, title, top_k=5)

            if result:
                print(f"🎯 Service mapping: {result['service_recommendation']} (confidence: {result['service_confidence']:.2f})")
                return {
                    "recommendation": result['service_recommendation'],
                    "confidence": result['service_confidence'],
                    "reasoning": result['service_reasoning'],
                    "matching_services": result['matching_services'],
                    "development_impact": result['development_impact']
                }

            # Fallback to keyword matching if RAG fails
            print("⚠️ RAG mapping unavailable, using keyword matching...")
            service_mapper = get_service_mapper()
            if not service_mapper.loaded:
                print("⚠️ Service catalog not loaded, skipping service mapping")
                return None

            # Find matching services
            idea_text = f"{title} {description}"
            matching_services = service_mapper.find_matching_services(idea_text, max_results=5)

            if not matching_services:
                print("📋 No matching services found")
                return {
                    "recommendation": "new_service",
                    "confidence": 0.8,
                    "reasoning": "Inga befintliga tjänster hittades som matchar detta behov.",
                    "matching_services": []
                }

            # Categorize development need
            result = service_mapper.categorize_idea_development_need(title, description, matching_services)

            # Convert service objects to dictionaries for JSON serialization
            serialized_matches = []
            for service, score in matching_services:
                serialized_matches.append({
                    "name": service.name,
                    "description": service.description,
                    "category": service.category,
                    "match_score": float(score)
                })

            result["matching_services"] = serialized_matches

            recommendation_text = {
                "existing_service": "befintlig tjänst",
                "develop_existing": "utveckla befintlig",
                "new_service": "ny tjänst"
            }.get(result["recommendation"], result["recommendation"])

            print(f"🎯 Service mapping: {recommendation_text} (confidence: {result['confidence']:.2f})")

            return result

        except Exception as e:
            print(f"❌ Service mapping failed: {e}")
            return None

    def _generate_analysis_notes(self, analysis: AnalysisResult, context: Dict) -> str:
        """Generate human-readable analysis notes"""
        notes = []

        if analysis.category_name:
            notes.append(f"Kategoriserad som: {analysis.category_name}")

        if analysis.priority:
            priority_text = {
                Priority.LOW: "låg",
                Priority.MEDIUM: "medel",
                Priority.HIGH: "hög"
            }.get(analysis.priority, "okänd")
            notes.append(f"Prioritet: {priority_text}")

        if analysis.sentiment:
            notes.append(f"Sentiment: {analysis.sentiment}")

        if analysis.tags:
            notes.append(f"Taggar: {', '.join(analysis.tags)}")

        if analysis.service_recommendation:
            service_text = {
                "existing_service": "Befintlig tjänst kan användas",
                "develop_existing": "Befintlig tjänst kan utvecklas",
                "new_service": "Ny tjänst behövs"
            }.get(analysis.service_recommendation, analysis.service_recommendation)
            notes.append(f"Tjänstebehov: {service_text}")

        if analysis.confidence_score:
            confidence_pct = int(analysis.confidence_score * 100)
            notes.append(f"AI-analys tillförlitlighet: {confidence_pct}%")

        return " | ".join(notes) if notes else "AI-analys genomförd"

# Global service instance
_service = None

def get_ai_analysis_service() -> AIAnalysisService:
    """Get or create the global AI analysis service instance"""
    global _service
    if _service is None:
        _service = AIAnalysisService()
    return _service