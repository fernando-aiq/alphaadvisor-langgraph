"""
Tool e helper para obter regras de redirecionamento (handoff) do backend Flask.
Usado pelo grafo no LangSmith para decidir handoff e exibir a tool no Studio.

IMPORTANTE: No deploy do LangSmith (Cloud), defina a variável BACKEND_URL com a URL
base do backend Flask (ex: https://seu-backend.onrender.com). Sem BACKEND_URL,
o agente usa sempre as 4 regras padrão e não reflete o que foi salvo na página Autonomia.
"""
import os
from typing import List
from langchain_core.tools import tool

REGRAS_REDIRECIONAMENTO_PADRAO = [
    "Solicitação de valores acima de R$ 100.000",
    "Reclamações ou insatisfação",
    "Solicitação de cancelamento de conta",
    "Questões legais ou regulatórias",
]


def fetch_regras_redirecionamento(user_id: str = "default") -> List[str]:
    """
    Obtém as regras de redirecionamento do backend Flask.
    Se BACKEND_URL não estiver definida ou a requisição falhar, retorna as regras padrão.
    """
    base = (os.getenv("BACKEND_URL") or "").rstrip("/")
    if not base:
        print("[RegrasHandoff] BACKEND_URL não definida; usando regras padrão.")
        return list(REGRAS_REDIRECIONAMENTO_PADRAO)
    url = f"{base}/api/configuracoes/regras_redirecionamento?user_id={user_id}"
    print(f"[RegrasHandoff] BACKEND_URL definida; GET {url[:80]}{'...' if len(url) > 80 else ''}")
    try:
        import requests
        r = requests.get(url, timeout=5)
        if r.ok:
            data = r.json()
            regras = data.get("regras_redirecionamento")
            count = len(regras) if isinstance(regras, list) else 0
            print(f"[RegrasHandoff] Flask OK status={r.status_code} regras_count={count}")
            if isinstance(regras, list) and regras:
                return regras
        else:
            print(f"[RegrasHandoff] Flask error status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        print(f"[RegrasHandoff] Exception: {type(e).__name__} {e}")
    print("[RegrasHandoff] Usando regras padrão (fallback).")
    return list(REGRAS_REDIRECIONAMENTO_PADRAO)


@tool
def obter_regras_redirecionamento(user_id: str = "default") -> dict:
    """
    Busca as regras de handoff/redirecionamento configuradas para o atendimento.
    Use quando o usuário perguntar quais situações acionam transferência para um assessor humano
    ou 'tem ferramentas pra handoff'. Retorna a lista de regras (ex.: cancelamento de conta,
    reclamações, valores altos, questões legais).
    """
    regras = fetch_regras_redirecionamento(user_id)
    return {"regras_redirecionamento": regras}
