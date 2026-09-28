import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from transformers import BitsAndBytesConfig

# Global State
index = None
query_engine = None
DATA_DIR = "data"

def initialize_rag():
    global index, query_engine
    print("Loading Models... This might take a minute on Colab/GPU.")
    
    os.makedirs(DATA_DIR, exist_ok=True)

    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-mpnet-base-v2")
    
    system_prompt = """You are an expert educational AI assistant. 
    You must strictly follow the user's instructions and format your output exactly as requested."""
    query_wrapper_prompt = PromptTemplate("<|USER|>{query_str}<|ASSISTANT|>")
    
    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    
    llm = HuggingFaceLLM(
        context_window=4096,
        max_new_tokens=1500,
        generate_kwargs={"temperature": 0.1, "do_sample": False},
        system_prompt=system_prompt,
        query_wrapper_prompt=query_wrapper_prompt,
        tokenizer_name="meta-llama/Llama-2-7b-chat-hf",
        model_name="meta-llama/Llama-2-7b-chat-hf",
        device_map="auto",
        model_kwargs={"quantization_config": quantization_config},
    )

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 100

    existing_files = os.listdir(DATA_DIR)
    if len(existing_files) > 0:
        docs = SimpleDirectoryReader(DATA_DIR).load_data()
        index = VectorStoreIndex.from_documents(docs)
    else:
        index = VectorStoreIndex.from_documents([])
        
    query_engine = index.as_query_engine(similarity_top_k=3)
    print("RAG Engine is ready!")

def update_index(new_docs):
    global index, query_engine
    for doc in new_docs:
        index.insert(doc)
    query_engine = index.as_query_engine(similarity_top_k=3)
