# AI Knowledge & Research Assistant

![alt text](<AI Knowledge & Research Assistant.png>)

## 1. Project Overview

The project is a **Unified AI Knowledge & Research Assistant**.

The main idea is to combine two types of AI applications into one system:

1. **Knowledge Assistant**
   - General AI chat
   - PDF upload
   - Chat with uploaded documents
   - Semantic document search
   - RAG-based answers
   - Source citations

2. **Research & Automation Assistant**
   - Web search
   - Research generation
   - Tool/function calling
   - Multi-step AI workflows
   - Email actions
   - Conversation memory

Instead of creating a simple chatbot that only sends a prompt to an LLM, the application gives the AI access to **external knowledge, documents, databases, memory and tools**.

The overall system can be described as:

```text
User
  ↓
Next.js Frontend
  ↓
FastAPI Backend
  ↓
AI Orchestration Layer
  │
  ├── General LLM
  ├── PDF RAG
  ├── Web Search
  ├── Research Tool
  ├── Email Tool
  └── Conversation Memory
```

---

# 2. Main Objective

The purpose of the project is to create an assistant that can determine **where it should get information from**.

For example:

```text
User: "Explain Apache Kafka."
```

The AI can answer using its normal knowledge.

But:

```text
User: "According to the PDF I uploaded, what were the main conclusions?"
```

The application retrieves relevant sections from that PDF and sends them to the AI.

And:

```text
User: "Research the latest developments in Apache Spark."
```

the system can use the web-search tool.

And:

```text
User: "Email this summary to xyz@gmail.com."
```

the AI can trigger the email tool.

So instead of having several separate applications, we created one architecture capable of handling multiple AI workflows.

---

# 3. Technology Stack

## Frontend

### Next.js

The frontend is developed using:

```text
Next.js 16
React 19
TypeScript
```

Next.js provides the web application structure while React handles the interactive user interface.

The frontend contains the main chat interface where users can:

- Enter questions
- View AI responses
- Upload PDF files
- See source references
- Start a new conversation
- Interact with the assistant

### Tailwind CSS

Tailwind CSS is used for styling.

It allows us to create the responsive chat interface without maintaining large separate CSS files.

---

# 4. Backend

The backend is implemented in:

```text
Python
FastAPI
```

FastAPI acts as the application's API layer.

For example:

```text
Frontend
   ↓
POST /api/chat
   ↓
FastAPI
```

or:

```text
Frontend
   ↓
POST /api/upload-pdf
   ↓
FastAPI
```

FastAPI was selected because it works very well with Python-based AI libraries and provides:

- Fast API development
- Request validation
- Pydantic models
- Automatic Swagger documentation
- Async support
- Easy integration with AI services

The backend listens on:

```text
localhost:8000
```

while the frontend runs on:

```text
localhost:3000
```

---

# 5. LLM Layer

The application uses a Gemini model through an OpenAI-compatible interface.

The architecture is:

```text
FastAPI
   ↓
OpenAI-compatible Python SDK
   ↓
Google Gemini API
```

This is useful because the backend can use the familiar OpenAI-style chat-completions interface while Gemini provides the actual model.

The LLM is responsible for:

- Understanding questions
- Generating responses
- Deciding whether tools are required
- Summarizing web research
- Generating RAG answers
- Processing tool results
- Producing final natural-language answers

---

# 6. AI Agent / Tool Calling

One of the most important features of this project is **tool calling**.

A normal chatbot works like:

```text
User
 ↓
LLM
 ↓
Answer
```

Our application can work like:

```text
User
 ↓
LLM
 ↓
Decide whether a tool is required
 ↓
Call tool
 ↓
Get tool result
 ↓
Send result back to LLM
 ↓
Generate final answer
```

The model is not manually told:

> Always search the web.

Instead, tools are described to the model.

The model can decide whether a particular request requires one.

This is the beginning of an **agent-style architecture**.

---

# 7. Multi-Step Tool Workflow

The system supports multiple tool-call iterations.

For example:

```text
User:
"Research AI agents and summarize the findings."
```

Workflow:

```text
1. User sends request

2. LLM analyses request

3. LLM selects web/research tool

4. Tavily searches the internet

5. Search results return to backend

6. Results are sent back to LLM

7. LLM creates structured summary

8. Sources are returned with response

9. Frontend displays answer + sources
```

The code limits tool iterations to avoid an infinite agent loop.

Conceptually:

```text
MAX_TOOL_ITERATIONS = 5
```

So the AI can perform several actions but cannot continue indefinitely.

---

# 8. Web Search

For live web research, the application uses:

```text
Tavily Search API
```

Tavily is designed for AI-oriented search.

Instead of simply returning a collection of links, it can return information such as:

```text
Title
URL
Content
```

Example workflow:

```text
User:
"What are the latest developments in vector databases?"

            ↓

Gemini identifies that fresh information is needed

            ↓

Tavily Search

            ↓

Search results

            ↓

Gemini processes results

            ↓

Final summarized answer

            ↓

Source links displayed
```

An important principle here is that the model is instructed not to invent sources.

---

# 9. Research Assistant

There is also a dedicated research workflow.

The research service performs:

```text
Topic
 ↓
Tavily Search
 ↓
Collect sources
 ↓
Combine relevant content
 ↓
Send context to LLM
 ↓
Generate structured research report
```

The research output is organized into sections such as:

```text
Overview
Key Points
Common Use Cases
Conclusion
```

The AI is instructed to generate the report using the retrieved sources rather than simply relying on its internal knowledge.

---

# 10. PDF Knowledge Assistant

Another major feature is document intelligence.

The user can upload a PDF through the frontend.

The PDF does not simply get sent directly to the LLM.

It passes through an ingestion pipeline.

The pipeline is:

```text
PDF Upload
    ↓
FastAPI
    ↓
PyMuPDF
    ↓
Text extraction
    ↓
Page-based text
    ↓
Chunking
    ↓
Embeddings
    ↓
PostgreSQL + pgvector
```

---

# 11. Why PDF Chunking Is Required

LLMs cannot efficiently search an entire large document every time a user asks a question.

Therefore the document is divided into smaller sections called **chunks**.

For example:

```text
PDF = 50 pages
```

becomes:

```text
Chunk 1
Chunk 2
Chunk 3
...
Chunk 120
```

Our chunking configuration is approximately:

```text
Chunk size: 1000 characters
Overlap: 200 characters
```

The overlap is important.

Without overlap:

```text
Chunk 1:
"...the system uses"

Chunk 2:
"vector embeddings to..."
```

important context can be divided across chunk boundaries.

With overlap, some information from the previous chunk appears in the next chunk, reducing context loss.

---

# 12. PyMuPDF

PDF text extraction uses:

```text
PyMuPDF
```

It reads the PDF and extracts the text.

Our updated design also tracks:

```text
Page number
Chunk index
Filename
Document ID
```

This information is important because later we can return meaningful citations.

Instead of:

```text
Source: Chunk 76
```

we can return:

```text
Source:
architecture.pdf
Page 8
```

---

# 13. Embeddings

After chunks are created, each chunk is converted into an **embedding**.

The embedding model is:

```text
gemini-embedding-001
```

An embedding converts text into a numerical vector.

Conceptually:

```text
"Apache Kafka is a distributed event-streaming platform."
```

becomes something conceptually similar to:

```text
[
  0.023,
  -0.291,
  0.812,
  ...
]
```

The real embedding contains thousands of numerical dimensions.

These numbers represent the semantic meaning of the text.

This allows us to compare text based on **meaning**, instead of only matching exact words.

---

# 14. Why Embeddings Matter

Consider this PDF sentence:

```text
"Kafka allows applications to process continuous event streams."
```

The user asks:

```text
"How does Kafka handle real-time data?"
```

A traditional exact keyword search may struggle because the wording is different.

Semantic search understands that:

```text
continuous event streams
```

and:

```text
real-time data
```

have related meanings.

This is why embeddings are useful.

---

# 15. PostgreSQL

The project uses:

```text
PostgreSQL
```

as the primary relational database.

The document data is organized into two logical entities.

## documents

