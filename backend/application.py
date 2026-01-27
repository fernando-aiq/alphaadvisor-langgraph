from flask import Flask, jsonify, request
from flask_cors import CORS
from app.routes import chat, oportunidades, alertas, assessor, cliente, configuracoes, conexoes, health, trace_visualization, painel_agente, agent_builder, auth, langgraph_server
import os
import sys

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Preservar acentos (ex: João, Olá) no JSON

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verificar configuração LangSmith no startup
def check_langsmith_config():
    """Verifica e loga status da configuração LangSmith"""
    api_key = os.getenv('LANGSMITH_API_KEY')
    if api_key:
        try:
            from langsmith import Client
            client = Client(api_key=api_key)
            project = os.getenv('LANGSMITH_PROJECT', 'alphaadvisor')
            logger.info(f"[Startup] LangSmith configurado - Projeto: {project}")
            logger.info("[Startup] Tracing automático habilitado para LangGraph e AgentExecutor")
            return True
        except ImportError:
            logger.warning("[Startup] LangSmith não instalado (pip install langsmith)")
            return False
        except Exception as e:
            logger.warning(f"[Startup] Erro ao configurar LangSmith: {e}")
            return False
    else:
        logger.info("[Startup] LangSmith não configurado (LANGSMITH_API_KEY não encontrada)")
        logger.info("[Startup] Para habilitar tracing, configure LANGSMITH_API_KEY no .env")
        return False

# Executar verificação no import
check_langsmith_config()

# Configurar CORS para permitir requisições do frontend Vercel e LangSmith Studio
frontend_url = os.getenv('FRONTEND_URL', 'https://alphaadvisor.vercel.app')

def is_allowed_origin(origin):
    """
    Verifica se uma origem é permitida para CORS.
    Aceita subdomínios do LangChain e Vercel dinamicamente.
    """
    if not origin:
        return False
    
    # Lista de origens fixas permitidas
    fixed_origins = [
        frontend_url,
        'https://alphaadvisor.vercel.app',
        'http://localhost:3000',
        'http://localhost:3001',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://localhost:8123',
        'http://127.0.0.1:8123',
        'https://smith.langchain.com',
        'https://studio.langchain.com',
        'https://api.smith.langchain.com',
    ]
    
    if origin in fixed_origins:
        return True
    
    # Aceitar qualquer subdomínio do langchain.com
    if origin.endswith('.langchain.com') and origin.startswith('https://'):
        return True
    
    # Aceitar qualquer subdomínio do langgraph.app
    if origin.endswith('.langgraph.app') and origin.startswith('https://'):
        return True
    
    # Aceitar qualquer subdomínio do vercel.app
    if origin.endswith('.vercel.app') and origin.startswith('https://'):
        return True
    
    # Aceitar qualquer subdomínio do vercel.com
    if origin.endswith('.vercel.com') and origin.startswith('https://'):
        return True
    
    return False

# Configurar CORS com função de validação dinâmica
# Usar uma lista expandida de origens para garantir compatibilidade
expanded_origins = [
    frontend_url,
    'https://alphaadvisor.vercel.app',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8123',
    'http://127.0.0.1:8123',
    'https://smith.langchain.com',
    'https://studio.langchain.com',
    'https://api.smith.langchain.com',
    # Adicionar mais subdomínios comuns do LangChain
    'https://app.langchain.com',
    'https://cloud.langchain.com',
]

CORS(app, 
     origins=expanded_origins,  # Lista expandida de origens
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'X-LangSmith-API-Key', 'Accept', 'x-auth-scheme', 'x-user-id', 'x-tenant-id'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
     expose_headers=['Content-Type', 'X-Request-Id'],
     automatic_options=True)  # Garantir que OPTIONS seja tratado automaticamente

# Handler adicional para garantir que OPTIONS retorne headers CORS corretos para origens dinâmicas
@app.after_request
def after_request(response):
    """Adiciona headers CORS para origens dinâmicas após o processamento"""
    origin = request.headers.get('Origin')
    if origin and is_allowed_origin(origin):
        # Se a origem é permitida mas não está na lista expandida, adicionar manualmente
        if origin not in expanded_origins:
            response.headers.add("Access-Control-Allow-Origin", origin)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Registrar blueprints
