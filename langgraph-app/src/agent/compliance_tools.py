"""
Tools para o agente de compliance consultar políticas e regras no backend Flask.
Usado para validar a resposta do agente principal antes de devolvê-la ao usuário.
"""
import os
from typing import Any, Dict, Optional
from langchain_core.tools import tool

DEFAULT_BACKEND_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"


def _get_backend_url(backend_url: Optional[str] = None) -> str:
    base = (backend_url or os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL or "").strip().rstrip("/")
    return base


def _fetch_policy(policy_id: str, backend_url: Optional[str] = None) -> Dict[str, Any]:
    """Chama GET /api/painel-agente/compliance/policies?id=<policy_id>. Retorna dict ou mensagem de erro."""
    base = _get_backend_url(backend_url)
    if not base:
        return {"error": "Backend não configurado (BACKEND_URL). Política indisponível."}
    url = f"{base}/api/painel-agente/compliance/policies?id={policy_id}"
    try:
        import requests
        r = requests.get(url, timeout=10)
        if r.ok:
            return r.json()
        return {"error": f"Política indisponível (HTTP {r.status_code})."}
    except Exception as e:
        return {"error": f"Política indisponível: {type(e).__name__}."}


@tool
def consultar_politica_lgpd(backend_url: Optional[str] = None) -> dict:
    """
    Consulta a política de LGPD (Lei Geral de Proteção de Dados) para validar se a resposta
    está em conformidade com base legal, consentimento e tratamento de dados pessoais.
    Use para revisar a resposta do agente à luz desta política.
    """
    return _fetch_policy("lgpd", backend_url)


@tool
def consultar_politica_cvm(backend_url: Optional[str] = None) -> dict:
    """
    Consulta as regras CVM para assessoria de investimentos. Use para validar se a resposta
    está em conformidade com recomendações, adequação e registro para auditoria.
    """
    return _fetch_policy("cvm", backend_url)


@tool
def consultar_politica_auditoria(backend_url: Optional[str] = None) -> dict:
    """
    Consulta a política de auditoria (trilha de eventos e acessos). Use para garantir
    que a resposta não contradiz requisitos de rastreabilidade.
    """
    return _fetch_policy("auditoria", backend_url)


@tool
def consultar_politica_pii(backend_url: Optional[str] = None) -> dict:
    """
    Consulta a política de mascaramento de PII (dados pessoais sensíveis). Use para validar
    que a resposta não expõe dados que devem ser mascarados.
    """
    return _fetch_policy("pii", backend_url)


@tool
def consultar_politica_retencao(backend_url: Optional[str] = None) -> dict:
    """
    Consulta a política de retenção de dados (ex.: 90 dias). Use para validar que a resposta
    está alinhada com prazos de guarda e auditoria.
    """
    return _fetch_policy("retencao", backend_url)


@tool
def consultar_regras_especificas(backend_url: Optional[str] = None) -> dict:
    """
    Consulta as regras de compliance específicas cadastradas (customizadas). Use para validar
    a resposta do agente contra essas regras adicionais.
    """
    return _fetch_policy("rules", backend_url)


COMPLIANCE_TOOLS = [
    consultar_politica_lgpd,
    consultar_politica_cvm,
    consultar_politica_auditoria,
    consultar_politica_pii,
    consultar_politica_retencao,
    consultar_regras_especificas,
]
