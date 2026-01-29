"""Agente LangGraph com ferramentas (ReAct) — módulo usado pelo Studio para Chat.

Estado: MessagesState (chave "messages") para o Studio ativar a interface de Chat.
Usa as tools do backend Flask para análise de carteira e recomendações.
Suporta regras de redirecionamento (handoff) via config.configurable.regras_redirecionamento.
"""

from __future__ import annotations

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Regras padrão quando nenhuma for passada (espelha CONFIGURACOES_PADRAO do backend)
REGRAS_REDIRECIONAMENTO_PADRAO = [
    "Solicitação de valores acima de R$ 100.000",
    "Reclamações ou insatisfação",
    "Solicitação de cancelamento de conta",
    "Questões legais ou regulatórias",
]

try:
    from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
    from langchain_core.runnables import RunnableConfig
    from langchain_openai import ChatOpenAI
    from langgraph.graph import MessagesState, StateGraph, START, END
    from langgraph.prebuilt import ToolNode
    from langgraph.checkpoint.memory import MemorySaver

    from app.services.langgraph_tools import (
        obter_perfil,
        obter_carteira,
        analisar_adequacao,
        analisar_alinhamento_objetivos,
        analisar_diversificacao,
        recomendar_rebalanceamento,
        calcular_projecao,
        buscar_oportunidades
    )
    logger.info("[LangGraphGraph] Imports realizados com sucesso")
