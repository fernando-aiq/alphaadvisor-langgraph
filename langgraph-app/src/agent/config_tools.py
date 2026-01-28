"""
Tool e helper para obter regras de redirecionamento (handoff) do backend Flask.
Usado pelo grafo no LangSmith para decidir handoff e exibir a tool no Studio.
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
        return list(REGRAS_REDIRECIONAMENTO_PADRAO)
    url = f"{base}/api/configuracoes/regras_redirecionamento?user_id={user_id}"
    try:
        import requests
        r = requests.get(url, timeout=5)
        if r.ok:
            data = r.json()
            regras = data.get("regras_redirecionamento")
            if isinstance(regras, list) and regras:
                return regras
    except Exception:
        pass
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
