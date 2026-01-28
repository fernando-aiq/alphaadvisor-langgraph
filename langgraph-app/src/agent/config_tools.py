"""
Tool e helper para obter regras de redirecionamento (handoff) do backend Flask.
Usado pelo grafo no LangSmith para decidir handoff e exibir a tool no Studio.

IMPORTANTE: No deploy do LangSmith (Cloud), defina a variável BACKEND_URL com a URL
base do backend Flask (ex: https://seu-backend.onrender.com). Sem BACKEND_URL,
o agente usa sempre as 4 regras padrão e não reflete o que foi salvo na página Autonomia.
"""
import os
from typing import List, Optional
from langchain_core.tools import tool

REGRAS_REDIRECIONAMENTO_PADRAO = [
    "Solicitação de valores acima de R$ 100.000",
    "Reclamações ou insatisfação",
    "Solicitação de cancelamento de conta",
    "Questões legais ou regulatórias",
]

# URL padrão do backend quando BACKEND_URL e config.configurable.backend_url não estão definidos (ex.: LangGraph Cloud).
DEFAULT_BACKEND_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"


def fetch_regras_redirecionamento(user_id: str = "default", backend_url: Optional[str] = None) -> List[str]:
    """
    Obtém as regras de redirecionamento do backend Flask.
    Usa backend_url (ex: de config.configurable) se informado; senão usa env BACKEND_URL; senão DEFAULT_BACKEND_URL.
    Se nenhum estiver definido ou a requisição falhar, retorna as regras padrão.
    """
    base = (backend_url or os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL or "").strip().rstrip("/")
    if not base:
        print("[RegrasHandoff] BACKEND_URL nao definida (env ou config); usando regras padrao.")
        return list(REGRAS_REDIRECIONAMENTO_PADRAO)
    url = f"{base}/api/configuracoes/regras_redirecionamento?user_id={user_id}"
    print(f"[RegrasHandoff] GET {url[:90]}{'...' if len(url) > 90 else ''}")
    try:
        import requests
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            regras = data.get("regras_redirecionamento")
            count = len(regras) if isinstance(regras, list) else 0
            print(f"[RegrasHandoff] Backend OK status={r.status_code} regras_count={count}")
            if isinstance(regras, list):
                return regras if regras else list(REGRAS_REDIRECIONAMENTO_PADRAO)
        else:
            print(f"[RegrasHandoff] Backend error status={r.status_code} body={r.text[:300]}")
    except Exception as e:
        print(f"[RegrasHandoff] Exception: {type(e).__name__} {e}")
    print("[RegrasHandoff] Fallback: usando regras padrao.")
    return list(REGRAS_REDIRECIONAMENTO_PADRAO)


@tool
def obter_regras_redirecionamento(user_id: str = "default", backend_url: Optional[str] = None) -> dict:
    """
    Busca as regras de handoff/redirecionamento configuradas para o atendimento.
    Use quando o usuário perguntar quais situações acionam transferência para um assessor humano
    ou 'tem ferramentas pra handoff'. Retorna a lista de regras (ex.: cancelamento de conta,
    reclamações, valores altos, questões legais).
    """
    regras = fetch_regras_redirecionamento(user_id, backend_url)
    return {"regras_redirecionamento": regras}
