AI Knowledge & Research Assistant — Progress Review

Our original goal is to combine LLM + Basic RAG + AI Agent/Tool Calling + Research Automation + AWS deployment into one project.

We are following:

Project → Phase → Step → Test → Next Step

and we're staying within the agreed scope.

Phase 1 — Project Foundation ✅
What we did
Created the project structure
Created Python virtual environment
Set up FastAPI
Set up Next.js
Set up React + Tailwind
Connected frontend → backend
Configured CORS
Added .env
Protected secrets with .gitignore
Initialized Git and made the first commit
What you learned
FastAPI basics
API endpoints
Next.js/React basics
Frontend/backend communication
HTTP requests
Environment variables
Why API keys should not be committed
Basic Git workflow
Phase 2 — LLM + Basic Chat ✅
What we did

We connected Gemini through its OpenAI-compatible API.

Our setup:

Next.js
   ↓
FastAPI
   ↓
OpenAI Python SDK
   ↓
Gemini API
   ↓
Gemini 3.8 Flash

We created:

llm_service.py

and implemented:

client.chat.completions.create()
What you learned
What an LLM is
How an API call works
OpenAI-compatible APIs
messages
system
user
LLM responses
Pydantic request validation
HTTP 422 validation errors
Phase 3 — Next.js + Tailwind Chat UI ✅
What we did

Built the basic chat interface:

Input
Send button
AI response
Loading state

Connected it to:

POST /api/chat
What you learned
React useState
Event handlers
fetch()
JSON requests/responses
Loading state
Frontend → API communication
Phase 4 — PDF Upload + Processing ✅
What we did

Implemented:

PDF
 ↓
Next.js
 ↓
FastAPI UploadFile
 ↓
Temporary file
 ↓
PyMuPDF
 ↓
Extracted text
 ↓
Chunks

We tested this with a real PDF.

What you learned
PDF is binary data
multipart/form-data
FormData
FastAPI UploadFile
PDF text extraction
PyMuPDF
Text chunking
Chunk size
Chunk overlap

Current chunking:

chunk size = 1000 characters
overlap = 200 characters
Phase 5 — Embeddings + PostgreSQL/pgvector ✅

This was one of the most important phases.

What we did

Installed:

google-genai
psycopg

Used:

gemini-embedding-001

Flow:

PDF text
   ↓
Chunks
   ↓
Embedding model
   ↓
Vectors
   ↓
PostgreSQL + pgvector

We created:

document_chunks

with:

id
chunk_text
embedding vector(3072)

We stored the actual PDF chunks and embeddings.

Then implemented semantic search:

Question
   ↓
Question embedding
   ↓
pgvector
   ↓
Cosine distance
   ↓
Most relevant chunks
What you learned
What embeddings are
Text → vector
Semantic meaning represented by vectors
Embedding models vs LLMs
Vector databases
PostgreSQL + pgvector
Cosine distance
Lower distance = more similar
Semantic search
Phase 6 — Basic RAG ✅

Then we connected everything together.

Our RAG flow became:

User Question
      ↓
Embedding
      ↓
Vector Search
      ↓
Top 3 Chunks
      ↓
Context
      ↓
Gemini
      ↓
Final Answer

We created:

rag_service.py

and implemented:

answer_with_rag()

We tested it with:

What cloud platforms does Farhan have experience with?

and it correctly retrieved relevant resume chunks and generated the answer.

What you learned

Most importantly:

RAG does not make the LLM learn the document.

Instead:

Question
 ↓
Retrieve relevant information
 ↓
Put information into prompt
 ↓
LLM generates answer

You also learned the difference between:

Retrieved source text
vs
LLM-generated final answer

Phase 7 — Source Citations + Conversation History ✅

This phase is now complete.

Source Citations

We changed retrieval from simply:

chunks = [row[1] for row in results]

to preserving:

chunk_id
text
distance

Then returned:

{
  "answer": "...",
  "sources": [
    "Document Chunk 4",
    "Document Chunk 2",
    "Document Chunk 5"
  ]
}
What you learned
Backend already knows which chunks were retrieved
Don't ask the LLM to invent source IDs
Source IDs should come from the database
Distance can be used internally for relevance
Sources can be exposed separately from the answer
Conversation History

We changed:

message

into:

message + history

Example:

