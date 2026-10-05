import os
import shutil
from dotenv import load_dotenv
load_dotenv(override=True)

from llama_index.core import (
    VectorStoreIndex,
    Settings,
    StorageContext,
    load_index_from_storage,
    Document,
)
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pypdf import PdfReader

# Global State
index = None
query_engine = None
DATA_DIR = "data"
STORAGE_DIR = "storage"

def extract_pdf_documents(file_path: str):
    """Cleanly extracts actual text page-by-page from any PDF file."""
    docs = []
    filename = os.path.basename(file_path)
    try:
        reader = PdfReader(file_path)
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                docs.append(
                    Document(
                        text=text,
                        metadata={
                            "file_name": filename,
                            "page_number": page_idx + 1,
                            "total_pages": len(reader.pages),
                        },
                    )
                )
    except Exception as e:
        print(f"Error extracting PDF {filename}: {e}")
    return docs

def load_documents_from_directory(directory: str):
    """Dynamically scans directory and loads any PDFs or text files cleanly."""
    documents = []
    if not os.path.exists(directory):
        return documents

    for fname in os.listdir(directory):
        fpath = os.path.join(directory, fname)
        if fname.lower().endswith(".pdf"):
            docs = extract_pdf_documents(fpath)
            documents.extend(docs)
        elif fname.lower().endswith((".txt", ".md")):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content.strip():
                        documents.append(Document(text=content, metadata={"file_name": fname}))
            except Exception as e:
                print(f"Error loading {fname}: {e}")
    return documents

def initialize_rag(force_reindex: bool = False, top_k: int = 3, model_name: str = None):
    global index, query_engine
    print(">>> Initializing Dynamic RAG Engine...")

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(STORAGE_DIR, exist_ok=True)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY is not set in environment or .env file!")

    # 1. Embedding Model (Local CPU model, 100% free, 0 rate limits)
    print("Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 2. Google Gemini LLM
    selected_model = model_name or "models/gemini-3.5-flash"
    if not selected_model.startswith("models/"):
        selected_model = f"models/{selected_model}"

    print(f"Connecting to Google Gemini LLM ({selected_model})...")
    llm = Gemini(
        model_name=selected_model,
        api_key=api_key,
        temperature=0.2,
    )

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 100

    # 3. Check if cached index exists and is valid (re-index if forced or empty)
    storage_has_files = os.path.exists(STORAGE_DIR) and len(os.listdir(STORAGE_DIR)) > 0

    if storage_has_files and not force_reindex:
        try:
            print("Loading cached vector index from storage...")
            storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
            index = load_index_from_storage(storage_context)
        except Exception as e:
            print(f"Cached index corrupted or unreadable ({e}). Rebuilding clean index...")
            force_reindex = True

    if force_reindex or not storage_has_files or index is None:
        print(f"Scanning '{DATA_DIR}' for all documents to build vector index...")
        docs = load_documents_from_directory(DATA_DIR)
        if len(docs) > 0:
            print(f"Cleanly extracted {len(docs)} page/text documents. Building vector index...")
            index = VectorStoreIndex.from_documents(docs)
            index.storage_context.persist(persist_dir=STORAGE_DIR)
            print("Vector index built and persisted successfully!")
        else:
            print("No documents found in 'data/' folder. Initialized empty vector index.")
            index = VectorStoreIndex.from_documents([])

    query_engine = index.as_query_engine(similarity_top_k=top_k)
    print(f">>> RAG Engine is READY (similarity_top_k={top_k})! <<<")
    return query_engine

def update_index(new_docs):
    """Dynamically adds new documents to the vector index in real-time."""
    global index, query_engine
    if index is None:
        initialize_rag()
    for doc in new_docs:
        index.insert(doc)
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    query_engine = index.as_query_engine(similarity_top_k=3)
    print(f"Index updated! Now contains dynamic knowledge from new documents.")
