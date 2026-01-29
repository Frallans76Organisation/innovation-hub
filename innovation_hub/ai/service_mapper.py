"""
Service Mapper - Maps ideas against existing services
Loads and processes service catalog data for AI analysis
"""

import os
import json
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class ExistingService:
    """Represents an existing service from the catalog"""
    name: str
    description: str
    start_date: Optional[str] = None
    keywords: List[str] = None
    category: Optional[str] = None

class ServiceMapper:
    def __init__(self):
        self.services: List[ExistingService] = []
        self.service_index = {}  # For fast keyword-based lookup
        self.loaded = False

    def load_service_catalog(self, file_path: str = None) -> bool:
        """Load services from HTML table file"""
        if not file_path:
            file_path = "/home/frehal0707/use_cases/existingservicesandprojects/tjanstekatalog-export-2025-10-07_12_40_39.xls"

        if not os.path.exists(file_path):
            print(f"⚠️ Service catalog not found: {file_path}")
            return False

        try:
            print("📂 Loading service catalog...")

            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table')

            if not table:
                print("❌ No table found in HTML file")
                return False

            # Parse table rows
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    name = cells[0].get_text(strip=True)
                    description = cells[1].get_text(strip=True)
                    start_date = cells[2].get_text(strip=True) if cells[2] else None

                    # Generate keywords from name and description
                    keywords = self._extract_keywords(name + " " + description)

                    # Categorize service
                    category = self._categorize_service(name, description)

                    service = ExistingService(
                        name=name,
                        description=description,
                        start_date=start_date,
                        keywords=keywords,
                        category=category
                    )

                    self.services.append(service)

            # Build keyword index for fast lookup
            self._build_keyword_index()

            self.loaded = True
            print(f"✅ Loaded {len(self.services)} services from catalog")

            # Show some statistics
            categories = {}
            for service in self.services:
                cat = service.category or "Okänd"
                categories[cat] = categories.get(cat, 0) + 1

            print("📊 Service categories:")
            for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
                print(f"  {cat}: {count} services")

            return True

        except Exception as e:
            print(f"❌ Error loading service catalog: {e}")
            return False

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from service name and description"""
        # Clean and normalize text
        text = text.lower()
        text = re.sub(r'[^\wåäöÅÄÖ\s]', ' ', text)

        # Split into words and filter
        words = text.split()

        # Filter out common Swedish stop words and short words
        stop_words = {
            'och', 'att', 'det', 'en', 'är', 'för', 'av', 'med', 'som', 'på', 'till', 'den',
            'har', 'de', 'i', 'om', 'var', 'inte', 'kan', 'vi', 'ett', 'han', 'hon', 'du',
            'ska', 'blir', 'eller', 'så', 'från', 'när', 'över', 'under', 'efter', 'före',
            'mellan', 'hos', 'inom', 'utan', 'genom', 'mot', 'vid', 'upp', 'ner', 'ut', 'in',
            'bara', 'också', 'mycket', 'mer', 'än', 'här', 'där', 'nu', 'då', 'sedan',
            'bäst', 'passar', 'används', 'tjänst', 'service', 'system', 'lösning', 'för'
        }

        keywords = []
        for word in words:
            if len(word) >= 3 and word not in stop_words:
                keywords.append(word)

        # Keep only unique keywords, max 10 per service
        return list(set(keywords))[:10]

    def _categorize_service(self, name: str, description: str) -> str:
        """Automatically categorize service based on name and description"""
        text = (name + " " + description).lower()

        # Define category patterns
        categories = {
            "IT och Digital": [
                "system", "digital", "webb", "app", "api", "databas", "server", "nätverk",
                "internet", "email", "epost", "programvara", "mjukvara", "it", "dator",
                "teknologi", "mobil", "uppkoppling", "anslutning", "wifi", "fiber"
            ],
            "Kommunikation": [
                "kommunikation", "telefon", "samtal", "videokonferens", "möte", "meddelande",
                "anslagstavla", "information", "publicera", "kommunicera", "kontakt"
            ],
            "Säkerhet": [
                "säkerhet", "brandskydd", "övervakning", "kamera", "larm", "skydd", "säker",
                "behörighet", "access", "inloggning", "authentication", "autentisering"
            ],
            "Transport": [
                "transport", "fordons", "bil", "buss", "cykel", "parkering", "trafik",
                "väg", "resa", "mobilitet", "kollektivtrafik"
            ],
            "Fastighet och Lokaler": [
                "fastighet", "lokal", "byggnad", "hyra", "uthyrning", "utrymme", "rum",
                "kontor", "mötesrum", "facilitet", "underhåll", "rengöring"
            ],
            "Miljö och Hållbarhet": [
                "miljö", "hållbar", "energi", "avfall", "återvinning", "klimat", "grön",
                "förnybar", "koldioxid", "utsläpp", "natur", "ekologi"
            ],
            "Utbildning": [
                "utbildning", "kurs", "träning", "lärande", "skola", "undervisning",
                "kompetensutveckling", "workshop", "seminarium", "certifiering"
            ]
        }

        # Score each category
        category_scores = {}
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            category_scores[category] = score

        # Return category with highest score
        best_category = max(category_scores, key=category_scores.get)
        if category_scores[best_category] > 0:
            return best_category
        else:
            return "Övrig"

    def _build_keyword_index(self):
        """Build index for fast keyword-based service lookup"""
        self.service_index = {}

        for i, service in enumerate(self.services):
            # Index by keywords
            for keyword in service.keywords or []:
                if keyword not in self.service_index:
                    self.service_index[keyword] = []
                self.service_index[keyword].append(i)

            # Index by service name words
            name_words = service.name.lower().split()
            for word in name_words:
                if len(word) >= 3:
                    if word not in self.service_index:
                        self.service_index[word] = []
                    self.service_index[word].append(i)

    def find_matching_services(self, idea_text: str, max_results: int = 10) -> List[Tuple[ExistingService, float]]:
        """Find services that might match or relate to an idea"""
        if not self.loaded:
            return []

        # Extract keywords from idea
        idea_keywords = self._extract_keywords(idea_text)

        # Score services based on keyword matches
        service_scores = {}

        for keyword in idea_keywords:
            if keyword in self.service_index:
                for service_idx in self.service_index[keyword]:
                    if service_idx not in service_scores:
                        service_scores[service_idx] = 0
                    service_scores[service_idx] += 1

        # Sort by score and return top matches
        sorted_matches = sorted(service_scores.items(), key=lambda x: -x[1])

        results = []
        for service_idx, score in sorted_matches[:max_results]:
            service = self.services[service_idx]
            # Normalize score by number of keywords
            normalized_score = score / max(len(idea_keywords), 1)
            results.append((service, normalized_score))

        return results

    def categorize_idea_development_need(
        self,
        idea_title: str,
        idea_description: str,
        matching_services: List[Tuple[ExistingService, float]]
    ) -> Dict[str, any]:
        """
        Categorize whether idea needs:
        - Existing service can meet need
        - Existing service can be developed/extended
        - Completely new service needed
        """

        if not matching_services:
            return {
                "recommendation": "new_service",
                "confidence": 0.9,
                "reasoning": "Ingen befintlig tjänst hittades som matchar behovet.",
                "matching_services": []
            }

        # Analyze best matches
        best_match = matching_services[0]
        best_service, best_score = best_match

        # High similarity threshold
        if best_score >= 0.6:
            return {
                "recommendation": "existing_service",
                "confidence": min(0.9, best_score + 0.2),
                "reasoning": f"Befintlig tjänst '{best_service.name}' kan troligen möta behovet.",
                "matching_services": matching_services[:3],
                "primary_service": {
                    "name": best_service.name,
                    "description": best_service.description,
                    "category": best_service.category,
                    "match_score": best_score
                }
            }

        # Medium similarity - could be developed
        elif best_score >= 0.3:
            return {
                "recommendation": "develop_existing",
                "confidence": 0.7,
                "reasoning": f"Befintlig tjänst '{best_service.name}' skulle kunna utvecklas för att möta behovet.",
                "matching_services": matching_services[:5],
                "development_candidate": {
                    "name": best_service.name,
                    "description": best_service.description,
                    "category": best_service.category,
                    "match_score": best_score
                }
            }

        # Low similarity - probably needs new service
        else:
            return {
                "recommendation": "new_service",
                "confidence": 0.8,
                "reasoning": "Ingen befintlig tjänst matchar tillräckligt väl - ny tjänst behövs troligen.",
                "matching_services": matching_services[:3]
            }

    def get_service_summary(self) -> Dict[str, any]:
        """Get summary statistics about loaded services"""
        if not self.loaded:
            return {"loaded": False}

        categories = {}
        total_keywords = 0

        for service in self.services:
            cat = service.category or "Okänd"
            categories[cat] = categories.get(cat, 0) + 1
            total_keywords += len(service.keywords or [])

        return {
            "loaded": True,
            "total_services": len(self.services),
            "categories": categories,
            "avg_keywords_per_service": total_keywords / len(self.services) if self.services else 0,
            "sample_services": [
                {"name": s.name, "category": s.category}
                for s in self.services[:5]
            ]
        }

# Global service mapper instance
_service_mapper = None

def get_service_mapper() -> ServiceMapper:
    """Get or create the global service mapper instance"""
    global _service_mapper
    if _service_mapper is None:
        _service_mapper = ServiceMapper()
        # Try to load service catalog on first access
        _service_mapper.load_service_catalog()
    return _service_mapper