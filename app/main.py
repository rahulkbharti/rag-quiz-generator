from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.api.routes import router
from app.core import engine

app = FastAPI(title="RAG Quiz Generator API", version="1.0.0")

# API Routes ko attach karna
app.include_router(router)

@app.on_event("startup")
def startup_event():
    # App start hote hi ML engine load karega
    engine.initialize_rag()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
