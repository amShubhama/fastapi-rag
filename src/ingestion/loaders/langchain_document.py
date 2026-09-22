from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)


class DocumentLoader:

    def load(self, file_path: str, document_type: str):
        if document_type == "pdf":
            loader = PyMuPDFLoader(file_path)
        elif document_type == "txt":
            loader = TextLoader(file_path=file_path)
        elif document_type in ["docx", "doc"]:
            loader = UnstructuredWordDocumentLoader(file_path=file_path, mode="single")
        else:
            raise ValueError("Unsupported Dcoument")

        return loader.load()
