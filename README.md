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

## Multiple File Upload Architecture

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

## Document Processing Architecture

                    ┌───────────────┐
                    │   FastAPI     │
                    │   Upload API  │
                    └───────┬───────┘
                            │
                ┌───────────┼────────────┐
                │           │            │
                ▼           ▼            ▼
            PostgreSQL    Storage       Queue
                │           │            │
            documents       │            │
            ingestion_jobs  │            │
                            │            │
                            └──────┬─────┘
                                   │
                                   ▼
                              Ingestion
                                Worker
                                   │
                  ┌────────────────┼─────────────────┐
                  │                │                 │
                  ▼                ▼                 ▼
              Extractor         Chunker          Embedder
                  │                │                 │
                  └────────────────┼─────────────────┘
                                   │
                                   ▼
                            document_chunks
                                   │
                                   ▼
                              pgvector

### API → Queue → Worker → Extract → Chunk → Embed → pgvector
