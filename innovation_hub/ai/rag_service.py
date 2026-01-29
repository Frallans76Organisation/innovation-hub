"""
RAG Service
Manages document storage, retrieval and semantic search using ChromaDB
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

from .embeddings_client import EmbeddingsClient
from .document_processor import DocumentProcessor


class RAGService:
    """RAG service for document storage and retrieval"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize RAG service

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        self.embeddings_client = EmbeddingsClient()
        self.document_processor = DocumentProcessor()

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="service_documents",
            metadata={"description": "Service catalog documents for innovation hub"}
        )

        print(f"✅ RAG service initialized")
        print(f"📊 Collection: {self.collection.name}")
        print(f"📈 Documents in collection: {self.collection.count()}")

    def add_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a document to the RAG system

        Args:
            file_path: Path to document file
            metadata: Optional additional metadata

        Returns:
            Dictionary with processing results
        """
        print(f"📄 Processing document: {file_path}")

        # Process document
        doc_info = self.document_processor.process_document(file_path)

        # Generate embeddings for all chunks
        print(f"🔮 Generating embeddings for {doc_info['chunk_count']} chunks...")
        embeddings = self.embeddings_client.embed_batch(doc_info['chunks'])

        # Prepare metadata for each chunk
        chunk_metadatas = []
        chunk_ids = []
        timestamp = datetime.now().isoformat()

        for i in range(len(doc_info['chunks'])):
            chunk_id = f"{doc_info['filename']}_chunk_{i}_{timestamp}"
            chunk_ids.append(chunk_id)

            chunk_metadata = {
                'filename': doc_info['filename'],
                'file_type': doc_info['file_type'],
                'chunk_index': i,
                'total_chunks': doc_info['chunk_count'],
                'timestamp': timestamp
            }

            # Add custom metadata if provided
            if metadata:
                chunk_metadata.update(metadata)

            chunk_metadatas.append(chunk_metadata)

        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=doc_info['chunks'],
            metadatas=chunk_metadatas
        )

        print(f"✅ Document added: {doc_info['filename']}")
        print(f"   Chunks: {doc_info['chunk_count']}")
        print(f"   Total documents in collection: {self.collection.count()}")

        return {
            'filename': doc_info['filename'],
            'chunk_count': doc_info['chunk_count'],
            'file_size': doc_info['file_size'],
            'status': 'success'
        }

    def add_text(self, text: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add raw text to RAG system

        Args:
            text: Text content
            filename: Identifier for this text
            metadata: Optional metadata

        Returns:
            Dictionary with processing results
        """
        print(f"📝 Processing text: {filename}")

        # Chunk text
        chunks = self.document_processor.chunk_text(text)

        # Generate embeddings
        print(f"🔮 Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embeddings_client.embed_batch(chunks)

        # Prepare metadata
        chunk_metadatas = []
        chunk_ids = []
        timestamp = datetime.now().isoformat()

        for i in range(len(chunks)):
            chunk_id = f"{filename}_chunk_{i}_{timestamp}"
            chunk_ids.append(chunk_id)

            chunk_metadata = {
                'filename': filename,
                'file_type': 'text',
                'chunk_index': i,
                'total_chunks': len(chunks),
                'timestamp': timestamp
            }

            if metadata:
                chunk_metadata.update(metadata)

            chunk_metadatas.append(chunk_metadata)

        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=chunk_metadatas
        )

        print(f"✅ Text added: {filename} ({len(chunks)} chunks)")

        return {
            'filename': filename,
            'chunk_count': len(chunks),
            'status': 'success'
        }

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of relevant documents with metadata
        """
        print(f"🔍 Searching for: '{query[:100]}...'")

        # Generate query embedding
        query_embedding = self.embeddings_client.embed_text(query)

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count())
        )

        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None,
                    'id': results['ids'][0][i]
                })

        print(f"✅ Found {len(formatted_results)} relevant documents")
        return formatted_results

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents in the collection

        Returns:
            List of all documents
        """
        results = self.collection.get()
        documents = []

        for i in range(len(results['ids'])):
            documents.append({
                'id': results['ids'][i],
                'text': results['documents'][i] if 'documents' in results else None,
                'metadata': results['metadatas'][i] if 'metadatas' in results else {}
            })

        return documents

    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete all chunks of a document

        Args:
            filename: Name of file to delete

        Returns:
            Dictionary with deletion results
        """
        # Get all documents
        all_docs = self.collection.get()

        # Find IDs matching filename
        ids_to_delete = []
        for i, metadata in enumerate(all_docs['metadatas']):
            if metadata.get('filename') == filename:
                ids_to_delete.append(all_docs['ids'][i])

        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
            print(f"✅ Deleted {len(ids_to_delete)} chunks from {filename}")
            return {
                'filename': filename,
                'chunks_deleted': len(ids_to_delete),
                'status': 'success'
            }
        else:
            print(f"⚠️ No chunks found for {filename}")
            return {
                'filename': filename,
                'chunks_deleted': 0,
                'status': 'not_found'
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG collection

        Returns:
            Dictionary with statistics
        """
        all_docs = self.collection.get()

        # Count unique documents
        unique_files = set()
        file_types = {}

        for metadata in all_docs['metadatas']:
            filename = metadata.get('filename', 'unknown')
            file_type = metadata.get('file_type', 'unknown')

            unique_files.add(filename)

            if file_type not in file_types:
                file_types[file_type] = 0
            file_types[file_type] += 1

        return {
            'total_chunks': self.collection.count(),
            'unique_documents': len(unique_files),
            'file_types': file_types,
            'collection_name': self.collection.name
        }

    def clear_collection(self):
        """Clear all documents from collection"""
        all_docs = self.collection.get()
        if all_docs['ids']:
            self.collection.delete(ids=all_docs['ids'])
            print(f"✅ Cleared {len(all_docs['ids'])} documents from collection")
