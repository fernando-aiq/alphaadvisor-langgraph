"""
Tool e helper para obter regras de redirecionamento (handoff) e respostas permitidas do backend Flask.
Usado pelo grafo no LangSmith para decidir handoff e exibir a tool no Studio.
Uma única chamada ao mesmo endpoint traz regras + respostas (fonte S3).

IMPORTANTE: No deploy do LangSmith (Cloud), defina a variável BACKEND_URL com a URL
base do backend Flask (ex: https://seu-backend.onrender.com). Sem BACKEND_URL,
o agente usa sempre as 4 regras padrão e não reflete o que foi salvo na página Autonomia.
"""
import os
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool

REGRAS_REDIRECIONAMENTO_PADRAO = [
    "Solicitação de valores acima de R$ 100.000",
    "Reclamações ou insatisfação",
    "Solicitação de cancelamento de conta",
    "Questões legais ou regulatórias",
]

# Respostas permitidas padrão (tudo True = não handoff por tópico quando API não retorna respostas)
RESPOSTAS_PADRAO: Dict[str, bool] = {
    "falar_sobre_precos": True,
    "falar_sobre_risco": True,
    "recomendar_produtos": True,
    "fornecer_projecoes": True,
    "comparar_produtos": True,
}

# URL padrão do backend quando BACKEND_URL e config.configurable.backend_url não estão definidos (ex.: LangGraph Cloud).
DEFAULT_BACKEND_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"


def fetch_regras_redirecionamento(user_id: str = "default", backend_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtém regras de redirecionamento e respostas permitidas do backend (mesmo endpoint, fonte S3).
    Retorna {"regras_redirecionamento": list, "respostas": dict}. Se a API não retornar respostas, usa tudo permitido.
    """
    base = (backend_url or os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL or "").strip().rstrip("/")
    if not base:
        print("[RegrasHandoff] BACKEND_URL nao definida (env ou config); usando regras e respostas padrao.")
        return {"regras_redirecionamento": list(REGRAS_REDIRECIONAMENTO_PADRAO), "respostas": dict(RESPOSTAS_PADRAO)}
    url = f"{base}/api/configuracoes/regras_redirecionamento?user_id={user_id}"
    print(f"[RegrasHandoff] GET {url[:90]}{'...' if len(url) > 90 else ''}")
    try:
        import requests
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            regras = data.get("regras_redirecionamento")
            if not isinstance(regras, list):
                regras = list(REGRAS_REDIRECIONAMENTO_PADRAO)
            elif not regras:
                regras = list(REGRAS_REDIRECIONAMENTO_PADRAO)
            respostas = data.get("respostas")
            if not isinstance(respostas, dict):
                respostas = dict(RESPOSTAS_PADRAO)
            else:
                for k, v in RESPOSTAS_PADRAO.items():
                    if k not in respostas:
                        respostas[k] = v
            print(f"[RegrasHandoff] Backend OK status={r.status_code} regras_count={len(regras)}")
            return {"regras_redirecionamento": regras, "respostas": respostas}
        print(f"[RegrasHandoff] Backend error status={r.status_code} body={r.text[:300]}")
    except Exception as e:
        print(f"[RegrasHandoff] Exception: {type(e).__name__} {e}")
    print("[RegrasHandoff] Fallback: usando regras e respostas padrao.")
    return {"regras_redirecionamento": list(REGRAS_REDIRECIONAMENTO_PADRAO), "respostas": dict(RESPOSTAS_PADRAO)}


@tool
def obter_regras_redirecionamento(user_id: str = "default", backend_url: Optional[str] = None) -> dict:
    """
    Busca as regras de handoff/redirecionamento e respostas permitidas configuradas para o atendimento.
    Use quando o usuário perguntar quais situações acionam transferência para um assessor humano
    ou 'tem ferramentas pra handoff'. Retorna regras_redirecionamento (lista) e respostas (dict de tópicos true/false).
    """
    return fetch_regras_redirecionamento(user_id, backend_url)
