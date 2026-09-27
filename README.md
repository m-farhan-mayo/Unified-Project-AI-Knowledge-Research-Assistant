"# 🤖 AI Knowledge & Research Assistant

Our project is basically an **AI assistant that can chat, understand PDFs, search the web, perform research, remember conversations, use tools, and send results by email.**

The final local architecture is:

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │   Next.js   │
                    │  Frontend   │
                    │    :3000    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    │   Backend   │
                    │    :8000    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌────────┐       ┌────────────┐      ┌────────┐
    │ Gemini │       │ PostgreSQL │      │ Redis  │
    │  LLM   │       │ + pgvector │      │        │
    └────────┘       └────────────┘      └────────┘
        │
        ├──────────► Tavily
        │
        └──────────► Gmail SMTP
```

---

# 1. Project Foundation ✅

First we created the basic application structure.

### Backend

We used:

* Python
* FastAPI
* Uvicorn
* Pydantic
* `.env`

### Frontend

We used:

* Next.js
* React
* TypeScript
* Tailwind CSS

We also established:

```text
Frontend → Backend API
```

and configured CORS so they could communicate.

---

# 2. Gemini LLM Integration ✅

We connected Gemini to the backend.

The application can send:

```text
System message
+
User message
+
Conversation history
```

to Gemini and receive an answer.

We used the OpenAI Python SDK with Google's OpenAI-compatible endpoint.

So the basic flow is:

```text
User
 ↓
FastAPI
 ↓
Gemini
 ↓
Answer
 ↓
Frontend
```

---

# 3. Chat UI ✅

We created the frontend chat interface.

It handles:

* User input
* Send button
* Loading state
* API requests
* JSON responses
* Displaying assistant responses
* Conversation interaction
* PDF upload UI

So the user doesn't need to interact directly with the API.

---

# 4. PDF Upload & Processing ✅

We added PDF processing.

The flow is:

```text
PDF
 ↓
FastAPI UploadFile
 ↓
Validation
 ↓
Temporary file
 ↓
PyMuPDF
 ↓
Extract text
 ↓
Split into chunks
```

Our current chunking:

```text
Chunk size = 1000 characters
Overlap    = 200 characters
```

Why?

Because we don't want to send an entire PDF to Gemini at once.

We break it into smaller pieces that can later be searched.

---

# 5. Embeddings ✅

After creating PDF chunks, we convert each chunk into a vector.

We use:

```text
gemini-embedding-001
```

Conceptually:

```text
PDF chunk
   ↓
Embedding model
   ↓
[0.12, -0.45, 0.87, ...]
```

That vector represents the semantic meaning of the text.

---

# 6. PostgreSQL + pgvector ✅

We added PostgreSQL with the `pgvector` extension.

Database:

```text
rag_db
```

Main table:

```text
document_chunks
```

The table stores:

```text
chunk_text
embedding
```

The embedding uses:

```text
vector(3072)
```

PostgreSQL is our **persistent storage**.

So:

```text
PDF
 ↓
Chunks
 ↓
Embeddings
 ↓
PostgreSQL
```

This data survives application/container restarts.

---

# 7. RAG ✅

Then we implemented **Retrieval-Augmented Generation**.

This is one of the most important parts of the project.

When the user asks something about an uploaded PDF:

```text
User Question
      ↓
Question Embedding
      ↓
Vector Search
      ↓
PostgreSQL + pgvector
      ↓
Top 3 relevant chunks
      ↓
Context
      ↓
Gemini
      ↓
Answer
```

So instead of expecting Gemini to already know your uploaded PDF, we retrieve relevant content and give it to Gemini.

---

# 8. Source Citations ✅

We added sources to the response.

The assistant can return information like:

```text
title
url
content
```

This allows the application to tell the user where information came from.

---

# 9. Conversation History ✅

Initially, conversation history was being maintained by the frontend.

We changed this architecture.

Now every conversation has:

```text
session_id
```

Example:

```json
{
  "session_id": "session_001",
  "message": "What is Kafka?"
}
```

The backend uses the session ID to retrieve previous conversation history.

This became especially important when we introduced Redis.

---

# 10. Tool / Function Calling ✅

We taught Gemini how to use tools.

Current tools include:

```text
get_user_info()
search_web()
research_topic()
send_email()
```

The important thing we learned is:

**Gemini doesn't directly execute Python.**

Instead:

```text
User
 ↓
Gemini
 ↓
"I need search_web"
 ↓
Python executes search_web()
 ↓
Tool result
 ↓
Gemini
 ↓
Final answer
```

This became the foundation of our agent architecture.

---

# 11. Web Search with Tavily ✅

We integrated Tavily.

When Gemini determines that a question requires current web information:

```text
User
 ↓
Gemini
 ↓
search_web()
 ↓
Tavily
 ↓
Search results
 ↓
Gemini
 ↓
