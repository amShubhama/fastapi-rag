from langchain_community.document_loaders import PyMuPDFLoader, TextLoader


class DocumentLoader:

    def load(self, file_path: str, document_type: str):
        if document_type == "pdf":
            loader = PyMuPDFLoader(file_path)
        elif document_type == "txt":
            loader = TextLoader(file_path=file_path)
        else:
            raise ValueError("Unsupported Dcoument")

        return loader.load()