try:
    logger.info("[Startup] Registrando blueprints...")
    app.register_blueprint(chat.chat_bp)
    logger.info("[Startup] Blueprint 'chat' registrado")
    app.register_blueprint(oportunidades.oportunidades_bp)
    logger.info("[Startup] Blueprint 'oportunidades' registrado")
    app.register_blueprint(alertas.alertas_bp)
    logger.info("[Startup] Blueprint 'alertas' registrado")
    app.register_blueprint(assessor.assessor_bp)
    logger.info("[Startup] Blueprint 'assessor' registrado")
    app.register_blueprint(cliente.cliente_bp)
    logger.info("[Startup] Blueprint 'cliente' registrado")
    app.register_blueprint(configuracoes.configuracoes_bp)
    logger.info("[Startup] Blueprint 'configuracoes' registrado")
    app.register_blueprint(conexoes.conexoes_bp)
    logger.info("[Startup] Blueprint 'conexoes' registrado")
    app.register_blueprint(health.health_bp)
    logger.info("[Startup] Blueprint 'health' registrado")
    app.register_blueprint(trace_visualization.trace_bp)
    logger.info("[Startup] Blueprint 'trace_visualization' registrado")
    app.register_blueprint(painel_agente.painel_agente_bp)
    logger.info("[Startup] Blueprint 'painel_agente' registrado")
    app.register_blueprint(agent_builder.agent_builder_bp)
    logger.info("[Startup] Blueprint 'agent_builder' registrado")
    app.register_blueprint(auth.auth_bp)
    logger.info("[Startup] Blueprint 'auth' registrado")
    app.register_blueprint(langgraph_server.langgraph_server_bp)
    logger.info("[Startup] Blueprint 'langgraph_server' registrado")
    
    # Listar todas as rotas registradas para debug
    logger.info("[Startup] Rotas registradas:")
    for rule in app.url_map.iter_rules():
        logger.info(f"[Startup]   {rule.rule} [{', '.join(rule.methods)}] -> {rule.endpoint}")
    
    logger.info("[Startup] Blueprints registrados com sucesso")
except Exception as e:
    logger.error(f"[Startup] Erro ao registrar blueprints: {type(e).__name__}: {e}")
    import traceback
    logger.error(f"[Startup] Traceback:\n{traceback.format_exc()}")
    raise

@app.route('/')
def index():
    return jsonify({'message': 'AlphaAdvisor API', 'status': 'running'}), 200

# Error handlers globais
@app.errorhandler(404)
def handle_404(e):
    """Handler para erros 404 (Not Found)"""
    logger.warning(f"[ErrorHandler] 404 Not Found: {request.method} {request.url}")
    logger.warning(f"[ErrorHandler] Headers: {dict(request.headers)}")
    return jsonify({'error': 'Not Found', 'message': 'A rota solicitada não foi encontrada', 'path': request.path}), 404

@app.errorhandler(405)
def handle_405(e):
    """Handler para erros 405 (Method Not Allowed)"""
    logger.warning(f"[ErrorHandler] 405 Method Not Allowed: {request.method} {request.url}")
    logger.warning(f"[ErrorHandler] Headers: {dict(request.headers)}")
    return jsonify({'error': 'Method Not Allowed', 'message': f'O método {request.method} não é permitido para esta rota', 'path': request.path}), 405

@app.errorhandler(500)
def handle_500(e):
    """Handler para erros 500 (Internal Server Error)"""
    logger.error(f"[ErrorHandler] 500 Internal Server Error: {type(e).__name__}: {e}")
    logger.error(f"[ErrorHandler] Request: {request.method} {request.url}")
    logger.error(f"[ErrorHandler] Headers: {dict(request.headers)}")
    try:
        logger.error(f"[ErrorHandler] JSON Body: {request.get_json()}")
    except:
        logger.error("[ErrorHandler] Não foi possível obter JSON do body")
    import traceback
    error_traceback = traceback.format_exc()
    logger.error(f"[ErrorHandler] Traceback completo:\n{error_traceback}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Ocorreu um erro interno no servidor',
        'type': type(e).__name__
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handler global para qualquer exceção não tratada"""
    logger.error(f"[ErrorHandler] Exceção não tratada: {type(e).__name__}: {e}")
    logger.error(f"[ErrorHandler] Request: {request.method} {request.url}")
    logger.error(f"[ErrorHandler] Path: {request.path}")
    logger.error(f"[ErrorHandler] Headers: {dict(request.headers)}")
    try:
        logger.error(f"[ErrorHandler] JSON Body: {request.get_json()}")
    except:
        logger.error("[ErrorHandler] Não foi possível obter JSON do body")
    import traceback
    error_traceback = traceback.format_exc()
    logger.error(f"[ErrorHandler] Traceback completo:\n{error_traceback}")
    
    # Se já foi tratado por outro handler, não fazer nada
    if hasattr(e, 'code'):
        raise e
    
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(e),
        'type': type(e).__name__
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

# Para gunicorn
application = app

