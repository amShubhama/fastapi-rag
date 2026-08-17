from langchain_community.document_loaders import (
    PyMuPDFLoader,
)


class PDFLoader:

    def load(self, file_path: str):
        loader = PyMuPDFLoader(file_path)

        return loader.load()