Summary + Sources
```

So the assistant isn't limited to its built-in knowledge.

---

# 12. Research Workflow ✅

We created:

```text
research_service.py
```

This is different from simply doing one web search.

The workflow is:

```text
Research Topic
      ↓
Search Web
      ↓
Collect Sources
      ↓
Organize Information
      ↓
Gemini
      ↓
Structured Research Report
```

Current report structure:

```text
Overview
Key Points
Common Use Cases
Conclusion
```

And we exposed research as a tool that Gemini can call.

---

# 13. Agent Decision Making ✅

Now Gemini can decide what type of action is appropriate.

For example:

```text
"What is Python?"
        ↓
Direct answer
```

Whereas:

```text
"What happened in X recently?"
        ↓
Web search
```

And:

```text
"Research Apache Kafka and give me a structured report."
        ↓
Research workflow
```

So our architecture became:

```text
                    Gemini
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Answer        Search       Research

          └────────────┬────────────┘
                       ▼
                    Result
```

---

# 14. Email Integration ✅

We added Gmail SMTP.

Configuration:

```text
smtp.gmail.com
Port 587
STARTTLS
```

The application can send the generated answer/research through email.

Flow:

```text
Assistant Result
      ↓
send_email()
      ↓
Gmail SMTP
      ↓
User Email
```

We first tested this with a mock email function and then connected real Gmail SMTP.

We successfully tested email sending.

---

# 15. Multi-Tool Agent Workflow ✅

This was an important milestone.

We tested:

```text
Research Apache Kafka
+
Email me the result
```

The agent performed multiple operations:

```text
User
 ↓
Gemini
 ↓
research_topic()
 ↓
Tavily
 ↓
Research result
 ↓
Gemini
 ↓
send_email()
 ↓
Gmail
```

So the assistant isn't just a chatbot anymore.

It can **use multiple tools in one workflow.**

---

# 16. Authentication ⏭️ SKIPPED

We had planned basic authentication.

But you specifically decided to skip it because:

> This project is primarily for learning and understanding, not building a production SaaS application.

So:

```text
Authentication → SKIPPED
```

This was intentional.

---

# 17. Redis ✅

Then we introduced Redis.

We learned the difference between:

### PostgreSQL

Persistent storage:

```text
PDF chunks
Embeddings
RAG data
```

### Redis

Fast temporary/session storage:

```text
Chat history
Session state
```

---

## Redis Operations We Learned

We implemented and tested:

### Connection

```python
redis_client.ping()
```

### SET

```text
key → value
```

### GET

```text
key → value
```

### DELETE

```text
delete(key)
```

### TTL

Temporary data:

```text
set(key, value, ex=10)
```

After 10 seconds the key disappears.

### JSON

We stored Python lists/dictionaries as JSON.

### Session History

We created keys like:

```text
chat:session_001
```

---

# 18. Redis + Chat Integration ✅

We changed the chat architecture to:

```text
User
 ↓
Frontend
 ↓
Backend
 ↓
Redis
 ↓
Load history
 ↓
Gemini
 ↓
Answer
 ↓
Save updated history
 ↓
Redis
 ↓
Frontend
```

This allows follow-up questions.

For example:

```text
User:
What is Kafka?

Assistant:
Kafka is...

User:
What are its components?

Assistant:
Kafka's components are...
```

The second question works because the previous conversation is available through the session history.

---

# 19. Redis Error Handling ✅

We deliberately stopped Redis to see what would happen.

Initially:

```text
Redis unavailable
 ↓
ConnectionError
 ↓
Backend failure
```

We then added error handling.

Now:

```text
Redis unavailable
       ↓
load_history()
       ↓
None
       ↓
history = []
       ↓
Gemini can still answer
       ↓
save_history() returns False
```

So Redis is useful but the basic chat doesn't completely die if Redis is temporarily unavailable.

---

# 20. Docker ✅

Then we Dockerized the application.

We learned:

### Image

A packaged blueprint.

### Container

A running instance of that image.

So:

```text
Application
+
Dependencies
      ↓
Docker Image
      ↓
Container
```

And we learned that Docker is **not a hosting platform**.

---

# 21. Backend Dockerization ✅

We created:

```text
backend/Dockerfile
```

It uses:

```text
Python 3.12 slim
```

The Dockerfile:

```text
Python image
 ↓
WORKDIR /app
 ↓
Copy requirements
 ↓
Install dependencies
 ↓
Copy backend
 ↓
Run Uvicorn
```

Backend runs on:

```text
8000
```

---

# 22. Frontend Dockerization ✅

We created:

```text
frontend/Dockerfile
```

It uses:

```text
Node 22 Alpine
```

The process is:

```text
Node image
 ↓
WORKDIR
 ↓
npm ci
 ↓
Copy frontend
 ↓
npm run build
 ↓
