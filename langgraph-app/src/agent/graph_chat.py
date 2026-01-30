"""Agente LangGraph com ferramentas (ReAct) — módulo usado pelo Studio para Chat.

Estado: MessagesState (chave "messages") para o Studio ativar a interface de Chat.
Usa as tools do backend Flask para análise de carteira e recomendações.
"""

from __future__ import annotations

from pathlib import Path
import re
import os
import json
from typing import Any, Optional, Tuple
from threading import Thread
from datetime import datetime

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode

from agent.backend_tools import (
    obter_perfil,
    obter_carteira,
    analisar_adequacao,
    analisar_alinhamento_objetivos,
    analisar_diversificacao,
    recomendar_rebalanceamento,
    calcular_projecao,
    buscar_oportunidades
)
from agent.config_tools import obter_regras_redirecionamento, REGRAS_REDIRECIONAMENTO_PADRAO, RESPOSTAS_PADRAO
from agent.regulacoes_tools import consultar_regulacao
from agent.compliance_tools import COMPLIANCE_TOOLS

# Usar modelo configurável via .env ou padrão gpt-4o
import os
model_name = os.getenv('AI_MODEL', 'gpt-4o')
model = ChatOpenAI(model=model_name, temperature=0.7)

# Todas as tools do backend + tool de regras de handoff + regulacoes
tools = [
    obter_perfil,
    obter_carteira,
    analisar_adequacao,
    analisar_alinhamento_objetivos,
    analisar_diversificacao,
    recomendar_rebalanceamento,
    calcular_projecao,
    buscar_oportunidades,
    obter_regras_redirecionamento,
    consultar_regulacao,
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
    "- obter_regras_redirecionamento: Busca as regras de handoff (quando transferir para assessor humano). Use quando perguntarem 'quais tools tem', 'tem ferramentas pra handoff' ou 'quando vocês transferem para humano'.\n"
    "- consultar_regulacao: Consulta o texto completo de normas que o assessor deve seguir (CVM 178/179, Lei Mercado de Capitais, LGPD, ANBIMA). Use quando perguntarem sobre regulações, obrigações legais do assessor, CVM, LGPD ou leis do mercado de capitais.\n"
    "\n"
    "IMPORTANTE: Sempre use as ferramentas quando necessário. Se o cliente perguntar sobre perfil, carteira, adequação, regulações, etc., "
    "use as ferramentas apropriadas para obter dados reais antes de responder. "
    "Seja conversacional, empático e claro nas explicações.\n"
    "\n"
    "ATENÇÃO: Quando o cliente solicitar recomendações específicas de investimentos, produtos financeiros ou orientação personalizada "
    "para investir, ou quando a mensagem se enquadrar nas regras de handoff (cancelamento de conta, reclamações, valores altos, questões legais), "
    "você deve sinalizar que um assessor humano será acionado."
)


def init_node(state: MessagesState) -> dict:
    """
    Nó de inicialização do grafo.
    Valida e prepara o estado inicial antes de processar.
    """
    # Validar que há mensagens no estado
    if not state.get("messages"):
        return state
    
    # Retornar estado sem modificações (pass-through)
    return state


def end_node(state: MessagesState) -> dict:
    """
    Nó de finalização do grafo.
    Executa limpeza e logging final antes de terminar.
    """
    # Retornar estado final sem modificações
    return state


def agent_node(state: MessagesState) -> dict:
    messages = [SystemMessage(content=SYSTEM)] + state["messages"]
    response = model.bind_tools(tools).invoke(messages)
    return {"messages": [response]}


def _extract_text_content(content) -> str:
    """
    Extrai texto do content, que pode ser string ou lista.
    """
    if isinstance(content, str):
        return content.lower()
    elif isinstance(content, list):
        # Se for lista, extrair strings e concatenar
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
        return " ".join(text_parts).lower()
    else:
        return ""


def _extract_text_plain(content: Any) -> str:
    """Texto bruto para o classificador de handoff (sem lower)."""
    if isinstance(content, str):
        return (content or "").strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return " ".join(parts).strip()
    return str(content or "").strip()


