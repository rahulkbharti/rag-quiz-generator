import os
from dotenv import load_dotenv
load_dotenv(override=True)

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Global State
index = None
query_engine = None
DATA_DIR = "data"
STORAGE_DIR = "storage"

def initialize_rag():
    global index, query_engine
    print(">>> Initializing RAG Engine...")

    os.makedirs(DATA_DIR, exist_ok=True)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY is not set in environment or .env file!")

    # 1. Superfast, quota-free local embedding model (80MB, runs smoothly on CPU, NO rate limits)
    print("Loading fast embedding model (all-MiniLM-L6-v2)...")
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 2. Google Gemini LLM for fast quiz generation
    print("Connecting to Google Gemini LLM...")
    llm = Gemini(
        model_name="models/gemini-2.5-flash",
        api_key=api_key,
        temperature=0.1
    )

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 100

    # 3. Load from storage if already indexed (Instant load!), else create index
    if os.path.exists(STORAGE_DIR) and len(os.listdir(STORAGE_DIR)) > 0:
        print("Loading cached vector index from storage (instant startup)...")
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)
    else:
        pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf")]
        if len(pdf_files) > 0:
            print(f"Indexing {len(pdf_files)} PDF(s) from '{DATA_DIR}' and caching to '{STORAGE_DIR}'...")
            docs = SimpleDirectoryReader(DATA_DIR, required_exts=[".pdf"]).load_data()
            index = VectorStoreIndex.from_documents(docs)
            index.storage_context.persist(persist_dir=STORAGE_DIR)
            print("Indexing completed and cached successfully!")
        else:
            print("No existing PDFs found. Initialized empty index ready for uploads.")
            index = VectorStoreIndex.from_documents([])

    query_engine = index.as_query_engine(similarity_top_k=3)
    print(">>> RAG Engine with Gemini is READY! <<<")

def update_index(new_docs):
    global index, query_engine
    for doc in new_docs:
        index.insert(doc)
    # Persist updated index to storage
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    query_engine = index.as_query_engine(similarity_top_k=3)