{
  "message": "Who provides it?",
  "history": [
    {
      "role": "user",
      "content": "What is Azure?"
    },
    {
      "role": "assistant",
      "content": "Azure is a cloud computing platform."
    }
  ]
}

The backend builds:

System message
      ↓
Previous messages
      ↓
Current message
      ↓
Gemini

And the frontend now maintains:

messages
What you learned
Why LLMs don't automatically remember previous messages
Conversation history is just a list of messages
role = user
role = assistant
Follow-up questions depend on context
React can maintain the conversation state
Backend sends the history to the LLM

You successfully tested:

What is Azure?
        ↓
Who provides it?
        ↓
Microsoft

So Phase 7 = COMPLETE ✅

Phase 8 — Tool / Function Calling 🚧 CURRENT

We're currently here.

What we've done
Step 1 — Understand Function Calling ✅

You learned:

LLM decides which tool is needed; backend actually executes the tool.

Step 2 — Created a Python Tool ✅

Created:

tools.py

with:

def get_user_info(name: str):
    return f"The user's name is {name}."
Step 3 — Defined Tool for Gemini ✅

Created:

get_tools()

which tells Gemini:

Tool:
get_user_info

Parameter:
name
Step 4 — Gemini Tool Selection ✅

Gemini successfully returned:

get_user_info

with:

name = Farhan

So Gemini understood:

"I need this tool to answer the question."

Step 5 — Backend Tool Execution ✅

We created:

execute_tool()

which takes Gemini's request and executes:

get_user_info("Farhan")
Step 6 — Tested Execution ✅

We successfully got:

The user's name is Farhan.
Step 7 — Complete Tool Calling Cycle ✅

We connected everything:

User
 ↓
Gemini
 ↓
Tool Call
 ↓
Python Function
 ↓
Tool Result
 ↓
Gemini
 ↓
Final Answer

And your test successfully returned a natural-language response.

What You Have Learned Overall

At this point, you've covered a large portion of the core AI application architecture.

You understand:

LLM
API calls
Prompting
FastAPI
React
Next.js
PDF processing
Chunking
Embeddings
Vector databases
pgvector
Semantic search
RAG
Source citations
Conversation history
Function calling
Tool definitions
Tool execution
Agent-like tool flow

And more importantly, you have actually implemented and tested these concepts rather than just reading about them.

Remaining Project Plan

Now we continue with the original agreed scope.

✅ Phase 1  — Project Foundation
✅ Phase 2  — LLM + Basic Chat
✅ Phase 3  — Next.js + Tailwind Chat UI
✅ Phase 4  — PDF Upload + Processing
✅ Phase 5  — Embeddings + PostgreSQL/pgvector
✅ Phase 6  — Basic RAG
✅ Phase 7  — Source Citations + Conversation History

🚧 Phase 8  — Tool / Function Calling
   ├── ✅ Understand function calling
   ├── ✅ Create Python tool
   ├── ✅ Define tool
   ├── ✅ Gemini selects tool
   ├── ✅ Execute tool
   ├── ✅ Send result to Gemini
   └── ⏭️ Tool selection testing

⬜ Phase 9  — Web Search + AI Summarization
⬜ Phase 10 — Research Workflow + Basic Agent Architecture
⬜ Phase 11 — Slack + Email
⬜ Phase 12 — Redis + Error Handling
⬜ Phase 13 — Basic Authentication (Optional)
⬜ Phase 14 — Docker
⬜ Phase 15 — AWS Deployment
The bigger picture

Eventually your application will look like:

                         ┌── PDF → Embeddings → pgvector
                         │
User → Next.js → FastAPI ├── RAG
                         │
                         ├── Web Search
                         │
                         ├── Slack
                         │
                         └── Email
                                ↓
                             Gemini
                                ↓
                         Final Response

And the agent architecture will eventually allow Gemini to decide:

"What does this question require?"

        ↓

RAG?
Web Search?
Slack?
Email?
No tool?

But we will not jump there yet.

Current exact position

Phase 8 → Step 8: Tool Selection Testing

We'll test that Gemini can correctly distinguish:

"What is Farhan's name?"
        ↓
Use tool

vs.

"What is Python?"
        ↓
No tool needed

That will give you a proper understanding of tool selection before we move to the real Web Search tool in Phase 9.