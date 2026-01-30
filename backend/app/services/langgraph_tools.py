"""
Tools do backend convertidas para formato @tool do LangChain.
Wrapper para usar as funções de agent_tools.py no formato LangChain.
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    from langchain_core.tools import tool
    logger.info("[LangGraphTools] langchain_core.tools importado com sucesso")
except Exception as e:
    logger.error(f"[LangGraphTools] Erro ao importar langchain_core.tools: {e}")
    raise

# Importar dados do cliente
try:
    from app.routes.cliente import CARTEIRA, PERFIL_JOAO
    logger.info("[LangGraphTools] Dados do cliente importados com sucesso")
except Exception as e:
    logger.error(f"[LangGraphTools] Erro ao importar dados do cliente: {e}")
    # Usar valores vazios como fallback
    CARTEIRA = {}
    PERFIL_JOAO = {}

# Importar serviço de regulacoes (para tool consultar_regulacao)
try:
    from app.services.regulacoes_service import get_regulacao as _get_regulacao, list_regulacoes as _list_regulacoes
except Exception as e:
    logger.warning("[LangGraphTools] regulacoes_service não disponível: %s", e)
    _get_regulacao = None
    _list_regulacoes = None

# Importar funções do agent_tools
try:
    from app.services.agent_tools import (
        obter_perfil as _obter_perfil,
        obter_carteira as _obter_carteira,
        analisar_adequacao as _analisar_adequacao,
        analisar_alinhamento_objetivos as _analisar_alinhamento_objetivos,
        analisar_diversificacao as _analisar_diversificacao,
        recomendar_rebalanceamento as _recomendar_rebalanceamento,
        calcular_projecao as _calcular_projecao,
        buscar_oportunidades as _buscar_oportunidades
    )
    logger.info("[LangGraphTools] Funções do agent_tools importadas com sucesso")
except Exception as e:
    logger.error(f"[LangGraphTools] Erro ao importar funções do agent_tools: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise


@tool
def obter_perfil() -> Dict[str, Any]:
    """
    Busca o perfil completo do cliente, incluindo perfil de investidor.
    Use SEMPRE quando o cliente perguntar sobre seu perfil de investidor ou quando precisar saber o perfil para fazer análises.
    Retorna informações sobre nome, idade, profissão, perfil de investidor (conservador/moderado/arrojado) e outros dados do cliente.
    """
    result = _obter_perfil()
    # Converter Pydantic model para dict se necessário
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, 'dict'):
        return result.dict()
    return result


@tool
def obter_carteira() -> Dict[str, Any]:
    """
    Busca dados completos da carteira do cliente.
    Use APENAS quando o cliente perguntar especificamente sobre sua carteira atual, saldo, investimentos ou patrimônio.
    Retorna informações sobre total, distribuição percentual e investimentos.
    """
    result = _obter_carteira()
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, 'dict'):
        return result.dict()
    return result


@tool
def analisar_adequacao(carteira: Dict[str, Any], perfil: str) -> Dict[str, Any]:
    """
    Analisa se a carteira está adequada ao perfil do investidor.
    Use SEMPRE quando o cliente perguntar sobre adequação ao perfil, se a carteira está adequada, ou sobre problemas na carteira.
    Obtém a carteira automaticamente. Parâmetro: perfil (str: 'conservador', 'moderado', 'arrojado', padrão: 'conservador').
    
    Args:
        carteira: Dicionário com dados da carteira (obtido via obter_carteira)
        perfil: Perfil de investidor ('conservador', 'moderado', 'arrojado')
    
    Returns:
        Dict com score, problemas, recomendações e se está adequado
    """
    result = _analisar_adequacao(carteira, perfil)
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, 'dict'):
        return result.dict()
    return result


@tool
def analisar_alinhamento_objetivos(carteira: Dict[str, Any], perfil: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa se a carteira está alinhada com objetivos de curto, médio e longo prazo.
    Use SEMPRE quando o cliente perguntar sobre alinhamento com objetivos, se está alinhado com curto/médio/longo prazo, ou sobre adequação aos horizontes temporais.
    Obtém carteira e perfil automaticamente. Retorna análise detalhada por horizonte temporal.
    
    Args:
        carteira: Dicionário com dados da carteira
        perfil: Dicionário com dados do perfil do cliente
    
    Returns:
        Dict com análise de alinhamento para curto, médio e longo prazo
    """
    result = _analisar_alinhamento_objetivos(carteira, perfil)
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, 'dict'):
        return result.dict()
    return result


