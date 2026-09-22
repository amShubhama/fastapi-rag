FROM python:3.14.2-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# libreoffice is required to convert DOC to DOCX
# Install 'libreoffice-core' and 'libreoffice-writer' to keep the image lightweight
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libmagic1 \
    libreoffice \
    && soffice --version \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install -r requirement.txt

COPY . .

RUN mkdir -p /app/storage/documents /app/storage/.tmp

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]