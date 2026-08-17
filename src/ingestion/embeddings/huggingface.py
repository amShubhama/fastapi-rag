from langchain_huggingface import (
    HuggingFaceEmbeddings,
)


class EmbeddingService:

    def __init__(
        self,
        model_name: str,
    ):
        self.model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={
                "device": "cpu",
            },
            encode_kwargs={
                "normalize_embeddings": True,
            },
        )

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        return self.model.embed_documents(texts)

    def embed_query(
        self,
        text: str,
    ) -> list[float]:

        return self.model.embed_query(text)
