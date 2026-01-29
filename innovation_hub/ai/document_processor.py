"""
Document Processor
Handles loading and chunking of various document formats
"""

import os
from typing import List, Dict, Any
from pathlib import Path
import re


class DocumentProcessor:
    """Process and chunk documents for RAG system"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"✅ Document processor initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")

    def load_txt(self, file_path: str) -> str:
        """Load text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_pdf(self, file_path: str) -> str:
        """Load PDF file"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            raise

    def load_docx(self, file_path: str) -> str:
        """Load Word document"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"❌ Error loading DOCX: {e}")
            raise

    def load_xls(self, file_path: str) -> str:
        """Load Excel file (both .xls and .xlsx, including HTML-based .xls)"""
        try:
            from pathlib import Path
            file_ext = Path(file_path).suffix.lower()

            # First, check if it's actually HTML disguised as Excel
            with open(file_path, 'rb') as f:
                header = f.read(100)
                if header.startswith(b'<html') or b'<table' in header.lower():
                    # It's HTML, parse as such
                    print("📋 Detected HTML table in .xls file, parsing as HTML...")
                    return self.load_html_table(file_path)

            if file_ext == '.xls':
                # Old Excel format - use xlrd
                import xlrd
                wb = xlrd.open_workbook(file_path)
                text = ""
                for sheet in wb.sheets():
                    text += f"\n=== {sheet.name} ===\n"
                    for row_idx in range(sheet.nrows):
                        row_values = sheet.row_values(row_idx)
                        row_text = " | ".join([str(cell) if cell else "" for cell in row_values])
                        if row_text.strip():
                            text += row_text + "\n"
                return text
            else:
                # New Excel format - use openpyxl
                import openpyxl
                wb = openpyxl.load_workbook(file_path)
                text = ""
                for sheet in wb.worksheets:
                    text += f"\n=== {sheet.title} ===\n"
                    for row in sheet.iter_rows(values_only=True):
                        row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                        if row_text.strip():
                            text += row_text + "\n"
                return text
        except Exception as e:
            print(f"❌ Error loading Excel: {e}")
            raise

    def load_html_table(self, file_path: str) -> str:
        """Load HTML file with table data - each row as separate chunk for better RAG"""
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')

            # For service catalogs, treat each row as a separate "document" for better RAG matching
            # We'll add delimiters that the chunker can split on
            text = ""
            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')
                headers = None

                for row in rows:
                    cells = row.find_all(['td', 'th'])

                    # Check if this is header row
                    if cells and cells[0].name == 'th':
                        headers = [cell.get_text(strip=True) for cell in cells]
                        continue

                    # Data row - format as standalone entry
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]

                        # Create a complete entry for this service
                        if headers and len(row_data) >= 2:
                            service_name = row_data[0] if len(row_data) > 0 else ""
                            service_desc = row_data[1] if len(row_data) > 1 else ""

                            if service_name and service_desc:
                                # Each service as a complete entry with clear separation
                                text += f"\n\n=== TJÄNST: {service_name} ===\n"
                                text += f"Beskrivning: {service_desc}\n"
                                if len(row_data) > 2:
                                    text += f"Startdatum: {row_data[2]}\n"
                                text += "\n"  # Extra newline for separation
                        else:
                            # Fallback to simple format
                            row_text = " | ".join(row_data)
                            if row_text.strip():
                                text += row_text + "\n"

            return text
        except Exception as e:
            print(f"❌ Error loading HTML table: {e}")
            raise

    def load_document(self, file_path: str) -> Dict[str, Any]:
        """
        Load document and extract metadata

        Args:
            file_path: Path to document

        Returns:
            Dictionary with content and metadata
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # Load based on file type
        loaders = {
            '.txt': self.load_txt,
            '.pdf': self.load_pdf,
            '.docx': self.load_docx,
            '.doc': self.load_docx,
            '.xls': self.load_xls,
            '.xlsx': self.load_xls
        }

        if extension not in loaders:
            raise ValueError(f"Unsupported file type: {extension}")

        content = loaders[extension](file_path)

        return {
            'content': content,
            'filename': path.name,
            'file_type': extension,
            'file_size': path.stat().st_size,
            'char_count': len(content)
        }

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If not at the end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
                last_sentence = -1

                for ending in sentence_endings:
                    pos = text.rfind(ending, start, end)
                    if pos > last_sentence:
                        last_sentence = pos + len(ending)

                if last_sentence > start:
                    end = last_sentence

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Load and chunk a document

        Args:
            file_path: Path to document

        Returns:
            Dictionary with document metadata and chunks
        """
        doc_info = self.load_document(file_path)
        chunks = self.chunk_text(doc_info['content'])

        return {
            'filename': doc_info['filename'],
            'file_type': doc_info['file_type'],
            'file_size': doc_info['file_size'],
            'char_count': doc_info['char_count'],
            'chunks': chunks,
            'chunk_count': len(chunks)
        }

    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Process all documents in a directory

        Args:
            directory_path: Path to directory

        Returns:
            List of processed documents
        """
        directory = Path(directory_path)
        documents = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.pdf', '.docx', '.doc', '.xls', '.xlsx']:
                try:
                    doc = self.process_document(str(file_path))
                    doc['file_path'] = str(file_path)
                    documents.append(doc)
                    print(f"✅ Processed: {file_path.name} ({doc['chunk_count']} chunks)")
                except Exception as e:
                    print(f"⚠️ Failed to process {file_path.name}: {e}")

        return documents
