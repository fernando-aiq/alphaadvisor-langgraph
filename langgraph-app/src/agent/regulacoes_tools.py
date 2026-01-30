"""
Tool para consultar regulacoes (CVM, Lei Mercado de Capitais, LGPD, ANBIMA) no backend Flask.
Quando BACKEND_URL estiver definido, chama GET /api/regulacoes e GET /api/regulacoes/<id>.
"""
import os
from typing import Any, Dict, Optional
from langchain_core.tools import tool

DEFAULT_BACKEND_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"


def _fetch_regulacao(regulacao_id: str, backend_url: Optional[str] = None) -> Dict[str, Any]:
    """Obtém uma regulacao pelo id ou lista todas (regulacao_id='lista')."""
    base = (backend_url or os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL or "").strip().rstrip("/")
    if not base:
        return {"error": "BACKEND_URL não definida. Configure para consultar regulacoes."}
    id_clean = (regulacao_id or "").strip().lower()
    if id_clean in ("lista", "listar", ""):
        url = f"{base}/api/regulacoes"
    else:
        url = f"{base}/api/regulacoes/{id_clean}"
    try:
        import requests
        r = requests.get(url, timeout=15)
        if r.ok:
            return r.json()
        return {"error": f"Backend retornou {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": f"Falha ao consultar backend: {type(e).__name__} {e}"}


@tool
def consultar_regulacao(regulacao_id: str, backend_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Consulta o texto completo de uma norma regulatória que o assessor de investimentos deve seguir.
    Use quando o cliente perguntar sobre regulações, CVM, LGPD, leis do mercado de capitais, ANBIMA ou obrigações legais do assessor.
    IDs disponíveis: cvm_178_2023 (assessor de investimentos), cvm_179_2023 (transparência remuneração),
    lei_6385_1976 (Lei Mercado de Capitais), lei_13709_lgpd_2018 (LGPD), anbima_codigo_conduta (ANBIMA).
    Para listar todas, use regulacao_id='lista'.

    Args:
        regulacao_id: ID da norma (ex: cvm_178_2023, lei_13709_lgpd_2018) ou 'lista' para listar normas disponíveis.
        backend_url: URL base do backend (opcional; usa BACKEND_URL se não informado).

    Returns:
        Dict com id, titulo, norma, fonte_url, vigencia, resumo e texto_completo (ou lista de normas se regulacao_id='lista')
    """
    return _fetch_regulacao(regulacao_id, backend_url)
