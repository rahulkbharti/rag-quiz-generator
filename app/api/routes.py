import os
import json
import re
import shutil
import time
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from llama_index.core import SimpleDirectoryReader

from app.schemas.quiz import QuizRequest
from app.core import engine

router = APIRouter()

# High-Concurrency Controls
MAX_CONCURRENT_LLM_CALLS = 30
llm_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)

# In-Memory Cache: {(topic, num_questions): (data, timestamp)}
QUIZ_CACHE = {}
CACHE_TTL_SECONDS = 900  # 15 minutes TTL

@router.post("/upload-document/")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    file_path = os.path.join(engine.DATA_DIR, file.filename)
    
    # Run synchronous file writing in threadpool to keep event loop free
    loop = asyncio.get_running_loop()
    def save_and_index():
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"Processing new document: {file.filename}")
        new_docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
        engine.update_index(new_docs)
        return len(new_docs)

    chunks_added = await loop.run_in_executor(None, save_and_index)
    
    # Invalidate cache when new knowledge is uploaded
    QUIZ_CACHE.clear()
    
    return {
        "message": f"Successfully uploaded and indexed {file.filename}",
        "chunks_added": chunks_added
    }


@router.post("/generate-quiz/")
async def generate_quiz(req: QuizRequest):
    if engine.query_engine is None:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized.")

    cache_key = (req.topic.strip().lower(), req.num_questions)
    current_time = time.time()

    # 1. Fast Path: Check in-memory cache (serves in <2 milliseconds for concurrent users)
    if not req.refresh and cache_key in QUIZ_CACHE:
        cached_data, cached_at = QUIZ_CACHE[cache_key]
        if current_time - cached_at < CACHE_TTL_SECONDS:
            return {
                "status": "success",
                "source": "cache",
                "data": cached_data
            }

    quiz_prompt = f"""
    You are an expert quiz generator. Based ONLY on the provided context, generate {req.num_questions} multiple-choice questions focusing on the topic of "{req.topic}". 
    
    You MUST output strictly in JSON format. Do not write any explanations before or after the JSON.
    Format your response EXACTLY like this array:
    [
      {{
        "question": "Question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "explanation": "Explanation here based on context."
      }} 
    ]
    """

    # 2. Concurrency-Controlled Async Query
    async with llm_semaphore:
        response = await engine.query_engine.aquery(quiz_prompt)
        raw_output = str(response)

    try:
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if json_match:
            clean_json = json_match.group(0)
            quiz_data = json.loads(clean_json)
        else:
            quiz_data = json.loads(raw_output)

        # Store in cache
        QUIZ_CACHE[cache_key] = (quiz_data, current_time)

        return {"status": "success", "source": "generated", "data": quiz_data}
            
    except Exception:
        print("Raw Output:", raw_output)
        return {
            "status": "error", 
            "message": "LLM did not return valid JSON. See raw output.", 
            "raw_output": raw_output
        }