def _deve_redirecionar(messages: list, regras: list) -> Tuple[bool, Optional[str]]:
    """
    Usa o LLM para decidir se a última mensagem do usuário se enquadra em alguma
    regra de redirecionamento. Retorna (True, regra_casada) ou (False, None).
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
    texto_usuario = _extract_text_plain(getattr(last_user, "content", None) or "")
    if not texto_usuario:
        return False, None
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
        resp = model.invoke([HumanMessage(content=prompt)])
        out = (getattr(resp, "content", None) or str(resp)).strip()
        if not out or out.upper() == "NENHUMA":
            return False, None
        for r in regras:
            if not r or not r.strip():
                continue
            rnorm = r.strip()
            if rnorm in out or out in rnorm:
                return True, rnorm
        return True, out[:200]
    except Exception:
        return False, None


def detect_simple_calculation(content: str) -> Optional[Tuple[float, str, float]]:
    """
    Detecta cálculos simples como "8 por 7", "10 + 5", etc.
    Retorna (num1, operador, num2) ou None se não detectar.
    
    Suporta:
    - Multiplicação: "8 por 7", "8 x 7", "8 * 7", "8 vezes 7"
    - Adição: "8 mais 7", "8 + 7"
    - Subtração: "8 menos 7", "8 - 7"
    - Divisão: "8 dividido por 7", "8 / 7"
    """
    # Normalizar: remover acentos básicos e converter para lowercase
    content = content.lower().strip()
    
    # Padrão para números (inteiros ou decimais)
    number_pattern = r'\d+(?:\.\d+)?'
    
    # Padrões de multiplicação
    multiply_patterns = [
        (r'(\d+(?:\.\d+)?)\s*(?:por|x|\*|vezes)\s*(\d+(?:\.\d+)?)', '*'),
    ]
    
    # Padrões de adição
    add_patterns = [
        (r'(\d+(?:\.\d+)?)\s*(?:mais|\+)\s*(\d+(?:\.\d+)?)', '+'),
    ]
    
    # Padrões de subtração
    subtract_patterns = [
        (r'(\d+(?:\.\d+)?)\s*(?:menos|-)\s*(\d+(?:\.\d+)?)', '-'),
    ]
    
    # Padrões de divisão
    divide_patterns = [
        (r'(\d+(?:\.\d+)?)\s*(?:dividido por|/)\s*(\d+(?:\.\d+)?)', '/'),
    ]
    
    # Tentar cada tipo de operação
    all_patterns = multiply_patterns + add_patterns + subtract_patterns + divide_patterns
    
    for pattern, operator in all_patterns:
        match = re.search(pattern, content)
        if match:
            try:
                num1 = float(match.group(1))
                num2 = float(match.group(2))
                return (num1, operator, num2)
            except (ValueError, IndexError):
                continue
    
    return None


def calculate_simple_expression(num1: float, operator: str, num2: float) -> float:
    """
    Executa cálculo de forma segura (sem eval).
    Trata divisão por zero.
    """
    if operator == '*':
        return num1 * num2
    elif operator == '+':
        return num1 + num2
    elif operator == '-':
        return num1 - num2
    elif operator == '/':
        if num2 == 0:
            raise ValueError("Divisão por zero não é permitida")
        return num1 / num2
    else:
        raise ValueError(f"Operador não suportado: {operator}")


def detect_recommendation_request(state: MessagesState) -> bool:
    """
    Detecta se a mensagem do usuário é uma solicitação de recomendação de investimentos.
    Verifica palavras-chave relacionadas a recomendações específicas de produtos.
    """
    # Buscar a última mensagem do usuário
    user_messages = [msg for msg in state.get("messages", []) if isinstance(msg, HumanMessage)]
    if not user_messages:
        return False
    
    last_user_message = user_messages[-1]
    
    # Extrair conteúdo (pode ser string ou lista)
    if not hasattr(last_user_message, 'content'):
        return False
    
    content = _extract_text_content(last_user_message.content)
    
    # Palavras-chave que indicam solicitação de recomendação de investimentos
    recommendation_keywords = [
        "recomende", "recomendação", "recomendações", "recomendar",
        "onde investir", "em que investir", "o que investir",
        "qual investimento", "quais investimentos", "melhor investimento",
        "produto financeiro", "produtos financeiros",
        "sugestão de investimento", "sugestões de investimento",
        "oportunidade de investimento", "oportunidades de investimento",
        "me indique", "me indique um", "me indique investimentos",
        "quero investir em", "preciso investir em",
        "me oriente sobre investimentos", "me oriente sobre onde investir"
    ]
    
    # Verificar se a mensagem contém palavras-chave de recomendação
    for keyword in recommendation_keywords:
        if keyword in content:
            return True
    
    return False


def _deve_handoff_por_respostas(state: MessagesState, respostas: dict) -> Tuple[bool, Optional[str]]:
    """
    Verifica se a mensagem do usuário pede algo sobre um tópico cuja resposta não está permitida.
    respostas: dict com keys falar_sobre_precos, falar_sobre_risco, recomendar_produtos, fornecer_projecoes, comparar_produtos.
    Retorna (True, nome_do_topico) se pede sobre tópico não permitido; (False, None) caso contrário.
    """
    if not respostas:
        return False, None
    topicos_nao_permitidos = [k for k, v in respostas.items() if v is False]
    if not topicos_nao_permitidos:
        return False, None
    user_msgs = [m for m in state.get("messages", []) if isinstance(m, HumanMessage)]
    if not user_msgs:
        return False, None
    last_user = user_msgs[-1]
    texto_usuario = _extract_text_plain(getattr(last_user, "content", None) or "")
    if not texto_usuario:
        return False, None
    # Mapeamento nome amigável para key
    topic_labels = {
        "falar_sobre_precos": "preços e cotações",
        "falar_sobre_risco": "riscos de investimentos",
        "recomendar_produtos": "recomendação de produtos",
        "fornecer_projecoes": "projeções financeiras",
        "comparar_produtos": "comparação de produtos",
    }
    labels_str = ", ".join(topic_labels.get(t, t) for t in topicos_nao_permitidos)
    prompt = (
        "Você é um classificador. A mensagem do cliente pede informação ou ação sobre algum destes tópicos?\n"
        f"Tópicos (não permitidos para o agente responder): {labels_str}\n\n"
        f"Mensagem do cliente:\n\"\"\"\n{texto_usuario}\n\"\"\"\n\n"
        "Responda com UMA ÚNICA LINHA:\n"
        "- Se a mensagem pedir algo sobre um desses tópicos, responda apenas a CHAVE do tópico: falar_sobre_precos, falar_sobre_risco, recomendar_produtos, fornecer_projecoes ou comparar_produtos.\n"
        "- Se não pedir sobre nenhum deles, responda apenas: NENHUM\n"
        "Não invente. Só a chave exata ou NENHUM."
    )
    try:
        resp = model.invoke([HumanMessage(content=prompt)])
        out = (getattr(resp, "content", None) or str(resp)).strip().lower()
        if not out or out == "nenhum":
            return False, None
        for t in topicos_nao_permitidos:
            if t.lower() in out or out in t.lower():
                return True, t
        return True, topicos_nao_permitidos[0]
    except Exception:
        return False, None


def _trigger_calculation_webhook_sync(
    num1: float,
    operator: str,
    num2: float,
    result: float,
    user_message: str
) -> dict:
    """
    Dispara webhook de forma síncrona (visível no grafo).
    Retorna status da execução.
    """
    webhook_url = os.getenv('CALCULATION_WEBHOOK_URL')
    
    if not webhook_url:
        return {"status": "skipped", "reason": "no_url_configured"}
    
    payload = {
        "event": "calculation_executed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "num1": num1,
            "operator": operator,
            "num2": num2,
            "result": result,
            "user_message": user_message,
            "expression": f"{num1} {operator} {num2} = {result}"
        }
    }
    
    try:
        import requests
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return {
            "status": "success",
            "status_code": response.status_code,
            "url": webhook_url
        }
    except ImportError:
        return {
            "status": "error",
            "error": "requests library not installed",
            "url": webhook_url
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": webhook_url
        }


def _trigger_calculation_webhook(
    num1: float,
    operator: str,
    num2: float,
    result: float,
    user_message: str
) -> None:
    """
    Dispara webhook quando um cálculo é executado.
    Executa de forma assíncrona para não bloquear a resposta.
    """
    try:
        # Obter URL do webhook da variável de ambiente
        webhook_url = os.getenv('CALCULATION_WEBHOOK_URL')
        
        if not webhook_url:
            # Se não houver webhook configurado, apenas retornar
            return
        
        # Preparar payload
        payload = {
            "event": "calculation_executed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "num1": num1,
                "operator": operator,
                "num2": num2,
                "result": result,
                "user_message": user_message,
                "expression": f"{num1} {operator} {num2} = {result}"
            }
        }
        
        # Executar webhook em thread separada (não bloqueia)
        def _send_webhook():
            try:
                import requests
                response = requests.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5  # Timeout de 5 segundos
                )
                # Log opcional (pode ser removido em produção)
                if os.getenv('DEBUG_CALCULATION_WEBHOOK', 'false').lower() == 'true':
                    print(f"[Calculation Webhook] Status: {response.status_code}, URL: {webhook_url}")
            except ImportError:
                # Se requests não estiver instalado, apenas logar
                if os.getenv('DEBUG_CALCULATION_WEBHOOK', 'false').lower() == 'true':
                    print("[Calculation Webhook] Biblioteca 'requests' não instalada. Instale com: pip install requests")
            except Exception as e:
                # Não quebrar o fluxo se webhook falhar
                if os.getenv('DEBUG_CALCULATION_WEBHOOK', 'false').lower() == 'true':
                    print(f"[Calculation Webhook] Erro: {e}")
        
        # Executar em background
        thread = Thread(target=_send_webhook, daemon=True)
        thread.start()
        
    except Exception as e:
        # Não quebrar o fluxo se houver erro
        if os.getenv('DEBUG_CALCULATION_WEBHOOK', 'false').lower() == 'true':
            print(f"[Calculation Webhook] Erro ao configurar webhook: {e}")


def webhook_node(state: MessagesState) -> dict:
    """
    Nó de webhook para cálculos.
    Extrai dados do cálculo e dispara webhook se configurado.
    Visível no grafo LangGraph.
    """
    # Buscar última mensagem (deve ser do calculation_node)
    messages = state.get("messages", [])
    if not messages:
        return state
    
    last_message = messages[-1]
    
    # Extrair dados do cálculo
    calculation_data = None
    if hasattr(last_message, 'additional_kwargs') and last_message.additional_kwargs:
        calculation_data = last_message.additional_kwargs.get("calculation_data")
    
    if not calculation_data:
        # Se não houver dados, apenas passar adiante
        return state
    
    # Verificar se webhook está configurado
    webhook_url = os.getenv('CALCULATION_WEBHOOK_URL')
    
    if webhook_url:
        # Executar webhook (síncrono para ser visível no grafo)
        try:
            webhook_result = _trigger_calculation_webhook_sync(
                calculation_data["num1"],
                calculation_data["operator"],
                calculation_data["num2"],
                calculation_data["result"],
                calculation_data["user_message"]
            )
            
            # Adicionar mensagem indicando webhook executado
            webhook_message = AIMessage(
                content="",
                additional_kwargs={
                    "webhook_executed": True,
                    "webhook_url": webhook_url,
                    "webhook_status": webhook_result.get("status", "unknown"),
                    "webhook_result": webhook_result
                }
            )
            return {"messages": [webhook_message]}
        except Exception as e:
            # Em caso de erro, ainda adicionar mensagem para rastreamento
            webhook_message = AIMessage(
                content="",
                additional_kwargs={
                    "webhook_executed": True,
                    "webhook_url": webhook_url,
                    "webhook_status": "error",
                    "webhook_error": str(e)
                }
            )
            return {"messages": [webhook_message]}
    else:
        # Webhook não configurado - passar adiante sem mensagem adicional
        # Mas ainda retornar estado para manter o nó visível no grafo
        return state


def calculation_node(state: MessagesState) -> dict:
    """
    Nó de cálculo determinístico.
    Processa cálculos simples e retorna resposta formatada sem usar LLM ou tools.
    Armazena dados do cálculo em additional_kwargs para uso no webhook_node.
    """
    # Buscar a última mensagem do usuário
    user_messages = [msg for msg in state.get("messages", []) if isinstance(msg, HumanMessage)]
    if not user_messages:
        return state
    
    last_user_message = user_messages[-1]
    
    # Extrair conteúdo
    if not hasattr(last_user_message, 'content'):
        return state
    
    content = _extract_text_content(last_user_message.content)
    
    # Obter mensagem original para o webhook
    original_content = last_user_message.content
    if isinstance(original_content, list):
        original_content = " ".join([str(item) for item in original_content])
    elif not isinstance(original_content, str):
        original_content = str(original_content)
    
    # Detectar cálculo
    calculation = detect_simple_calculation(content)
    
    if calculation is None:
        # Se não detectar cálculo, retornar estado sem modificações
        return state
    
    num1, operator, num2 = calculation
    
    # Executar cálculo
    try:
        result = calculate_simple_expression(num1, operator, num2)
        
        # Formatar operador para exibição
        operator_display = {
            '*': '×',
            '+': '+',
            '-': '-',
            '/': '÷'
        }.get(operator, operator)
        
        # Formatar resultado
        if result == int(result):
            result_str = str(int(result))
        else:
            result_str = str(result)
        
        # Criar mensagem de resposta com dados do cálculo em additional_kwargs
        # Incluir pergunta sobre feedback
        response_content = (
            f"O resultado de {int(num1) if num1 == int(num1) else num1} {operator_display} {int(num2) if num2 == int(num2) else num2} é {result_str}.\n\n"
            "Você gostou do resultado?"
        )
        
        calculation_message = AIMessage(
            content=response_content,
            additional_kwargs={
                "calculation_data": {
                    "num1": num1,
                    "operator": operator,
                    "num2": num2,
                    "result": result,
                    "user_message": original_content
                }
            }
        )
        
        # Não disparar webhook aqui - será feito no webhook_node
        return {"messages": [calculation_message]}
        
    except ValueError as e:
        # Erro no cálculo (ex: divisão por zero)
        error_message = AIMessage(content=f"Erro no cálculo: {str(e)}")
        return {"messages": [error_message]}


def detect_positive_feedback(state: MessagesState) -> bool:
    """
    Detecta se o usuário deu feedback positivo após o cálculo.
    Verifica se a última mensagem é do usuário e contém palavras-chave positivas.
    Verifica se há uma mensagem do usuário APÓS a mensagem do cálculo.
    """
    messages = state.get("messages", [])
    if len(messages) < 2:
        # Precisa ter pelo menos: mensagem do usuário (cálculo) + resposta do cálculo
        return False
    
    # Verificar se a última mensagem é do usuário (resposta à pergunta)
    last_message = messages[-1]
    
    # Se a última mensagem não for do usuário, não há feedback ainda
    if not isinstance(last_message, HumanMessage):
        return False
    
    # Verificar se a penúltima mensagem é do cálculo (deve ter calculation_data)
    if len(messages) >= 2:
        second_last = messages[-2]
        if isinstance(second_last, AIMessage):
            # Verificar se tem calculation_data (indica que veio do calculation_node)
            has_calculation = (
                hasattr(second_last, 'additional_kwargs') and
                second_last.additional_kwargs and
                second_last.additional_kwargs.get("calculation_data") is not None
            )
            if not has_calculation:
                # Não é feedback para um cálculo
                return False
    
    # Extrair conteúdo da última mensagem do usuário
    if not hasattr(last_message, 'content'):
        return False
    
    content = _extract_text_content(last_message.content)
    
    # Palavras-chave de feedback negativo (têm prioridade)
    negative_keywords = [
        "não gostei", "não gostou", "não curti", "não curtiu",
        "errado", "incorreto", "não", "nao", "nope", "no"
    ]
    
    # Verificar feedback negativo primeiro
    for keyword in negative_keywords:
        if keyword in content:
            return False
    
    # Palavras-chave de feedback positivo
    positive_keywords = [
        "sim", "gostei", "gostou", "perfeito", "ótimo", "excelente",
        "obrigado", "obrigada", "valeu", "legal", "bom", "bom demais",
        "correto", "certo", "exato", "preciso", "ok", "okay", "yes",
        "show", "top", "massa", "bacana", "incrível", "fantástico"
    ]
    
    # Verificar se contém palavras-chave positivas
    for keyword in positive_keywords:
        if keyword in content:
            return True
    
    return False


def check_feedback_node(state: MessagesState) -> dict:
    """
    Nó de decisão que avalia feedback do usuário.
    Visível no grafo como nó separado para tornar a condição explícita.
    """
    # Avaliar feedback
    has_positive_feedback = detect_positive_feedback(state)
    
    # Adicionar metadados à última mensagem para indicar resultado da avaliação
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage) and hasattr(last_message, 'additional_kwargs'):
            # Adicionar resultado da avaliação
            if not last_message.additional_kwargs:
                last_message.additional_kwargs = {}
            last_message.additional_kwargs["feedback_evaluated"] = True
            last_message.additional_kwargs["feedback_positive"] = has_positive_feedback
    
    # Retornar estado (a decisão será feita na conditional edge seguinte)
    return state


def should_call_webhook(state: MessagesState) -> str:
    """
    Determina se deve chamar webhook baseado no feedback avaliado.
    Esta função é chamada APÓS check_feedback_node.
    Retorna 'webhook' se feedback positivo, 'end' caso contrário.
    """
    # Verificar feedback (já pode usar metadados se disponível, ou re-avaliar)
    if detect_positive_feedback(state):
        return "webhook"
    
    return "end"


def should_route_after_init(state: MessagesState, config: Optional[RunnableConfig] = None) -> str:
    """
    Router pós-init: decide calculate | handoff | agent com base só na mensagem do usuário.
    Ordem: (1) cálculo, (2) handoff (regras + recomendação), (3) agent.
    A decisão de handoff é feita antes de o agente responder.
    """
    # 1) Cálculo
    user_messages = [msg for msg in state.get("messages", []) if isinstance(msg, HumanMessage)]
    if not user_messages:
        return "agent"
    last_user_message = user_messages[-1]
    if hasattr(last_user_message, "content"):
        content = _extract_text_content(last_user_message.content)
        if detect_simple_calculation(content) is not None:
            return "calculate"

    # 2) Handoff: regras de redirecionamento + respostas permitidas (mesma fonte, S3)
    cfg = (config or {}).get("configurable", {}) or {}
    user_id = cfg.get("user_id", "default")
    backend_url = cfg.get("backend_url") or os.getenv("BACKEND_URL")
    payload = {"user_id": user_id}
    if backend_url:
        payload["backend_url"] = backend_url
    try:
        result = obter_regras_redirecionamento.invoke(payload)
        regras = result.get("regras_redirecionamento") or []
        respostas = result.get("respostas") or dict(RESPOSTAS_PADRAO)
    except Exception as e:
        print(f"[RegrasHandoff] should_route_after_init invoke falhou: {e}")
        regras = list(REGRAS_REDIRECIONAMENTO_PADRAO)
        respostas = dict(RESPOSTAS_PADRAO)
    # Resposta não permitida: recomendar produtos
    if detect_recommendation_request(state) and not respostas.get("recomendar_produtos", True):
        return "handoff"
    # Outros tópicos não permitidos (preços, risco, projeções, comparar)
    deve_resp, _ = _deve_handoff_por_respostas(state, respostas)
    if deve_resp:
        return "handoff"
    # Regras de redirecionamento
    deve, _ = _deve_redirecionar(state["messages"], regras)
    if deve:
        return "handoff"

    # 3) Agent
    return "agent"


def handoff_node(state: MessagesState, config: Optional[RunnableConfig] = None) -> dict:
    """
    Nó de handoff: informa que um assessor humano será acionado.
    Obtém regras e respostas invocando obter_regras_redirecionamento (mesma fonte, S3).
    """
    cfg = (config or {}).get("configurable", {}) or {}
    user_id = cfg.get("user_id", "default")
    backend_url = cfg.get("backend_url") or os.getenv("BACKEND_URL")
    payload = {"user_id": user_id}
    if backend_url:
        payload["backend_url"] = backend_url
    try:
        result = obter_regras_redirecionamento.invoke(payload)
        regras = result.get("regras_redirecionamento") or []
        respostas = result.get("respostas") or dict(RESPOSTAS_PADRAO)
    except Exception as e:
        print(f"[RegrasHandoff] handoff_node invoke falhou: {e}")
        regras = list(REGRAS_REDIRECIONAMENTO_PADRAO)
        respostas = dict(RESPOSTAS_PADRAO)
    print(f"[RegrasHandoff] handoff_node user_id={user_id} backend_url={bool(backend_url)} regras_count={len(regras)}")
    deve_regra, regra_casada = _deve_redirecionar(state["messages"], regras)
    deve_resp, topico_nao_permitido = _deve_handoff_por_respostas(state, respostas)
    if regra_casada:
        reason = regra_casada
    elif topico_nao_permitido:
        reason = f"Resposta não permitida: {topico_nao_permitido}"
    else:
        reason = "Solicitação de recomendação de investimentos"
    handoff_message = AIMessage(
        content=(
            "Para melhor atendê-lo neste assunto, vou encaminhar sua solicitação para um de nossos assessores. "
            "Você receberá um contato em breve."
        ),
        additional_kwargs={
            "handoff": True,
            "handoff_reason": reason,
            "handoff_rule": reason,
        }
    )
    return {"messages": [handoff_message]}


# Agente de compliance: revisor que consulta políticas antes da resposta final
COMPLIANCE_SYSTEM = (
    "Você é um revisor de compliance. Sua tarefa é validar a resposta rascunho do agente principal "
    "à luz das políticas de compliance (LGPD, CVM, Auditoria, PII, Retenção) e das regras específicas cadastradas. "
    "Você recebe a resposta rascunho e a pergunta do usuário. "
    "Use as ferramentas para consultar as políticas que achar relevantes (consultar_politica_lgpd, consultar_politica_cvm, "
    "consultar_politica_auditoria, consultar_politica_pii, consultar_politica_retencao, consultar_regras_especificas). "
    "Depois: (1) Aprove a resposta como está se estiver em conformidade, ou (2) Ajuste apenas o necessário para conformidade "
    "(tom, divulgação de dados, promessas de rentabilidade, etc.) sem mudar o sentido da resposta. "
    "Responda APENAS com o texto final da resposta ao usuário (a resposta validada ou corrigida). "
    "Não explique o que você fez; devolva só o texto que o usuário deve ver."
)

compliance_llm = ChatOpenAI(model=model_name, temperature=0.2)
compliance_llm_with_tools = compliance_llm.bind_tools(COMPLIANCE_TOOLS)
_compliance_tools_by_name = {t.name: t for t in COMPLIANCE_TOOLS}


def compliance_check_node(state: MessagesState, config: Optional[RunnableConfig] = None) -> dict:
    """
    Nó que invoca o agente de compliance para validar a resposta final do agente principal.
    Consulta políticas via tools conforme necessário e devolve o texto validado.
    """
    messages_list = list(state.get("messages", []))
    if not messages_list:
        return state
    last_msg = messages_list[-1]
    if not isinstance(last_msg, AIMessage):
        return state
    draft_content = getattr(last_msg, "content", "") or ""
    if isinstance(draft_content, list):
        draft_content = " ".join(str(x) for x in draft_content)
    last_human = None
    for m in reversed(messages_list):
        if isinstance(m, HumanMessage):
            last_human = m
            break
    user_question = ""
    if last_human and hasattr(last_human, "content"):
        c = last_human.content
        user_question = c if isinstance(c, str) else " ".join(str(x) for x in c)
    cfg = (config or {}).get("configurable", {}) or {}
    backend_url = cfg.get("backend_url") or os.getenv("BACKEND_URL")
    prompt = (
        f"Resposta rascunho do agente:\n\n{draft_content}\n\n"
        f"Pergunta do usuário:\n\n{user_question}\n\n"
        "Consulte as políticas que precisar e devolva o texto final da resposta (validada ou corrigida)."
    )
    compliance_messages = [
        SystemMessage(content=COMPLIANCE_SYSTEM),
        HumanMessage(content=prompt),
    ]
    max_iterations = 10
    for _ in range(max_iterations):
        response = compliance_llm_with_tools.invoke(compliance_messages)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            break
        compliance_messages.append(response)
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", {}) or {}
            if backend_url:
                args = {**args, "backend_url": backend_url}
            tool = _compliance_tools_by_name.get(name)
            if tool:
                try:
                    result = tool.invoke(args)
                    if not isinstance(result, str):
                        result = json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    result = json.dumps({"error": str(e)})
            else:
                result = json.dumps({"error": f"Tool não encontrada: {name}"})
            compliance_messages.append(
                ToolMessage(content=result, tool_call_id=tc.get("id", ""))
            )
    final_content = getattr(response, "content", "") or draft_content
    if isinstance(final_content, list):
        final_content = " ".join(str(x) for x in final_content)
    new_aimessage = AIMessage(
        content=final_content,
        additional_kwargs={"compliance_checked": True}
    )
    messages_list[-1] = new_aimessage
    return {"messages": messages_list}


def should_continue(state: MessagesState, config: Optional[RunnableConfig] = None) -> str:
    """
    Determina o próximo nó após o agent. Handoff já foi decidido antes do agent (router pós-init).
    Ordem: (1) tool_calls -> tools; (2) sem tool_calls -> compliance_check (antes da resposta final).
    """
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "compliance_check"


graph = (
    StateGraph(MessagesState)
    # Adicionar nós
    .add_node("init", init_node)
    .add_node("calculation", calculation_node)  # Nó de cálculo determinístico
    .add_node("check_feedback", check_feedback_node)  # NOVO: nó de decisão explícito (visível no grafo)
    .add_node("webhook", webhook_node)  # Nó de webhook visível no grafo
    .add_node("agent", agent_node)
    .add_node("tools", tool_node)
    .add_node("handoff", handoff_node)
    .add_node("compliance_check", compliance_check_node)
    .add_node("end", end_node)
    # Definir fluxo: START → init → (conditional) → calculation → check_feedback → (conditional) → webhook/end
    .add_edge(START, "init")
    # Conditional edge após init: calculate | handoff | agent (handoff decidido antes do agent)
    .add_conditional_edges(
        "init",
        should_route_after_init,
        {
            "calculate": "calculation",
            "handoff": "handoff",
            "agent": "agent"
        }
    )
    # calculation → check_feedback (nó de decisão explícito)
    .add_edge("calculation", "check_feedback")
    # Conditional edge após check_feedback baseado em feedback do usuário
    .add_conditional_edges(
        "check_feedback",
        should_call_webhook,
        {
            "webhook": "webhook",
            "end": "end"
        }
    )
    .add_edge("webhook", END)  # Webhook termina após execução
    # Após agent: tools ou compliance_check (resposta final passa pelo agente de compliance)
    .add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "compliance_check": "compliance_check"
        }
    )
    .add_edge("tools", "agent")
    .add_edge("compliance_check", "end")
    .add_edge("handoff", END)  # Handoff termina o fluxo
    .add_edge("end", END)
    .compile(name="agent")
)