Stores document-level information:

```text
id
filename
content_type
total_pages
total_chunks
created_at
```

For example:

```text
id: 4
filename: kafka-guide.pdf
total_pages: 32
total_chunks: 79
```

## document_chunks

Stores the searchable parts of the document:

```text
id
document_id
page_number
chunk_index
chunk_text
embedding
created_at
```

The relationship is:

```text
documents
     │
     │ one-to-many
     ▼
document_chunks
```

One document can contain many chunks.

---

# 16. pgvector

PostgreSQL itself is a relational database.

To perform vector similarity search we use:

```text
pgvector
```

pgvector adds support for vector data types and similarity operations inside PostgreSQL.

Instead of introducing another database such as Pinecone or Weaviate, the project can use PostgreSQL for both:

```text
Relational metadata
+
Vector embeddings
```

This keeps the architecture relatively simple.

---

# 17. Semantic Vector Search

When the user asks a question about a PDF:

```text
"What security controls does the document recommend?"
```

the application first converts the question into an embedding.

```text
Question
   ↓
Embedding model
   ↓
Query vector
```

Then pgvector compares that vector against stored document chunk vectors.

Conceptually:

```text
Question Vector
      ↓
Compare against
      ↓
Chunk 1 vector
Chunk 2 vector
Chunk 3 vector
...
```

The closest chunks are retrieved.

The SQL operation uses vector distance:

```text
embedding <=> query_vector
```

The chunks with the smallest semantic distance are considered the most relevant.

---

# 18. RAG

This architecture is called:

# Retrieval-Augmented Generation

or:

```text
RAG
```

RAG has two main stages:

```text
Retrieval
+
Generation
```

### Retrieval

Find relevant information from the document.

```text
Question
 ↓
Embedding
 ↓
pgvector
 ↓
Relevant chunks
```

### Generation

Give those chunks to the LLM.

```text
Question
+
Retrieved chunks
 ↓
LLM
 ↓
Grounded answer
```

The complete workflow is:

```text
User asks PDF question
        ↓
Generate question embedding
        ↓
Search pgvector
        ↓
Retrieve top relevant chunks
        ↓
Construct context
        ↓
Send context + question to Gemini
        ↓
Generate answer
        ↓
Return answer + PDF citations
```

---

# 19. Why RAG Instead of Fine-Tuning?

RAG is more appropriate here because uploaded documents can constantly change.

With fine-tuning, changing information would potentially require training again.

With RAG:

```text
New PDF
 ↓
Extract
 ↓
Embed
 ↓
Store
```

and it immediately becomes searchable.

We do not need to retrain the LLM.

This makes RAG particularly suitable for:

- Company documentation
- Policies
- Research papers
- User manuals
- Reports
- Internal knowledge bases

---

# 20. Document Isolation

Every uploaded PDF receives a:

```text
document_id
```

For example:

```text
Document 1 → HR Policy.pdf
Document 2 → AWS Architecture.pdf
Document 3 → Project Proposal.pdf
```

When the user is chatting with Document 2, vector search can filter:

```text
WHERE document_id = 2
```

This prevents information from unrelated PDFs from mixing together.

That is an important improvement over putting every PDF chunk into one undifferentiated vector collection.

---

# 21. PDF Citations

The RAG response also returns metadata.

For example:

```json
{
  "filename": "AWS-Architecture.pdf",
  "page_number": 12,
  "chunk_index": 21
}
```

The frontend can therefore display:

```text
AWS-Architecture.pdf — Page 12
```

This improves:

- Explainability
- Trust
- Verification
- User experience

The user can understand where the answer came from instead of receiving an unsupported AI answer.

---

# 22. Conversation History

The application uses:

```text
Redis
```

to maintain chat history.

Each browser conversation has a:

```text
session_id
```

The history is stored using a key similar to:

```text
chat:<session_id>
```

For example:

```text
chat:53fd9c42...
```

Inside Redis:

```text
[
    User message,
    Assistant response,
    User message,
    Assistant response
]
```

---

# 23. Why Redis?

Redis is an in-memory data store.

It is useful for temporary application state because it is extremely fast.

