from dotenv import load_dotenv
load_dotenv(override=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import router
from app.core import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # App start hote hi RAG engine load karega
    engine.initialize_rag()
    yield

app = FastAPI(title="RAG Quiz Generator API", version="1.0.0", lifespan=lifespan)

# API Routes ko attach karna
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        limit_concurrency=300,
        timeout_keep_alive=30
    )


