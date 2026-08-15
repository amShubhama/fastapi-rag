from pathlib import Path
import zipfile
import magic


from src.core.exceptions import InvalidDocumentError


class DocumentValidator:
    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
    }

    EXPECTED_MIME_TYPES = {
        ".pdf": {
            "application/pdf",
        },
        ".doc": {
            "application/msword",
            "application/x-ole-storage",
        },
        ".docx": {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/zip",
        },
        ".txt": {
            "text/plain",
        },
    }

    MAX_FILENAME_LENGTH = 255
    MAX_TEXT_SAMPLE_SIZE = 1024 * 1024

    @classmethod
    def validate_filename(cls, filename: str | None) -> str:
        if not filename:
            raise InvalidDocumentError("Filename is required.")

        filename = Path(filename).name.strip()

        if not filename:
            raise InvalidDocumentError("Invalid filename.")

        if len(filename) > cls.MAX_FILENAME_LENGTH:
            raise InvalidDocumentError("Filename is too long.")

        if "\x00" in filename:
            raise InvalidDocumentError("Filename contains invalid characters.")

        return filename

    @classmethod
    def get_extension(cls, filename: str) -> str:
        extension = Path(filename).suffix.lower()

        if extension not in cls.ALLOWED_EXTENSIONS:
            raise InvalidDocumentError(
                "Unsupported document type. "
                "Allowed types are PDF, DOC, DOCX and TXT."
            )

        return extension

    @classmethod
    def validate(
        cls,
        path: Path,
        filename: str,
    ) -> str:
        extension = cls.get_extension(filename)

        if not path.exists():
            raise InvalidDocumentError("Uploaded file could not be found.")

        if not path.is_file():
            raise InvalidDocumentError("Uploaded object is not a file.")

        if path.stat().st_size == 0:
            raise InvalidDocumentError("Empty files are not allowed.")

        detected_mime = cls._detect_mime_type(path)

        cls._validate_mime_type(
            extension=extension,
            detected_mime=detected_mime,
        )

        if extension == ".pdf":
            cls._validate_pdf(path)

        elif extension == ".doc":
            cls._validate_doc(path)

        elif extension == ".docx":
            cls._validate_docx(path)

        elif extension == ".txt":
            cls._validate_txt(path)

        return detected_mime

    @staticmethod
    def _detect_mime_type(path: Path) -> str:
        try:
            detected_mime = magic.from_file(
                str(path),
                mime=True,
            )
        except Exception as exc:
            raise InvalidDocumentError("Unable to determine file type.") from exc

        if not detected_mime:
            raise InvalidDocumentError("Unable to determine file type.")

        return detected_mime.lower()

    @classmethod
    def _validate_mime_type(
        cls,
        extension: str,
        detected_mime: str,
    ) -> None:
        expected_types = cls.EXPECTED_MIME_TYPES[extension]

        if detected_mime not in expected_types:
            raise InvalidDocumentError(
                f"File extension '{extension}' does not "
                f"match its actual content type."
            )

    @staticmethod
    def _validate_pdf(path: Path) -> None:
        try:
            with path.open("rb") as file:
                header = file.read(5)

            if header != b"%PDF-":
                raise InvalidDocumentError("Invalid PDF file.")

            with path.open("rb") as file:
                file.seek(0, 2)
                file_size = file.tell()

                if file_size < 8:
                    raise InvalidDocumentError("Invalid PDF file.")

                read_size = min(file_size, 4096)

                file.seek(-read_size, 2)

                tail = file.read(read_size)

            if b"%%EOF" not in tail:
                raise InvalidDocumentError("Invalid or incomplete PDF file.")

        except OSError as exc:
            raise InvalidDocumentError("Unable to validate PDF file.") from exc

    @staticmethod
    def _validate_doc(path: Path) -> None:
        expected_header = bytes.fromhex("D0CF11E0A1B11AE1")

        try:
            with path.open("rb") as file:
                header = file.read(8)

        except OSError as exc:
            raise InvalidDocumentError("Unable to validate DOC file.") from exc

        if header != expected_header:
            raise InvalidDocumentError("Invalid DOC file.")

    @staticmethod
    def _validate_docx(path: Path) -> None:
        try:
            if not zipfile.is_zipfile(path):
                raise InvalidDocumentError("Invalid DOCX file.")

            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise InvalidDocumentError("DOCX archive is corrupted.")

                names = set(archive.namelist())

        except zipfile.BadZipFile as exc:
            raise InvalidDocumentError("Invalid DOCX file.") from exc

        except OSError as exc:
            raise InvalidDocumentError("Unable to validate DOCX file.") from exc

        required_files = {
            "[Content_Types].xml",
            "_rels/.rels",
            "word/document.xml",
        }

        missing_files = required_files - names

        if missing_files:
            raise InvalidDocumentError("Invalid DOCX document structure.")

    @classmethod
    def _validate_txt(cls, path: Path) -> None:
        try:
            with path.open("rb") as file:
                sample = file.read(cls.MAX_TEXT_SAMPLE_SIZE)

        except OSError as exc:
            raise InvalidDocumentError("Unable to read text file.") from exc

        if b"\x00" in sample:
            raise InvalidDocumentError(
                "File contains binary data and is not a valid text document."
            )

        try:
            sample.decode("utf-8")

        except UnicodeDecodeError:
            try:
                sample.decode("utf-8-sig")

            except UnicodeDecodeError as exc:
                raise InvalidDocumentError(
                    "Text file must contain valid UTF-8 text."
                ) from exc
