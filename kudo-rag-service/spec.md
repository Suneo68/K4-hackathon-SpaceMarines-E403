# Specification: `kudo-rag-service`

## Project Description
`kudo-rag-service` is a real-time Retrieval-Augmented Generation (RAG) Discord Assistant for the AI20K community. It automates knowledge vectorization from specified channels and provides grounded answers with source citations using `gemini-2.5-flash`.

## Core Features
1. **Automated Vector Ingestion**: Real-time listening on `#thông-báo`, `#tài-nguyên`, `#bài-học`, `#lý-thuyết` channels to extract and upsert message content with metadata into ChromaDB.
2. **Context Retrieval**: Retrieve top-k semantic matches using `text-embedding-004`.
3. **Grounded Generation**: Prompt `gemini-2.5-flash` with retrieved context and strict rules requiring citation link insertion.
4. **Discord Bot Interface**: Handle channel events, commands, and `@mention` message triggers.

## Quality Bar
- **Accuracy & Grounding**: High relevance accuracy; answers strictly derived from fetched contexts. Hallucinations avoided via prompt engineering constraints.
- **Latency**: End-to-end question answering response under 5 seconds.
- **Metadata Integrity**: Citations must include valid `jump_url`, author handle, and channel title.
- **Maintainability**: Fully typed codebase with modular package separation.

## Risk Scenarios
- **API Rate Limits**: High volume of message events exhausting Discord gateway or Gemini API quotas.
- **Irrelevant Context**: Low similarity scores returning noise; fallback strategy required.
- **Stale Embeddings**: Updated or deleted Discord messages requiring index updates.
- **Permission Errors**: Bot missing channel read/write permissions in sandbox or production guilds.