npm start
```

Frontend runs on:

```text
3000
```

---

# 23. `.dockerignore` + Secrets ✅

We made sure `.env` is not copied into the Docker image.

Backend `.dockerignore` contains:

```text
.env
__pycache__
*.pyc
```

Frontend `.dockerignore` contains:

```text
node_modules
.next
.env
*.log
```

Secrets remain outside the image and are injected through environment variables.

Your root `.gitignore` also ignores:

```text
.env
backend/.env
```

---

# 24. Docker Compose ✅

Instead of manually managing each container, we created:

```text
docker-compose.yml
```

It manages:

```text
Backend
Frontend
PostgreSQL
Redis
```

Important:

**Compose does not combine them into one container.**

It manages multiple separate containers together.

---

# 25. Docker Internal Networking ✅

This was an important concept.

Inside Docker:

```text
Backend → Redis
```

uses:

```text
redis:6379
```

And:

```text
Backend → PostgreSQL
```

uses:

```text
postgres:5432
```

Because Docker Compose provides internal DNS using service names.

So:

```text
REDIS_HOST=redis
```

and:

```text
DATABASE_URL=...@postgres:5432/rag_db
```

are correct.

---

# 26. PostgreSQL Persistent Volume ✅

We already had PostgreSQL data before moving everything to Compose.

We therefore reused the existing external Docker volume.

We verified:

```text
document_chunks
```

still existed after recreating the PostgreSQL container.

So our RAG data survived the Docker transition.

This is very important:

```text
PostgreSQL Container
        ↓
External Volume
        ↓
RAG Data
```

The container can be recreated without losing the persistent database data, as long as the volume isn't deleted.

---

# 27. Full Docker Compose Application ✅

At this point everything is running together:

```text
┌───────────────────────────────────────┐
│           Docker Compose              │
│                                       │
│  ┌─────────────┐                      │
│  │  Frontend   │ :3000               │
│  └──────┬──────┘                      │
│         │                              │
│         ▼                              │
│  ┌─────────────┐                      │
│  │  Backend    │ :8000               │
│  └──────┬──────┘                      │
│         │                              │
│    ┌────┴────┐                         │
│    ▼         ▼                         │
│ PostgreSQL  Redis                      │
│  :5432      :6379                      │
│                                       │
└───────────────────────────────────────┘
```

Current containers:

```text
ai-frontend
ai-backend
rag-postgres
rag-redis
```

---

# 28. Final Docker Testing ✅

We tested the complete stack.

### Backend

```text
FastAPI starts
       ✅
```

### Frontend

```text
Next.js starts
       ✅
```

### PostgreSQL

```text
document_chunks exists
       ✅
```

### Redis

```text
chat:<session_id>
       ✅
```

### Chat

```text
Question → Answer
       ✅
```

### Follow-up

```text
Question 1
    ↓
Question 2
    ↓
Conversation context maintained
       ✅
```

### Email

```text
Assistant → Gmail
       ✅
```

### Restart

We tested:

```bash
docker compose down
docker compose up -d
```

All four services came back:

```text
ai-backend     → Up
ai-frontend    → Up
rag-postgres   → Up
rag-redis      → Up
```

Then we tested the chat again.

**Passed.** ✅

---

# 🏁 Where We Are Now

Our project currently looks like this:

```text
                         AI ASSISTANT
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
        Chat                 RAG                Agent
          │                   │                   │
          │              PDF + Vector       Tool Calling
          │                   │                   │
          │              PostgreSQL        ┌──────┼──────┐
          │                pgvector         │      │      │
          │                                 Web  Research Email
          │
          ▼
       Redis
   Conversation
      History
```

And the whole thing is now running inside Docker Compose.

---

# 📊 Overall Progress

| Phase                               | Status     |
| ----------------------------------- | ---------- |
| 1. Project Foundation               | ✅          |
| 2. Gemini + Basic Chat              | ✅          |
| 3. Next.js Chat UI                  | ✅          |
| 4. PDF Processing                   | ✅          |
| 5. Embeddings + PostgreSQL/pgvector | ✅          |
| 6. Basic RAG                        | ✅          |
| 7. Sources + Conversation History   | ✅          |
| 8. Tool Calling                     | ✅          |
| 9. Web Search                       | ✅          |
| 10. Research Agent                  | ✅          |
| 11. Email Integration               | ✅          |
| 12. Multi-Tool Agent                | ✅          |
| 13. Authentication                  | ⏭️ Skipped |
| 14. Redis + Error Handling          | ✅          |
| 15. Docker + Compose                | ✅          |
| **16. AWS Deployment**              | ⏳          |

## 🚀 Next

The only major part left in our agreed roadmap is:

**Phase 16 — AWS Deployment**

Planned architecture:

```text
                    AWS
                     │
          ┌──────────┴──────────┐
          │                     │
       Frontend              Backend
                                │
                         ECS Fargate
                                │
             ┌──────────────────┼─────────────────┐
             │                  │                 │
            RDS                S3              Redis*
       PostgreSQL
        + pgvector
             │
             ▼
          RAG Data

Supporting:
ECR              → Docker images
Secrets Manager  → Secrets
CloudWatch       → Logs
IAM              → Permissions
GitHub Actions   → CI/CD
