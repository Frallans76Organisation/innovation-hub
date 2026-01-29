"""
OpenRouter Client for AI Analysis
Handles communication with Qwen3 32B model via OpenRouter API
"""

import os
import httpx
import json
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class OpenRouterClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("AI_MODEL", "qwen/qwen3-32b")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        # Configure HTTP client with timeout and retries
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://innovation-hub.local",
                "X-Title": "Innovation Hub AI Analysis"
            }
        )

    async def chat_completion(
        self,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Send chat completion request to Qwen3 32B
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )

            if response.status_code != 200:
                error_text = response.text
                print(f"❌ OpenRouter API error {response.status_code}: {error_text}")
                return None

            result = response.json()

            # Extract the response content
            if result.get("choices") and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                if content and content.strip():
                    return {
                        "content": content.strip(),
                        "usage": result.get("usage", {}),
                        "model": result.get("model", self.model)
                    }

            print("❌ Empty or invalid response from OpenRouter")
            return None

        except httpx.TimeoutException:
            print("❌ OpenRouter request timed out")
            return None
        except httpx.RequestError as e:
            print(f"❌ OpenRouter request error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error in OpenRouter client: {e}")
            return None

    async def analyze_text(
        self,
        text: str,
        analysis_type: str,
        context: str = "",
        structured: bool = True
    ) -> Optional[str]:
        """
        Analyze text using Qwen3 32B with specific prompts
        """
        system_prompt = self._get_system_prompt(analysis_type)
        user_prompt = self._format_user_prompt(text, analysis_type, context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Use lower temperature for structured analysis
        temperature = 0.2 if structured else 0.3

        response = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=1000
        )

        return response["content"] if response else None

    def _get_system_prompt(self, analysis_type: str) -> str:
        """Get system prompt for specific analysis type"""

        base_prompt = """Du är en AI-assistent som analyserar idéer och förslag för svenska offentliga organisationer.
Du är expert på innovation inom offentlig sektor och förstår svenska förhållanden väl.

Dina svar ska vara:
- Objektiva och professionella
- Baserade på svensk offentlig sektor kontext
- Strukturerade och tydliga
- På svenska"""

        specific_prompts = {
            "categorization": base_prompt + """

Din uppgift är att kategorisera idéer baserat på dessa befintliga kategorier:
1. Digital transformation - Digitalisering av tjänster och processer
2. Medborgarservice - Förbättring av service till medborgare
3. Miljö och klimat - Hållbarhet och miljöinitiativ
4. Processer och effektivitet - Förbättring av interna processer
5. Innovation och utveckling - Nya idéer och lösningar

Svara endast med kategorinumret (1-5) och kategorins namn.""",

            "priority": base_prompt + """

Din uppgift är att bedöma prioritet baserat på:
- Påverkan på medborgare/verksamhet
- Genomförbarhet och kostnad
- Strategisk relevans för offentlig sektor
- Tidsaspekt (brådskande behov)

Svara med: låg, medel, eller hög""",

            "tags": base_prompt + """

Din uppgift är att föreslå 3-5 relevanta taggar som beskriver idén.
Taggar ska vara:
- Korta (1-2 ord)
- Relevanta för svensk offentlig sektor
- Sökbara nyckelord
- På svenska (småbokstäver)

Svara endast med taggarna separerade av komma.""",

            "sentiment": base_prompt + """

Din uppgift är att bedöma sentiment och ton i idén:
- positiv: Konstruktiv, lösningsfokuserad
- neutral: Faktabaserad, balanserad
- negativ: Kritisk, problemfokuserad

Svara endast med: positiv, neutral, eller negativ""",

            "status": base_prompt + """

Din uppgift är att föreslå lämplig initial status baserat på idéns mognad:
- ny: Tidig idé, behöver mer utveckling
- granskning: Välutvecklad idé redo för bedömning
- godkänd: Klar idé med tydlig genomförande plan

Svara endast med: ny, granskning, eller godkänd"""
        }

        return specific_prompts.get(analysis_type, base_prompt)

    def _format_user_prompt(self, text: str, analysis_type: str, context: str) -> str:
        """Format user prompt for analysis"""

        base_text = f"""Idé att analysera:

Titel: {context.get('title', 'Ej angiven') if isinstance(context, dict) else context}

Beskrivning: {text}

Typ: {context.get('type', 'Ej angiven') if isinstance(context, dict) else 'Ej angiven'}
Målgrupp: {context.get('target_group', 'Ej angiven') if isinstance(context, dict) else 'Ej angiven'}"""

        specific_instructions = {
            "categorization": "Vilken kategori passar bäst för denna idé?",
            "priority": "Vilken prioritet ska denna idé ha?",
            "tags": "Vilka taggar beskriver bäst denna idé?",
            "sentiment": "Vilken sentiment har denna idé?",
            "status": "Vilken status bör denna idé ha initialt?"
        }

        instruction = specific_instructions.get(analysis_type, "Analysera denna idé:")

        return f"{base_text}\n\n{instruction}"

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global client instance
_client = None

async def get_ai_client() -> OpenRouterClient:
    """Get or create the global AI client instance"""
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client

async def close_ai_client():
    """Close the global AI client"""
    global _client
    if _client:
        await _client.close()
        _client = None