except Exception as e:
    logger.error(f"[LangGraphGraph] Erro ao importar dependências: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise

# Usar modelo configurável via .env ou padrão gpt-4o
model_name = os.getenv('AI_MODEL', 'gpt-4o')
model = ChatOpenAI(model=model_name, temperature=0.7)

# Todas as tools do backend
tools = [
    obter_perfil,
    obter_carteira,
    analisar_adequacao,
    analisar_alinhamento_objetivos,
    analisar_diversificacao,
    recomendar_rebalanceamento,
    calcular_projecao,
    buscar_oportunidades
]

tool_node = ToolNode(tools)

SYSTEM = (
    "Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter. "
    "Você ajuda clientes a entender e otimizar suas carteiras de investimentos. "
    "\n\n"
    "Você tem acesso às seguintes ferramentas:\n"
    "- obter_perfil: Busca o perfil completo do cliente (nome, idade, profissão, perfil de investidor). Use SEMPRE quando precisar saber o perfil.\n"
    "- obter_carteira: Busca dados completos da carteira (total, investimentos, distribuição). Use quando o cliente perguntar sobre sua carteira.\n"
    "- analisar_adequacao: Analisa se a carteira está adequada ao perfil. Use quando perguntarem sobre adequação ou problemas na carteira.\n"
    "- analisar_alinhamento_objetivos: Analisa alinhamento com objetivos de curto/médio/longo prazo. Use quando perguntarem sobre alinhamento.\n"
    "- analisar_diversificacao: Analisa diversificação da carteira. Use quando perguntarem sobre diversificação ou concentração.\n"
    "- recomendar_rebalanceamento: Gera recomendações de rebalanceamento. Use quando perguntarem sobre rebalanceamento ou ajustes.\n"
    "- calcular_projecao: Calcula projeção de investimento. Use quando perguntarem sobre projeções ou viabilidade de objetivos.\n"
    "- buscar_oportunidades: Busca oportunidades de investimento. Use quando perguntarem sobre oportunidades ou recomendações de produtos.\n"
    "\n"
    "IMPORTANTE: Sempre use as ferramentas quando necessário. Se o cliente perguntar sobre perfil, carteira, adequação, etc., "
    "use as ferramentas apropriadas para obter dados reais antes de responder. "
    "Seja conversacional, empático e claro nas explicações."
)


def init_node(state: MessagesState) -> dict:
    """
    Nó de inicialização do grafo.
    Valida e prepara o estado inicial antes de processar.
    """
    logger.debug("[LangGraphGraph] init_node: Inicializando grafo")
    
    # Validar que há mensagens no estado
    if not state.get("messages"):
        logger.warning("[LangGraphGraph] init_node: Nenhuma mensagem no estado inicial")
        return state
    
    # Log da primeira mensagem (se houver)
    if state["messages"]:
        first_msg = state["messages"][0]
        msg_content = getattr(first_msg, "content", str(first_msg))[:100]
        logger.debug(f"[LangGraphGraph] init_node: Primeira mensagem: {msg_content}...")
    
    # Retornar estado sem modificações (pass-through)
    # O nó init serve como ponto de entrada explícito para validação/logging
    return state


def end_node(state: MessagesState) -> dict:
    """
    Nó de finalização do grafo.
    Executa limpeza e logging final antes de terminar.
    """
    logger.debug("[LangGraphGraph] end_node: Finalizando grafo")
    
    # Log da última mensagem (resposta do assistente)
    if state.get("messages"):
        last_msg = state["messages"][-1]
        msg_content = getattr(last_msg, "content", str(last_msg))[:100]
        logger.debug(f"[LangGraphGraph] end_node: Última mensagem: {msg_content}...")
    
    # Retornar estado final sem modificações
    return state


def agent_node(state: MessagesState) -> dict:
    messages = [SystemMessage(content=SYSTEM)] + state["messages"]
    response = model.bind_tools(tools).invoke(messages)
    return {"messages": [response]}


def _extract_text_content(content: Any) -> str:
    """Extrai texto do content (string ou lista de blocos)."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        text = " ".join(parts)
    else:
        text = str(content) if content is not None else ""
    return (text or "").strip()


def _deve_redirecionar(messages: list, regras: list[str], llm_model=None):
    """
    Usa o LLM para decidir se a última mensagem do usuário se enquadra em alguma
    regra de redirecionamento. Não é determinístico: o modelo interpreta contexto e intenção.
    Retorna (True, regra_casada) ou (False, None).
    Em caso de erro na chamada ao LLM, retorna (False, None).
    """
    if not regras:
        return False, None
    regras = [r.strip() for r in regras if r and str(r).strip()]
    if not regras:
        return False, None
    user_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    if not user_msgs:
        return False, None
    last_user = user_msgs[-1]
    texto_usuario = _extract_text_content(getattr(last_user, "content", None) or "")
    if not texto_usuario:
        return False, None

    llm = llm_model if llm_model is not None else model
    prompt = (
        "Você é um classificador. Avalie se a mensagem do cliente se enquadra em ALGUMA das regras abaixo.\n\n"
        "Mensagem do cliente:\n\"\"\"\n" + texto_usuario + "\n\"\"\"\n\n"
        "Regras (redirecionar para humano quando se aplicar):\n"
        + "\n".join(f"- {r}" for r in regras)
        + "\n\n"
        "Responda com UMA ÚNICA LINHA:\n"
        "- Se a mensagem se enquadrar em alguma regra, repita EXATAMENTE o texto dessa regra (uma das listadas).\n"
        "- Se não se enquadrar em nenhuma, responda apenas: NENHUMA\n"
        "Não invente regras. Não explique. Só a regra exata ou NENHUMA."
    )
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        out = (getattr(resp, "content", None) or str(resp)).strip()
        if not out or out.upper() == "NENHUMA":
            return False, None
        # Encontrar qual regra foi retornada (o LLM pode repetir a regra ou algo próximo)
        for r in regras:
            if not r or not r.strip():
                continue
            rnorm = r.strip()
            if rnorm in out or out in rnorm:
                return True, rnorm
        # Resposta do LLM não é "NENHUMA" e não bateu exato: considerar como regra casada (LLM indicou match)
        return True, out[:200]
    except Exception as e:
        logger.warning("[LangGraphGraph] _deve_redirecionar LLM falhou: %s", e)
        return False, None


def should_route_after_init(state: MessagesState, config: RunnableConfig) -> str:
    """
    Router pós-init: decide handoff ou agent com base só na mensagem do usuário.
    A decisão de handoff é feita antes de o agente responder.
    """
    regras = (config.get("configurable") or {}).get("regras_redirecionamento") or REGRAS_REDIRECIONAMENTO_PADRAO
    deve, _ = _deve_redirecionar(state["messages"], regras)
    if deve:
        return "handoff"
    return "agent"


def should_continue(state: MessagesState, config: RunnableConfig) -> str:
    """
    Determina o próximo nó após o agent. Handoff já foi decidido antes do agent (router pós-init).
    Ordem: (1) tool_calls -> tools; (2) end.
    """
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"


def handoff_node(state: MessagesState, config: RunnableConfig) -> dict:
    """
    Nó de handoff: informa que um assessor humano será acionado.
    A regra casada é obtida via LLM (mesma lógica de _deve_redirecionar) e usada em handoff_reason.
    """
    regras = (config.get("configurable") or {}).get("regras_redirecionamento") or REGRAS_REDIRECIONAMENTO_PADRAO
    deve, regra_casada = _deve_redirecionar(state["messages"], regras)
    reason = regra_casada or "Regra de redirecionamento acionada"
    handoff_message = AIMessage(
        content=(
            "Para melhor atendê-lo neste assunto, vou encaminhar sua solicitação para um de nossos assessores. "
            "Você receberá um contato em breve."
        ),
        additional_kwargs={
            "handoff": True,
            "handoff_reason": reason,
            "handoff_rule": reason,
        },
    )
    return {"messages": [handoff_message]}


try:
    # Criar checkpointer para preservar estado entre invocações
    checkpointer = MemorySaver()
    logger.info("[LangGraphGraph] Checkpointer (MemorySaver) criado")
    
    # Construir grafo com nós explícitos init, end e handoff
    graph = (
        StateGraph(MessagesState)
        .add_node("init", init_node)
        .add_node("agent", agent_node)
        .add_node("tools", tool_node)
        .add_node("end", end_node)
        .add_node("handoff", handoff_node)
        .add_edge(START, "init")
        .add_conditional_edges(
            "init",
            should_route_after_init,
            {
                "handoff": "handoff",
                "agent": "agent",
            },
        )
        .add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": "end",
            },
        )
        .add_edge("tools", "agent")
        .add_edge("end", END)
        .add_edge("handoff", END)
        .compile(name="agent", checkpointer=checkpointer)
    )
    logger.info("[LangGraphGraph] Grafo compilado com sucesso (checkpointer, init/end/handoff)")
except Exception as e:
    logger.error(f"[LangGraphGraph] Erro ao compilar grafo: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise
