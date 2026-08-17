from pathlib import Path
from uuid import UUID, uuid4


class DocumentStorage:
    BASE_DIR = Path("storage/documents")
    TEMP_DIR = Path("storage/.tmp")

    def __init__(self) -> None:
        self.BASE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.TEMP_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def create_temp_path(self) -> Path:
        return self.TEMP_DIR / f"{uuid4()}.tmp"

    def create_final_path(
        self,
        user_id: UUID,
        extension: str,
    ) -> tuple[Path, str]:

        extension = extension.lower()

        if not extension.startswith("."):
            extension = f".{extension}"

        document_type = extension.removeprefix(".")

        directory = self.BASE_DIR / "users" / str(user_id) / document_type

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = f"{uuid4()}{extension}"

        return (
            directory / stored_filename,
            stored_filename,
        )

    def to_storage_path(
        self,
        path: Path,
    ) -> str:
        return str(path.relative_to(self.BASE_DIR))

    def resolve(
        self,
        storage_path: str,
    ) -> Path:

        base = self.BASE_DIR.resolve()

        path = (self.BASE_DIR / storage_path).resolve()

        if not path.is_relative_to(base):
            raise ValueError("Invalid storage path")

        return path

    @staticmethod
    def finalize(
        temp_path: Path,
        final_path: Path,
    ) -> None:
        temp_path.replace(final_path)

    @staticmethod
    def delete(
        path: Path,
    ) -> None:
        path.unlink(missing_ok=True)
