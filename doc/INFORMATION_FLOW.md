# 🔄 Complete RAG & Financial Audit Information Flow

Yeh document hamare **RAG Quiz & Chat Backend** ke information flow, data movement, aur financial telemetry ka complete visual diagram provide karta hai.

---

## 1. High-Level Architectural Flow

```mermaid
flowchart TD
    %% Styling
    classDef client fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#ffffff;
    classDef localFree fill:#10b981,stroke:#047857,stroke-width:2px,color:#ffffff;
    classDef cloudPaid fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#ffffff;
    classDef storage fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#ffffff;
    classDef audit fill:#ec4899,stroke:#be185d,stroke-width:2px,color:#ffffff;

    subgraph UserLayer ["👤 User & Client Interfaces"]
        U1["📄 Document Upload (PDF)"]:::client
        U2["💬 Query / Quiz Request"]:::client
    end

    subgraph IngestionPipeline ["📥 Phase 1: Ingestion & Indexing (100% Free / ₹0)"]
        direction TB
        P1["PDF Parser (pypdf)\nClean page-by-page text"]:::localFree
        P2["Text Chunker\n1024 chunk size, 100 overlap"]:::localFree
        P3["Local Embedding Model\nall-MiniLM-L6-v2 (CPU / 80MB)"]:::localFree
        P4[("Disk Storage\n./storage (Vector Index)")]:::storage
        
        P1 --> P2 --> P3 --> P4
    end

    subgraph RetrievalPipeline ["🔍 Phase 2: Vector Retrieval (100% Free / ₹0)"]
        direction TB
        Q1["User Query Text"]:::client
        Q2["Query Embedding\nall-MiniLM-L6-v2 (CPU)"]:::localFree
        Q3["Cosine Similarity Match\nSearch in ./storage"]:::localFree
        Q4["Top-K Relevant Chunks\n(e.g., 3 Chunks)"]:::localFree
        
        Q1 --> Q2 --> Q3 --> Q4
    end

    subgraph LLMInference ["🧠 Phase 3: LLM Inference (Google Gemini Cloud)"]
        direction TB
        L1["Prompt Synthesizer\nSystem Prompt + Chunks + Query"]:::cloudPaid
        L2["Pre-flight Tokenizer\nclient.models.count_tokens()"]:::localFree
        L3["Google Gemini Cloud LLM\n(gemini-3.5-flash / gemini-2.5-flash)"]:::cloudPaid
        L4["Thinking / Reasoning Process\n(Internal thoughts tokens)"]:::cloudPaid
        L5["Candidate Answer Generation\n(Markdown Output)"]:::cloudPaid

        L1 --> L2 --> L3 --> L4 --> L5
    end

    subgraph AuditPipeline ["💰 Phase 4: Financial Audit & Telemetry"]
        direction TB
        A1["Metadata Extraction\n(Input, Output, Thinking Tokens)"]:::audit
        A2["Dynamic Pricing Catalog\n(Flash / Lite / Pro, <=128k vs >128k)"]:::audit
        A3["Currency Conversion\n(USD to INR @ ₹86.00)"]:::audit
        A4["Rich CLI / API Display\n(Turn Cost + Cumulative Session Bill)"]:::audit

        A1 --> A2 --> A3 --> A4
    end

    %% Cross-phase connections
    U1 --> P1
    U2 --> Q1
    P4 -.->|Reads cached index| Q3
    Q4 --> L1
    L5 --> A1
    A4 -->|Rendered to| U2
```

---

## 2. Sequence Diagram: Step-by-Step Data Movement

Yeh sequence diagram har request ke exact lifecycle ko chronologically dikhata hai:

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User / CLI
    participant Engine as ⚙️ RAG Engine (Local)
    participant LocalEmbed as 🧮 Local Embedder (MiniLM)
    participant Storage as 💾 Disk (./storage)
    participant Gemini as ☁️ Google Gemini API
    participant Auditor as 💰 Financial Auditor

    Note over User, Storage: Phase 1: Document Indexing (One-Time - ₹0 Cost)
    User->>Engine: Upload / Scan PDF in data/
    Engine->>Engine: Extract clean text per page (pypdf)
    Engine->>LocalEmbed: Send chunks for embedding
    LocalEmbed-->>Engine: Return 384-dimensional dense vectors (₹0 CPU)
    Engine->>Storage: Persist VectorStoreIndex to ./storage

    Note over User, Auditor: Phase 2: Live Query & Financial Audit (Real-Time)
    User->>Engine: Input question ("UNITS AND MEASUREMENT ke 5 question")
    
    par 1. Pre-flight Check & Vector Search
        Engine->>Gemini: Pre-flight count_tokens(question) [₹0 Cost]
        Gemini-->>Engine: Returns input question tokens
    and
        Engine->>LocalEmbed: Embed query question
        LocalEmbed-->>Engine: Query vector (₹0 Cost)
        Engine->>Storage: Cosine similarity vector search
        Storage-->>Engine: Return Top-K relevant text chunks (₹0 Cost)
    end

    Note over Engine, Gemini: Phase 3: Prompt Construction & LLM Inference
    Engine->>Engine: Assemble Prompt = [Context Chunks + Question]
    Engine->>Gemini: generate_content(model, assembled_prompt)
    Gemini->>Gemini: Generate thinking reasoning tokens
    Gemini-->>Engine: Response Text + usage_metadata

    Note over Engine, Auditor: Phase 4: Financial Audit Calculation
    Engine->>Auditor: Send metadata (prompt_tokens, candidate_tokens, thoughts_tokens)
    Auditor->>Auditor: Resolve dynamic rate for model ($0.075 / $0.30 per 1M)
    Auditor->>Auditor: Calculate USD cost & Convert to INR (@ ₹86.00)
    Auditor-->>User: Display Formatted Answer + Rich Financial Audit Box
```

---

## 3. Cost Attribution Matrix (Kis Step me Kitna Kharcha?)

```mermaid
pie title Cost Distribution per RAG Query (Typical Query = ~₹0.015)
    "Document Retrieval (Local Disk)" : 0
    "Query Vectorization (Local CPU)" : 0
    "Storage Access (Local File)" : 0
    "Gemini Input Tokens (Prompt + Chunks)" : 35
    "Gemini Thinking / Reasoning Tokens" : 45
    "Gemini Output Candidate Tokens" : 20
```

---

## 4. Key Architectural Insights

1. **Zero-Cost Storage & Retrieval**:
   - Vector database local disk (`./storage`) me in-process chalta hai.
   - Retrieval ke liye kisi cloud provider (jaise Pinecone ya Weaviate) ko subscription nahi dena padta.
2. **Local CPU Embeddings (`all-MiniLM-L6-v2`)**:
   - 80MB ka compact model server ke CPU/RAM par chalta hai.
   - 0 API latency, 0 rate limits, aur 0 cost.
3. **Pay-As-You-Go LLM Generation**:
   - Bill sirf aur sirf **Google Gemini LLM** API calls ka banta hai.
   - Flash model ke sath typical query ka kharcha sirf **1 se 2 paise (₹0.01 – ₹0.02)** hota hai.
