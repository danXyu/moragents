import logging
from typing import List, Optional

from langchain_core.embeddings import Embeddings
from together import Together

logger = logging.getLogger(__name__)


class TogetherEmbeddings(Embeddings):
    """Wrapper around Together AI embedding models."""

    def __init__(
        self,
        model_name: str = "togethercomputer/m2-bert-80M-8k-retrieval",
        api_key: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize the Together Embeddings client.

        Args:
            model_name: Name of the embedding model to use.
            api_key: Together API key (defaults to environment variable).
            **kwargs: Additional keyword arguments to pass to the Together client.
        """
        self.model_name = model_name
        self.client = Together(api_key=api_key, **kwargs)
        logger.info(f"Initialized TogetherEmbeddings with model: {model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        try:
            response = self.client.embeddings.create(model=self.model_name, input=texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Embed a single text query.

        Args:
            text: The text to embed.

        Returns:
            Embedding for the text.
        """
        try:
            response = self.client.embeddings.create(model=self.model_name, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