Conversation history does not necessarily need expensive persistent relational storage for every request.

The flow becomes:

```text
User sends message
      ↓
session_id
      ↓
FastAPI
      ↓
Redis
      ↓
Load previous conversation
      ↓
Send history + new message to LLM
      ↓
Get response
      ↓
Save updated history in Redis
```

This allows follow-up questions.

Example:

```text
User:
"Explain Kafka."

AI:
"Kafka is..."

User:
"What are its main components?"
```

The second request makes sense because the previous conversation is supplied to the model.

---

# 24. Graceful Redis Failure

The Redis service includes connection-error handling.

If Redis temporarily becomes unavailable, the application can still continue operating without conversation memory instead of completely failing.

That improves resilience.

---

# 25. Email Tool

Email sending is implemented using:

```text
SMTP
```

with Gmail-compatible configuration.

Typical configuration:

```text
SMTP server:
smtp.gmail.com

Port:
587

Encryption:
STARTTLS
```

The email workflow is:

```text
User:
"Email this summary to abc@gmail.com."

        ↓

LLM identifies email action

        ↓

send_email tool

        ↓

SMTP

        ↓

Gmail server

        ↓

Recipient receives email
```

An important design principle is that ordinary questions should **not automatically send email**.

Email is treated as an explicit action.

---

# 26. Tool Selection

The LLM receives definitions of available tools.

Conceptually:

```text
Available tools:

search_web(...)
research_topic(...)
send_email(...)
...
```

The user does not manually select:

```text
Tool = Search
```

Instead the LLM receives the request and decides.

Example:

```text
"What is Apache Spark?"
```

could be answered normally.

Whereas:

```text
"What happened with Apache Spark this week?"
```

requires fresh information, so the AI can select search.

And:

```text
"Email that summary."
```

requires the email tool.

This is one of the differences between an **AI chatbot** and a simple **AI agent architecture**.

---

# 27. Frontend and Backend Communication

The frontend communicates with FastAPI using HTTP APIs.

For normal chat:

```text
POST /api/chat
```

Request conceptually:

```json
{
  "session_id": "abc123",
  "message": "Explain the uploaded document",
  "document_id": 4
}
```

If:

```text
document_id = null
```

the system follows the normal AI/tool workflow.

If:

```text
document_id = 4
```

the system uses RAG for that document.

This provides a simple routing mechanism.

---

# 28. Chat Routing Logic

The backend can conceptually do:

```text
                Incoming message
                       │
                       ▼
              Is document_id set?
                 /           \
               Yes            No
                │              │
                ▼              ▼
              RAG       Agent + Tools
                │              │
                ▼              ▼
             Gemini          Gemini
                \              /
                 \            /
                  ▼          ▼
                    Response
```

This means we can support different AI workflows behind one chat interface.

---

# 29. Docker

The whole application is containerized using:

```text
Docker
Docker Compose
```

Instead of manually installing and starting every component:

```text
Python
Node.js
PostgreSQL
Redis
pgvector
```

Docker provides isolated containers.

The application currently has four major containers:

```text
ai-frontend
ai-backend
rag-postgres
rag-redis
```

---

# 30. Docker Architecture

```text
Docker Compose
│
├── ai-frontend
│     Next.js
│     Port 3000
│
├── ai-backend
│     FastAPI
│     Port 8000
│
├── rag-postgres
│     PostgreSQL + pgvector
│     Port 5432
│
└── rag-redis
      Redis
      Port 6379
```

Docker Compose creates an internal Docker network automatically.

Therefore the backend can communicate with PostgreSQL using:

```text
postgres:5432
```

and Redis using:

```text
redis:6379
```

instead of using localhost.

Inside Docker:

```text
localhost
```

means the current container itself.

That is why service names are used for container-to-container communication.

---

# 31. PostgreSQL Persistence

PostgreSQL uses a Docker volume.

Conceptually:

```text
PostgreSQL Container
       ↓
Docker Volume
       ↓
Persistent database files
```

Therefore:

```bash
docker compose down
```

removes containers but keeps database data.

Whereas:

```bash
docker compose down -v
```

