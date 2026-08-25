## File Upload Architecture

                          Upload File
                             │
                             ▼
                  Check Request/File Size
                             │
                             ▼
                     Check File Extension
                             │
                             ▼
                Validate Actual File Content
                             │
                             ▼
                 Check Filename in PostgreSQL
                       /               \
                      /                 \
                 Exists                 New
                    │                    │
                    ▼                    ▼
                   409              Stream Upload
                                         │
                                         ▼
                                  Temporary File
                                         │
                                         ▼
                                    SHA-256
                                         │
                                         ▼
                                  Content Hash
                                         │
                                         ▼
                          Check Content Duplicate
                                /          \
                               /            \
                          Exists            New
                             │                │
                             ▼                ▼
                            409           Insert DB
                                              │
                                      ┌───────┴────────┐
                                      │                │
                                  Success        IntegrityError
                                      │                │
                                      ▼                ▼
                                   Commit           Rollback
                                      │                │
                                      ▼                ▼
                              Temp → Final       Delete Temp
                                      │
                                      ▼
                               Upload Success

## Multiple File Upload Architecture (later)

                         POST /documents
                               │
                               ▼
                         FastAPI Route
                               │
                               ▼
                       Document Service
                               │
                               ▼
                        Check File Count
                               │
                         ┌─────┴─────┐
                         │           │
                      ≤ 5 Files    > 5 Files
                         │           │
                         ▼           ▼
                  Process Files    Reject Request
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
            File 1     File 2     File N
              │          │          │
              ▼          ▼          ▼
        ┌─────────────────────────────────┐
        │     Same File Upload Flow       │
        │                                 │
        │  1. Check Size                  │
        │  2. Check Extension             │
        │  3. Validate Content            │
        │  4. Check Filename              │
        │  5. Stream to Temporary File    │
        │  6. Calculate SHA-256           │
        │  7. Check Content Duplicate     │
        │  8. Insert DB                   │
        │  9. Commit / Rollback           │
        │ 10. Finalize File               │
        └─────────────────────────────────┘
              │          │          │
              ▼          ▼          ▼
           Success    Success     Failed
              │          │          │
              ▼          ▼          ▼
          Finalize    Finalize    Cleanup
              │          │          │
              └──────────┼──────────┘
                         ▼
                   Batch Response
                         │
                  ┌──────┴──────┐
                  │             │
               Uploaded       Failed
                  │             │
                  ▼             ▼
             File Details    Error Details

## Outbox Architecture

                    PostgreSQL
                        │
                        │
               documents (outbox)
                        │
                        ▼
                   Celery Beat
                every 1-5 minutes
                        │
                        ▼
              publish_outbox_events
                        │
                        ▼
                      Redis
                        │
                        ▼
                 Celery Worker
                        │
                        ▼
                ingest_document

## Document Processing Architecture

                    ┌──────────────────┐
                    │       API        │
                    │  Upload Document │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    PostgreSQL    │
                    │                  │
                    │    documents     │
                    │ ingestion_jobs   │ (later)
                    │                  │
                    │ status = PENDING │
                    └────────┬─────────┘
                             │
                             │ Every 1 minute
                             ▼
                    ┌──────────────────┐
                    │    Celery Beat   │
                    │    Scheduler     │
                    └────────┬─────────┘
                             │
                             │ fetch pending jobs
                             ▼
                    ┌──────────────────┐
                    │  Publisher Task  │
                    │  / Dispatcher    │
                    └────────┬─────────┘
                             │
                             │ enqueue job
                             ▼
                    ┌──────────────────┐
                    │   Celery Queue   │
                    │       Redis      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Ingestion Worker │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Extractor│ → │  Chunker │ → │  Embedder│
        └──────────┘   └──────────┘   └─────┬────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ document_chunks │
                                   │   + embedding   │
                                   └────────┬────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │     pgvector    │
                                   └─────────────────┘

## RAG Retrieval Pipeline

                    Current Query
                         │
                         ▼
                Conversation Memory
                  (summary + recent) (later)
                         │
                         ▼
                   Query Rewrite (later)
                         │
                         ▼
                  Vector Retrieval
                         │
                         ▼
                    Reranker
                         │
                         ▼
                 Top 3-5 chunks
                         │
                         ▼
                      LLM
                         │
                         ▼
                 Persistence Lock (later)
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
          USER message          ASSISTANT
                                    │
                                 citations
                                    │
                                  COMMIT
