#!/usr/bin/env python3
"""
RAG Service Integration for Service Mapping
This script maps innovation ideas to existing city services using RAG
"""

import os
import requests
import json
from typing import List, Dict, Optional


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Safely get environment variable"""
    return os.getenv(name, default or "")


class RAGServiceMapper:
    """Service for mapping ideas to existing services using RAG"""

    def __init__(self):
        self.rag_service_url = get_env_var(
            "RAG_SERVICE_URL", "https://esbst.goteborg.se/vllm-19020/v1"
        )
        self.rag_api_key = get_env_var("RAG_API_KEY")
        self.openrouter_api_key = get_env_var("OPENROUTER_API_KEY")

    def map_idea_to_services(self, idea_text: str, idea_title: str) -> Dict:
        """Map an innovation idea to existing city services"""

        prompt = f"""Analyze the following innovation idea and identify relevant existing city services:

Idea Title: {idea_title}

Idea Description: {idea_text}

Based on Göteborg City's service catalog, provide a comprehensive service mapping analysis including:

1. Directly related existing services (with confidence scores 0-100)
2. Potentially overlapping services (with confidence scores 0-100)  
3. Complementary services that could integrate (with confidence scores 0-100)
4. Services that might be affected or need updates (with confidence scores 0-100)
5. Any gaps in current service offerings that this idea addresses

Return the results as a well-structured JSON object with clear categorization and confidence scores.

Be thorough and analytical in your assessment."""

        return self._call_rag_service(prompt)

    def _call_rag_service(self, prompt: str) -> Dict:
        """Call the RAG service with the given prompt"""

        headers = {"Content-Type": "application/json"}

        # Try primary RAG service first
        if self.rag_api_key:
            headers["Authorization"] = f"Bearer {self.rag_api_key}"
            service_url = self.rag_service_url
        elif self.openrouter_api_key:
            headers["Authorization"] = f"Bearer {self.openrouter_api_key}"
            service_url = "https://openrouter.ai/api/v1"
        else:
            # Fallback to public endpoint without auth
            service_url = self.rag_service_url

        data = {
            "model": "mistralai/Devstral-2-123B-Instruct-2512",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1000,
        }

        try:
            response = requests.post(
                f"{service_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]

                # Try to parse as JSON, if not, return raw content
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {
                        "raw_analysis": content,
                        "service_mappings": [],
                        "gaps_identified": [],
                    }

            return {"error": "No valid response from RAG service"}

        except Exception as e:
            print(f"⚠️ RAG Service Error: {str(e)}")
            return {
                "error": str(e),
                "fallback_analysis": "Manual service mapping review recommended",
            }

    def get_service_recommendations(self, idea_text: str) -> List[Dict]:
        """Get specific service integration recommendations"""

        prompt = f"""Based on this innovation idea, provide specific recommendations for service integration:

Idea: {idea_text}

For each relevant city service, provide:
- Service name and description
- Integration approach (API, data sharing, process integration, etc.)
- Expected benefits of integration
- Implementation complexity (Low/Medium/High)
- Priority recommendation (Low/Medium/High)

Return as JSON array of integration recommendations."""

        result = self._call_rag_service(prompt)

        if isinstance(result, dict) and "raw_analysis" in result:
            # Try to extract recommendations from raw text
            recommendations = []
            for line in result["raw_analysis"].split("\n"):
                if line.strip() and any(
                    word in line.lower()
                    for word in ["recommend", "integrate", "service"]
                ):
                    recommendations.append(
                        {"recommendation": line.strip(), "source": "text_analysis"}
                    )
            return recommendations

        return result.get("recommendations", [])


def main():
    """Test the RAG service integration"""
    import sys

    if len(sys.argv) < 3:
        print(
            "Usage: python rag_service_integration.py <idea_title> <idea_description>"
        )
        return 1

    idea_title = sys.argv[1]
    idea_description = " ".join(sys.argv[2:])

    mapper = RAGServiceMapper()

    print("🗺️ Mapping idea to existing services...")
    service_mapping = mapper.map_idea_to_services(idea_description, idea_title)

    print("\n📊 Service Mapping Results:")
    print(json.dumps(service_mapping, indent=2, ensure_ascii=False))

    print("\n💡 Integration Recommendations:")
    recommendations = mapper.get_service_recommendations(idea_description)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.get('recommendation', 'No recommendation')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