removes the volume as well.

That means the database is reset.

---

# 32. Database Initialization

A production-quality improvement is to maintain the schema as an initialization or migration script.

For example:

```text
init.sql
```

which creates:

```text
vector extension
documents table
document_chunks table
indexes
```

Then a fresh PostgreSQL instance can initialize automatically.

For a larger production system, we would normally use migration tooling rather than manually creating schemas.

---

# 33. Current Logical Architecture

The system can be summarized like this:

```text
                         USER
                           │
                           ▼
                  Next.js / React UI
                           │
                           ▼
                       FastAPI
                           │
          ┌────────────────┼──────────────────┐
          │                │                  │
          ▼                ▼                  ▼
     General AI           RAG               Tools
          │                │                  │
          │          Question Embedding       │
          │                │             ┌────┼─────┐
          │                ▼             │    │     │
          │           PostgreSQL         ▼    ▼     ▼
          │            pgvector        Web  Email Research
          │                │             │
          │                ▼             │
          │          Relevant Chunks     │
          │                │             │
          └────────────┬───┴─────────────┘
                       ▼
                     Gemini
                       │
                       ▼
                    Response
                       │
                       ▼
                    Frontend


                     Redis
                       ▲
                       │
                 Chat History
```

---

# 34. PDF Ingestion Architecture

Separately, before a PDF can be searched, it goes through:

```text
PDF
 │
 ▼
Upload endpoint
 │
 ▼
PyMuPDF
 │
 ▼
Extract text page-by-page
 │
 ▼
Chunk text
 │
 ▼
Embedding model
 │
 ▼
Vector representation
 │
 ▼
PostgreSQL / pgvector
 │
 ▼
Searchable knowledge base
```

This process is normally called:

```text
Document ingestion
```

---

# 35. Query-Time RAG Architecture

After ingestion:

```text
Question
 │
 ▼
Embedding model
 │
 ▼
Question vector
 │
 ▼
pgvector similarity search
 │
 ▼
Top relevant document chunks
 │
 ▼
Prompt/context construction
 │
 ▼
Gemini
 │
 ▼
Grounded answer
 │
 ▼
Document citations
```

The key concept is:

> We are not asking Gemini to memorize the PDF. We retrieve the relevant PDF content at query time and provide it to Gemini as context.

---

# 36. Difference Between Database, Redis and Vector Storage

This is a useful manager question.

We use each technology for a different responsibility.

### PostgreSQL

Longer-term structured application data:

```text
Documents
Document metadata
Chunks
```

### pgvector

Semantic retrieval:

```text
Embeddings
Vector similarity
```

### Redis

Fast temporary state:

```text
Conversation history
Session context
```

They are not duplicates.

Each solves a different problem.

---

# 37. Why FastAPI + Next.js?

We separated frontend and backend intentionally.

## Next.js

Responsible for:

```text
UI
User interaction
PDF selection
Chat display
Source display
```

## FastAPI

Responsible for:

```text
Business logic
AI requests
RAG
Database
Redis
External APIs
Tool execution
```

This separation means the AI logic remains server-side.

API keys and database credentials should never be exposed to the browser.

---

# 38. Environment Variables

Sensitive or environment-specific values are loaded through environment variables.

Examples:

```text
OPENAI_API_KEY
TAVILY_API_KEY
DATABASE_URL
REDIS_HOST
REDIS_PORT
SMTP_USERNAME
SMTP_PASSWORD
```

This separates configuration from application code.

We also maintain:

```text
.env.example
```

with variable names but no real secrets.

Actual credentials should never be committed to Git.

---

# 39. Security Design

Current security considerations include:

- API keys remain on backend
- Environment files excluded from Git
- Credentials are not sent to browser
- PDFs validated by MIME type
- Database access is server-side
- SMTP credentials remain server-side
- CORS controls permitted frontend origins

For production we can further add:

```text
Authentication
Authorization
Rate limiting
File-size limits
Malware scanning
HTTPS
IAM roles
AWS Secrets Manager
```

---

# 40. Error Handling

The project already considers several failure types.

For example:

### Redis failure