@tool
def analisar_diversificacao(carteira: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa a diversificação da carteira do cliente.
    Identifica concentrações excessivas e sugere melhorias.
    
    Args:
        carteira: Dicionário com dados da carteira
    
    Returns:
        Dict com score de diversificação, problemas, concentrações e recomendações
    """
    result = _analisar_diversificacao(carteira)
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, 'dict'):
        return result.dict()
    return result


@tool
def recomendar_rebalanceamento(carteira: Dict[str, Any], perfil: str) -> Dict[str, Any]:
    """
    Gera recomendações específicas de rebalanceamento da carteira.
    
    Args:
        carteira: Dicionário com dados da carteira
        perfil: Perfil de investidor ('conservador', 'moderado', 'arrojado') ou dict com perfilInvestidor
    
    Returns:
        Dict com recomendações de rebalanceamento
    """
    # Extrair perfil string se for dict
    if isinstance(perfil, dict):
        perfil_str = perfil.get('perfilInvestidor', 'conservador')
    else:
        perfil_str = str(perfil)
    
    # A função _recomendar_rebalanceamento espera perfil como string
    result = _recomendar_rebalanceamento(carteira, perfil_str)
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, 'dict'):
        return result.dict()
    return result


@tool
def calcular_projecao(
    valor_atual: Optional[float] = None,
    aporte_mensal: Optional[float] = None,
    prazo_anos: Optional[int] = None,
    rentabilidade_anual: float = 0.10,
    carteira: Optional[Dict[str, Any]] = None,
    perfil: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calcula projeção de investimento considerando aportes mensais e rentabilidade.
    Usa juros compostos para cálculo.
    
    Aceita dois formatos de entrada:
    1. Valores numéricos: valor_atual (float), aporte_mensal (float), prazo_anos (int)
    2. Dicionários: carteira (dict), perfil (dict) - extrai valores automaticamente
    
    Args:
        valor_atual: Valor atual investido (opcional se fornecer carteira)
        aporte_mensal: Aporte mensal (opcional se fornecer carteira/perfil)
        prazo_anos: Prazo em anos (opcional se fornecer perfil/carteira)
        rentabilidade_anual: Rentabilidade anual esperada (padrão: 10%)
        carteira: Dicionário com dados da carteira (opcional)
        perfil: Dicionário com dados do perfil (opcional)
    
    Returns:
        Dict com projeção de investimento
    """
    result = _calcular_projecao(
        valor_atual=valor_atual,
        aporte_mensal=aporte_mensal,
        prazo_anos=prazo_anos,
        rentabilidade_anual=rentabilidade_anual,
        carteira=carteira,
        perfil=perfil
    )
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    elif hasattr(result, 'dict'):
        return result.dict()
    return result


@tool
def buscar_oportunidades(perfil: str, problemas: List[str]) -> List[Dict[str, Any]]:
    """
    Busca oportunidades de investimento adequadas ao perfil e problemas identificados.
    
    Args:
        perfil: Perfil de investidor ('conservador', 'moderado', 'arrojado')
        problemas: Lista de problemas identificados na carteira
    
    Returns:
        Lista de oportunidades de investimento
    """
    result = _buscar_oportunidades(perfil, problemas)
    # Converter lista de Pydantic models para lista de dicts
    if result and isinstance(result, list):
        return [
            item.model_dump() if hasattr(item, 'model_dump')
            else item.dict() if hasattr(item, 'dict')
            else item
            for item in result
        ]
    return result


@tool
def consultar_regulacao(regulacao_id: str) -> Dict[str, Any]:
    """
    Consulta o texto completo de uma norma regulatória que o assessor de investimentos deve seguir.
    Use quando o cliente perguntar sobre regulações, CVM, LGPD, leis do mercado de capitais, ANBIMA ou obrigações legais do assessor.
    IDs disponíveis: cvm_178_2023 (assessor de investimentos), cvm_179_2023 (transparência remuneração),
    lei_6385_1976 (Lei Mercado de Capitais), lei_13709_lgpd_2018 (LGPD), anbima_codigo_conduta (ANBIMA).
    Para listar todas, use regulacao_id='lista'.

    Args:
        regulacao_id: ID da norma (ex: cvm_178_2023, lei_13709_lgpd_2018) ou 'lista' para listar normas disponíveis.

    Returns:
        Dict com id, titulo, norma, fonte_url, vigencia, resumo e texto_completo (ou lista de normas se regulacao_id='lista')
    """
    if _get_regulacao is None or _list_regulacoes is None:
        return {"error": "Serviço de regulacoes não disponível."}
    id_clean = (regulacao_id or "").strip().lower()
    if id_clean in ("lista", "listar", ""):
        items = _list_regulacoes()
        return {"regulacoes": items, "mensagem": "Use consultar_regulacao com um dos ids acima para obter o texto completo."}
    data = _get_regulacao(id_clean)
    if data is None:
        return {"error": f"Regulacao não encontrada: {regulacao_id}. Use regulacao_id='lista' para ver os ids disponíveis."}
    return data
