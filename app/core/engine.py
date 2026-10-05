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
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from pypdf import PdfReader

# Global State
index = None
query_engine = None
qdrant_client = None
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
    selected_model = model_name or "models/gemini-2.5-flash"
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

    # 3. Vector Database Connection (Qdrant Cloud or Local Storage fallback)
    global qdrant_client
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "quiz_collection")

    if qdrant_url and qdrant_api_key:
        print(f"Connecting to Qdrant Cloud Vector Database ({collection_name})...")
        qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        async_qdrant_client = AsyncQdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            aclient=async_qdrant_client,
            collection_name=collection_name
        )

        has_collection = qdrant_client.collection_exists(collection_name)
        points_count = 0
        if has_collection:
            try:
                coll_info = qdrant_client.get_collection(collection_name)
                points_count = coll_info.points_count or 0
            except Exception:
                points_count = 0

        if force_reindex and has_collection:
            print(f"Force re-index requested: clearing collection '{collection_name}' in Qdrant...")
            qdrant_client.delete_collection(collection_name)
            has_collection = False
            points_count = 0

        if not has_collection:
            from qdrant_client.http.models import VectorParams, Distance
            print(f"Creating Qdrant collection '{collection_name}' with 384-dim Cosine vectors...")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            has_collection = True

        if has_collection and points_count > 0:
            print(f"Loading existing vector index from Qdrant Cloud ({points_count} points)...")
            index = VectorStoreIndex.from_vector_store(vector_store)
        else:
            print(f"Scanning '{DATA_DIR}' to build vector index in Qdrant Cloud...")
            docs = load_documents_from_directory(DATA_DIR)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            if docs:
                print(f"Indexing {len(docs)} documents into Qdrant collection '{collection_name}'...")
                index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)
                print("Vector index built and persisted in Qdrant Cloud successfully!")
            else:
                print("No documents found in 'data/' folder. Initialized empty Qdrant collection.")
                index = VectorStoreIndex.from_documents([], storage_context=storage_context)

    else:
        # Fallback to local storage
        print("Using local vector storage (storage/ folder)...")
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
    if os.path.exists(STORAGE_DIR) and not os.getenv("QDRANT_URL"):
        index.storage_context.persist(persist_dir=STORAGE_DIR)
    query_engine = index.as_query_engine(similarity_top_k=3)
    print(f"Index updated! Now contains dynamic knowledge from new documents.")

def get_vector_db_stats():
    """Returns vector database status and metrics."""
    global qdrant_client
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "quiz_collection")
    if qdrant_url and qdrant_api_key:
        try:
            client = qdrant_client or QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            coll_info = client.get_collection(collection_name)
            return {
                "type": "Qdrant Cloud",
                "collection": collection_name,
                "points_count": coll_info.points_count,
                "status": coll_info.status.value if hasattr(coll_info.status, "value") else str(coll_info.status),
                "cluster_url": qdrant_url,
            }
        except Exception as e:
            return {"type": "Qdrant Cloud", "error": str(e)}
    return {"type": "Local Disk (JSON)", "path": STORAGE_DIR}