Chat can continue without history.

### Email authentication failure

SMTP returns a structured error.

### Invalid PDF

FastAPI rejects non-PDF uploads.

### Missing API key

Backend reports missing configuration.

### LLM provider availability

The application can receive provider errors such as rate limits or temporary service unavailability.

For production, retry logic and centralized logging would improve this further.

---

# 41. AWS Deployment Plan

The application is currently Dockerized, which makes cloud deployment easier.

The planned AWS architecture is:

```text
                         Internet
                            │
                            ▼
                       Load Balancer
                            │
                   ┌────────┴─────────┐
                   ▼                  ▼
             Frontend ECS       Backend ECS
                                      │
                     ┌────────────────┼─────────────┐
                     │                │             │
                     ▼                ▼             ▼
                   RDS               S3       Secrets Manager
              PostgreSQL
               + pgvector
                     │
                     ▼
                  Redis
             / ElastiCache

                    Logs
                     │
                     ▼
                CloudWatch
```

Container images would be stored in:

```text
Amazon ECR
```

and executed through:

```text
Amazon ECS Fargate
```

---

# 42. S3 Future Integration

Currently PDF processing occurs through the backend.

For the production AWS version, the original uploaded PDF can be stored in:

```text
Amazon S3
```

while searchable representations are stored in PostgreSQL.

So:

```text
Original file
    ↓
Amazon S3
```

and:

```text
Text chunks + embeddings + metadata
    ↓
RDS PostgreSQL + pgvector
```

This separation is appropriate because S3 is optimized for files and PostgreSQL is optimized for structured/searchable data.

---

# 43. CloudWatch

CloudWatch would provide centralized:

```text
Application logs
Container logs
Errors
Metrics
Monitoring
```

Instead of looking at local Docker terminal logs, we could inspect production logs centrally.

---

# 44. AWS Secrets Manager

Production credentials such as:

```text
Gemini API key
Tavily API key
Database credentials
SMTP credentials
```

should not be hardcoded into ECS configuration.

They can be stored in:

```text
AWS Secrets Manager
```

and provided securely to containers.

---

# 45. Key Features Delivered

The unified architecture demonstrates several important AI engineering concepts:

1. LLM integration
2. Prompt engineering
3. FastAPI APIs
4. React/Next.js frontend
5. PDF processing
6. Embeddings
7. Vector databases
8. Semantic search
9. Retrieval-Augmented Generation
10. Source citations
11. Tool calling
12. Web research
13. Multi-step agent workflows
14. Conversation memory
15. Email automation
16. PostgreSQL
17. Redis
18. Docker
19. Container networking
20. Cloud-ready architecture

---

# 46. What Makes This More Than a Basic Chatbot?

A normal chatbot is essentially:

```text
Prompt → LLM → Response
```

Our system is:

```text
                         User Request
                              │
                              ▼
                        AI Orchestrator
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
      Internal LLM       Knowledge Base      External Tools
                              │                  │
                         RAG / pgvector     Tavily / Email
           │                  │                  │
           └──────────────────┴──────────────────┘
                              │
                              ▼
                        Final Response
```

The key improvement is that the AI can access information and actions beyond its pretrained model knowledge.

---

# 47. Example Demo Flow

For the manager demo, I would present it in this order.

## Demo 1 — General Chat

Ask:

```text
Explain Apache Kafka in simple terms.
```

Explain:

> This request does not need our document knowledge base. The backend passes the conversation context to the LLM and returns the generated response.

---

## Demo 2 — Upload PDF

Upload a PDF.

Explain:

> When the PDF is uploaded, we extract its text page-by-page, divide the text into overlapping chunks, generate an embedding for every chunk and store those vectors in PostgreSQL using pgvector.

The frontend can display:

```text
PDF indexed successfully
Pages: 20
Chunks: 48
```

---

## Demo 3 — Chat With PDF

Ask:

```text
What are the three main recommendations in this document?
```

Explain:

> We don't send the entire document to the model. The question is converted into an embedding, pgvector retrieves the most semantically relevant chunks, and only those chunks are provided to the LLM.

Then show:

```text
Source:
document.pdf — Page 4
document.pdf — Page 7
```

---

## Demo 4 — Web Research

Ask:

```text
Research recent developments in AI agents.
```

Explain:

> The LLM determines that external up-to-date information is required. It calls the web-search/research tool, gets sources through Tavily, and generates a summarized answer based on those sources.

---

## Demo 5 — Follow-Up Question

Ask:

```text
What was the second point you mentioned?
```

Explain:

> We maintain conversation history in Redis using the session ID, so the model has context from previous messages.

---

## Demo 6 — Email Tool

Ask:

```text
Email this summary to example@example.com.
```

Explain:

> The LLM identifies an action rather than only a question. It invokes the email function, which sends the message through SMTP.

---

# 48. The Main Business Value

From a business perspective, the system can become an internal company knowledge assistant.

For example, employees could upload:

```text
Policies
SOPs
Technical documents
Reports
Contracts
Training materials
Project documentation
```

and ask questions naturally.

Instead of manually searching through dozens of documents:

```text
Employee
    ↓
Ask natural-language question
    ↓
Relevant internal knowledge
    ↓
AI-generated answer
    ↓
Source reference
```

The same assistant could also gather external research and perform selected actions.

---

# 49. Scalability Direction

The current project is a learning/prototype architecture, but it has a clear path toward production.

The next production improvements would be:

```text
S3 document storage
AWS RDS PostgreSQL
ECS Fargate
ECR
Secrets Manager
CloudWatch
Authentication
User-level document isolation
Database migrations
Retries and circuit breakers
Background ingestion jobs
Streaming responses
Slack integration
CI/CD with GitHub Actions
```

The fundamental architecture does not need to be thrown away.

The individual infrastructure components can be upgraded around the same application design.

---

# 50. Short Manager Summary

If I had to explain the whole project in around one minute, I would say:

> The project is a unified AI Knowledge and Research Assistant. It combines general LLM chat, document intelligence and AI tool calling in one application. The frontend is built with Next.js and React, while FastAPI handles the backend AI workflows. Users can upload PDFs, which are processed with PyMuPDF, divided into chunks and converted into semantic embeddings. Those embeddings are stored in PostgreSQL using pgvector. When a user asks a document-related question, we use Retrieval-Augmented Generation, or RAG, to semantically retrieve the most relevant chunks and provide them to Gemini before generating the answer, including document citations. For external information, the AI can call Tavily web search and generate structured research reports. Redis maintains conversation history, and the assistant can also invoke tools such as email when explicitly requested. The complete application is containerized using Docker, with separate frontend, backend, PostgreSQL and Redis services, and the architecture is designed to later deploy on AWS using ECS, RDS, S3, ECR, Secrets Manager and CloudWatch.

---

# 51. Most Important Technical Terms to Remember

### LLM
Large Language Model used to understand and generate language.

### Embedding
Numerical representation of the semantic meaning of text.

### Vector
The array of numbers produced by the embedding model.

### pgvector
PostgreSQL extension for storing and comparing vectors.

### Semantic Search
Searching based on meaning rather than exact keyword matches.

### RAG
Retrieve relevant information first, then provide it to the LLM to generate a grounded response.

### Chunking
Dividing large documents into smaller searchable pieces.

### Tool Calling
Allowing the LLM to request execution of external functions.

### Agent
An AI workflow where the model can reason about which actions/tools to use.

### Redis
Fast in-memory store used here for conversation/session history.

### FastAPI
Python backend API framework.

### Next.js
React-based frontend framework.

### Tavily
Search API used by the AI for web research.

### PyMuPDF
Library used to extract PDF text.

### Docker
Packages services and dependencies into isolated containers.

### Docker Compose
Starts and connects all application containers together.

---

# 52. One-Line Architecture

The easiest sentence to remember is:

> **Next.js provides the interface, FastAPI orchestrates the workflows, Gemini provides intelligence, Tavily provides live web knowledge, PyMuPDF processes documents, Gemini embeddings convert document text into vectors, PostgreSQL with pgvector performs semantic retrieval, Redis maintains conversation context, and Docker packages the complete system.**