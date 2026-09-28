import os
import json
import re
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from llama_index.core import SimpleDirectoryReader

from app.schemas.quiz import QuizRequest
from app.core import engine

router = APIRouter()

@router.post("/upload-document/")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    file_path = os.path.join(engine.DATA_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    print(f"Processing new document: {file.filename}")
    new_docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
    
    # Engine ko update karne ke liye call
    engine.update_index(new_docs)
    
    return {"message": f"Successfully uploaded and indexed {file.filename}", "chunks_added": len(new_docs)}


@router.post("/generate-quiz/")
async def generate_quiz(req: QuizRequest):
    if engine.query_engine is None:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized.")
        
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
    
    response = engine.query_engine.query(quiz_prompt)
    raw_output = str(response)
    
    try:
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if json_match:
            clean_json = json_match.group(0)
            quiz_data = json.loads(clean_json)
            return {"status": "success", "data": quiz_data}
        else:
            return {"status": "success", "data": json.loads(raw_output)}
            
    except Exception:
        print("Raw Output:", raw_output)
        return {
            "status": "error", 
            "message": "LLM did not return valid JSON. See raw output.", 
            "raw_output": raw_output
        }
