"""
Service Catalog Loader
Special loader that imports service catalog with each service as separate document
"""

from typing import List, Dict
from bs4 import BeautifulSoup
from .rag_service import RAGService


class ServiceCatalogLoader:
    """Load service catalog with each service as individual document for optimal RAG matching"""

    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service

    def load_html_service_catalog(self, file_path: str) -> Dict:
        """
        Load service catalog from HTML file, treating each service as separate document

        Args:
            file_path: Path to HTML file with service catalog table

        Returns:
            Dictionary with loading results
        """
        print(f"📚 Loading service catalog from: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table')

            if not table:
                raise ValueError("No table found in HTML file")

            rows = table.find_all('tr')
            headers = None
            services_loaded = 0

            for row in rows:
                cells = row.find_all(['td', 'th'])

                # Check if header row
                if cells and cells[0].name == 'th':
                    headers = [cell.get_text(strip=True) for cell in cells]
                    continue

                # Data row - process as individual service
                if cells and len(cells) >= 2:
                    service_name = cells[0].get_text(strip=True)
                    service_description = cells[1].get_text(strip=True)
                    start_date = cells[2].get_text(strip=True) if len(cells) > 2 else ""

                    if service_name and service_description:
                        # Create complete service text
                        service_text = f"""Tjänst: {service_name}

Beskrivning: {service_description}

Startdatum: {start_date}

Detta är en befintlig tjänst som kan användas eller utvecklas för att möta liknande behov."""

                        # Add as separate document with service name as identifier
                        self.rag_service.add_text(
                            text=service_text,
                            filename=service_name,  # Use service name as identifier!
                            metadata={
                                'service_name': service_name,
                                'service_type': 'municipal_service',
                                'start_date': start_date,
                                'source': 'service_catalog'
                            }
                        )

                        services_loaded += 1

            print(f"✅ Loaded {services_loaded} services into RAG")
            print(f"📊 Total documents in RAG: {self.rag_service.collection.count()}")

            return {
                'services_loaded': services_loaded,
                'total_chunks': self.rag_service.collection.count(),
                'status': 'success'
            }

        except Exception as e:
            print(f"❌ Error loading service catalog: {e}")
            raise
