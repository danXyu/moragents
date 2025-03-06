import logging
import os
from typing import Any, List

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from werkzeug.utils import secure_filename
from fastapi import UploadFile

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")


class VectorStoreService:
    """Service for managing document embeddings and retrieval using vector stores."""

    def __init__(self, embeddings: Any) -> None:
        """Initialize the vector store service.

        Args:
            embeddings: The embedding model to use for document vectorization.
        """
        self.embeddings = embeddings
        self.vector_store = None
        self.retriever = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        self.max_size = 5 * 1024 * 1024  # 5 MB

        # Ensure upload folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    async def process_file(self, file: UploadFile) -> str:
        """Process an uploaded file and add it to the vector store.

        Args:
            file: The uploaded file to process.

        Returns:
            A message indicating success or failure.

        Raises:
            ValueError: If the file is too large or empty.
        """
        if file.filename == "":
            raise ValueError("Please select a file to upload")

        # Check file size to ensure it's less than max size
        content = await file.read()
        await file.seek(0)
        if len(content) > self.max_size:
            raise ValueError(
                f"The file is too large. Please upload a file less than {self.max_size // (1024 * 1024)} MB"
            )

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Process the document
        documents = self._load_documents(file_path)
        await self.add_documents(documents)

        return f"Successfully processed and indexed file: {filename}"

    def _load_documents(self, file_path: str) -> List[Document]:
        """Load documents from a file path.

        Args:
            file_path: The path to the file to load.

        Returns:
            A list of Document objects.
        """
        loader = PyMuPDFLoader(file_path)
        return loader.load()

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store.

        Args:
            documents: The documents to add to the vector store.
        """
        split_documents = self.text_splitter.split_documents(documents)

        if self.vector_store is None:
            # Initialize the vector store if it doesn't exist
            self.vector_store = FAISS.from_documents(split_documents, self.embeddings)
        else:
            # Add documents to existing vector store
            self.vector_store.add_documents(split_documents)

        # Update the retriever
        self._update_retriever()

    def _update_retriever(self, k: int = 7) -> None:
        """Update the retriever with the current vector store.

        Args:
            k: The number of documents to retrieve.
        """
        if self.vector_store is not None:
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": k})

    async def retrieve(self, query: str) -> List[Document]:
        """Retrieve documents relevant to a query.

        Args:
            query: The query to retrieve documents for.

        Returns:
            A list of retrieved documents.

        Raises:
            ValueError: If the retriever is not initialized.
        """
        if self.retriever is None:
            raise ValueError("Retriever not initialized. Please add documents first.")

        return self.retriever.invoke(query)

    def save(self, path: str) -> None:
        """Save the vector store to disk.

        Args:
            path: The path to save the vector store to.
        """
        if self.vector_store is not None:
            self.vector_store.save_local(path)

    @classmethod
    def load(cls, path: str, embeddings: Any) -> "VectorStoreService":
        """Load a vector store from disk.

        Args:
            path: The path to load the vector store from.
            embeddings: The embedding model to use.

        Returns:
            A new VectorStoreService instance with the loaded vector store.
        """
        service = cls(embeddings)
        service.vector_store = FAISS.load_local(path, embeddings)
        service._update_retriever()
        return service
