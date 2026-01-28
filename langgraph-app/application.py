"""
Application wrapper para deploy do LangGraph Server no Elastic Beanstalk.
Cria servidor FastAPI que expõe os endpoints do LangGraph.
"""
import os
import sys
from pathlib import Path

# Adicionar diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

# Modo produção: criar servidor FastAPI que expõe os endpoints do LangGraph
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import uuid

app = FastAPI(title="LangGraph Server", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, configurar origens específicas via variável de ambiente
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar e configurar o grafo
try:
    from agent.graph_chat import graph
    GRAPH_LOADED = True
except Exception as e:
    print(f"ERRO ao carregar grafo: {e}")
    GRAPH_LOADED = False

@app.get("/")
async def root():
    return {"service": "LangGraph Server", "status": "running", "graph_loaded": GRAPH_LOADED}

@app.get("/health")
async def health():
    return {"status": "healthy", "graph_loaded": GRAPH_LOADED}

# Endpoints do LangGraph Server API (compatível com LangSmith Studio)
@app.post("/assistants/search")
async def search_assistants():
    """Endpoint para buscar assistentes (compatível com LangSmith Studio)"""
    return [{
        "assistant_id": "agent",
        "name": "agent",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }]

@app.post("/threads")
async def create_thread(request: Request):
    """Criar thread e processar mensagem"""
    if not GRAPH_LOADED:
        return JSONResponse(
            status_code=500,
            content={"error": "Graph not loaded"}
        )
    
    try:
        data = await request.json()
        messages = data.get("input", {}).get("messages", [])
        if not messages:
            return JSONResponse(
                status_code=400,
                content={"error": "No messages provided"}
            )
        
        # Converter mensagens para formato LangChain
        from langchain_core.messages import HumanMessage
        
        langchain_messages = []
        for msg in messages:
            if msg.get("role") == "user":
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
        
        # Executar grafo (injetar backend_url para regras de handoff virem do backend/S3)
        config = {}
        if os.getenv("BACKEND_URL"):
            config["configurable"] = {"backend_url": os.getenv("BACKEND_URL").strip().rstrip("/")}
        result = graph.invoke({"messages": langchain_messages}, config=config if config else None)
        
        # Converter resultado para formato de resposta
        response_messages = []
        for msg in result.get("messages", []):
            if hasattr(msg, "content"):
                response_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        thread_id = str(uuid.uuid4())
        return {
            "thread_id": thread_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "values": {
                "messages": response_messages
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Exportar app para gunicorn/uvicorn (necessário para EB)
application = app

if __name__ == "__main__":
    # Para desenvolvimento local
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
