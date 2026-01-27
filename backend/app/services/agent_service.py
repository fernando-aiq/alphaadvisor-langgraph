"""
Serviço de Agente usando ReAct pattern para decisões conversacionais.
Implementa traceability e explicability para compliance CVM.
Estilo CFP (Certified Financial Planner) - consultivo, empático e educativo.
"""
import os
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
try:
    from langchain.prompts import PromptTemplate
    PROMPT_AVAILABLE = True
except Exception:
    PromptTemplate = None
    PROMPT_AVAILABLE = False
try:
    from langchain.tools import StructuredTool
    STRUCTURED_TOOL_AVAILABLE = True
except Exception:
    StructuredTool = None
    STRUCTURED_TOOL_AVAILABLE = False
try:
    from langchain.tools import Tool
except Exception:
    Tool = None
try:
    from langchain import hub
    HUB_AVAILABLE = True
except Exception:
    hub = None
    HUB_AVAILABLE = False
try:
    from langchain.agents import create_react_agent, AgentExecutor
    REACT_AVAILABLE = True
except Exception:
    create_react_agent = None
    AgentExecutor = None
    REACT_AVAILABLE = False
try:
    from langchain.agents.react.agent import create_react_agent as create_react_agent_alt
except Exception:
    create_react_agent_alt = None
try:
    from langchain.agents import initialize_agent, AgentType
    INITIALIZE_AGENT_AVAILABLE = True
except Exception:
    initialize_agent = None
    AgentType = None
    INITIALIZE_AGENT_AVAILABLE = False
from langsmith import traceable

from app.services.agent_tools import (
    obter_carteira, obter_perfil, analisar_adequacao, calcular_projecao,
    buscar_oportunidades, analisar_alinhamento_objetivos,
    analisar_diversificacao, recomendar_rebalanceamento
)
from app.services.traceability_service import TraceabilityService
from app.services.explainability_service import ExplainabilityService

# Tentar importar LangGraphAgent
try:
    from app.services.langgraph_agent import LangGraphAgent
    LANGGRAPH_AGENT_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AGENT_AVAILABLE = False
    LangGraphAgent = None
    print(f"[AgentService] LangGraphAgent não disponível: {e}")

class AgentService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY', '')
        model = os.getenv('AI_MODEL', 'gpt-4o')
        
        if api_key:
            self.llm = ChatOpenAI(model=model, temperature=0.7, api_key=api_key)
        else:
            self.llm = None
        
        self.traceability = TraceabilityService()
        self.explainability = ExplainabilityService()
        self.agent_executor = None
        self.langgraph_agent = None
        
        # Usar padrão oficial do LangChain Agent Builder (create_react_agent + AgentExecutor)
        # Este é o padrão recomendado pelo LangChain
        if self.llm:
            try:
                self.agent_executor = self._build_react_agent()
                if self.agent_executor:
                    print("[AgentService] AgentExecutor criado com padrão oficial do LangChain Agent Builder")
            except Exception as e:
                print(f"[AgentService] Erro ao criar agente reativo: {e}")
                self.agent_executor = None
        
        # LangGraphAgent como opção alternativa (não padrão oficial)
        if LANGGRAPH_AGENT_AVAILABLE and LangGraphAgent and not self.agent_executor:
            try:
                self.langgraph_agent = LangGraphAgent()
                print("[AgentService] LangGraphAgent inicializado como alternativa")
            except Exception as e:
                print(f"[AgentService] Erro ao inicializar LangGraphAgent: {e}")
                self.langgraph_agent = None
    
    def _build_react_agent(self) -> Optional[AgentExecutor]:
        """Constrói agente reativo estilo CFP que decide quando usar tools"""
        if not self.llm:
            return None
        
        # Verificar se Tools estão disponíveis antes de tentar criar o agente
        if not STRUCTURED_TOOL_AVAILABLE and not Tool:
            print("[AgentService] Nenhuma implementação de Tool disponível no LangChain instalado. Usando LangGraphAgent como alternativa.")
            return None
        
        try:
            # Criar funções wrapper para as tools
            def analisar_adequacao_wrapper(perfil: str = None):
                """Wrapper para analisar_adequacao - obtém carteira e perfil automaticamente"""
                # Obter perfil se não fornecido
                if perfil is None:
                    perfil_data = obter_perfil()
                    if hasattr(perfil_data, 'model_dump'):
                        perfil_dict = perfil_data.model_dump()
                    elif hasattr(perfil_data, 'dict'):
                        perfil_dict = perfil_data.dict()
                    else:
                        perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
                    perfil = perfil_dict.get('perfilInvestidor', 'conservador').lower()
                
                # Obter carteira
                carteira_data = obter_carteira()
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                resultado = analisar_adequacao(carteira_dict, perfil)
                # Converter resultado para string legível
                if hasattr(resultado, 'model_dump'):
                    result_dict = resultado.model_dump()
                elif hasattr(resultado, 'dict'):
                    result_dict = resultado.dict()
                else:
                    result_dict = resultado
                
                problemas_str = ', '.join(result_dict.get('problemas', [])) if result_dict.get('problemas') else 'Nenhum problema identificado'
                recomendacoes_str = ', '.join(result_dict.get('recomendacoes', [])) if result_dict.get('recomendacoes') else 'Nenhuma recomendação específica'
                
                return f"Score de adequação: {result_dict.get('score', 0)}/100. Problemas identificados: {problemas_str}. Recomendações: {recomendacoes_str}."
            
            def buscar_oportunidades_wrapper(perfil: str = None, problemas: str = ""):
                """Wrapper para buscar_oportunidades - obtém perfil automaticamente se não fornecido"""
                # Obter perfil se não fornecido
                if perfil is None:
                    perfil_data = obter_perfil()
                    if hasattr(perfil_data, 'model_dump'):
                        perfil_dict = perfil_data.model_dump()
                    elif hasattr(perfil_data, 'dict'):
                        perfil_dict = perfil_data.dict()
                    else:
                        perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
                    perfil = perfil_dict.get('perfilInvestidor', 'conservador').lower()
                
                problemas_list = [p.strip() for p in problemas.split(",")] if problemas else []
                oportunidades = buscar_oportunidades(perfil, problemas_list)
                
                # Converter para string legível
                resultado = []
                for op in oportunidades:
                    if hasattr(op, 'model_dump'):
                        op_dict = op.model_dump()
                    elif hasattr(op, 'dict'):
                        op_dict = op.dict()
                    else:
                        op_dict = op
                    resultado.append(f"{op_dict.get('nome', 'N/A')} ({op_dict.get('tipo', 'N/A')}): {op_dict.get('justificativa', '')}")
                
                return "\n".join(resultado) if resultado else "Nenhuma oportunidade encontrada."
            
            def analisar_alinhamento_objetivos_wrapper():
                """Wrapper para analisar_alinhamento_objetivos - obtém carteira e perfil automaticamente"""
                carteira_data = obter_carteira()
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                # Obter perfil usando obter_perfil
                perfil_data = obter_perfil()
                if hasattr(perfil_data, 'model_dump'):
                    perfil_dict = perfil_data.model_dump()
                elif hasattr(perfil_data, 'dict'):
                    perfil_dict = perfil_data.dict()
                else:
                    perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
                
                resultado = analisar_alinhamento_objetivos(carteira_dict, perfil_dict)
                if hasattr(resultado, 'model_dump'):
                    result_dict = resultado.model_dump()
                elif hasattr(resultado, 'dict'):
                    result_dict = resultado.dict()
                else:
                    result_dict = resultado
                
                resposta = f"Análise de Alinhamento com Objetivos (Score: {result_dict.get('score_geral', 0)}/100):\n\n"
                resposta += f"Curto Prazo: {'✓ Alinhado' if result_dict.get('alinhado_curto_prazo') else '✗ Não alinhado'}\n"
                if result_dict.get('problemas_curto'):
                    resposta += f"  Problemas: {', '.join(result_dict.get('problemas_curto', []))}\n"
                if result_dict.get('recomendacoes_curto'):
                    resposta += f"  Recomendações: {', '.join(result_dict.get('recomendacoes_curto', []))}\n"
                
                resposta += f"\nMédio Prazo: {'✓ Alinhado' if result_dict.get('alinhado_medio_prazo') else '✗ Não alinhado'}\n"
                if result_dict.get('problemas_medio'):
                    resposta += f"  Problemas: {', '.join(result_dict.get('problemas_medio', []))}\n"
                if result_dict.get('recomendacoes_medio'):
                    resposta += f"  Recomendações: {', '.join(result_dict.get('recomendacoes_medio', []))}\n"
                
                resposta += f"\nLongo Prazo: {'✓ Alinhado' if result_dict.get('alinhado_longo_prazo') else '✗ Não alinhado'}\n"
                if result_dict.get('problemas_longo'):
                    resposta += f"  Problemas: {', '.join(result_dict.get('problemas_longo', []))}\n"
                if result_dict.get('recomendacoes_longo'):
                    resposta += f"  Recomendações: {', '.join(result_dict.get('recomendacoes_longo', []))}\n"
                
                return resposta
            
            def analisar_diversificacao_wrapper():
                """Wrapper para analisar_diversificacao - obtém carteira automaticamente"""
                carteira_data = obter_carteira()
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                resultado = analisar_diversificacao(carteira_dict)
                if hasattr(resultado, 'model_dump'):
                    result_dict = resultado.model_dump()
                elif hasattr(resultado, 'dict'):
                    result_dict = resultado.dict()
                else:
                    result_dict = resultado
                
                resposta = f"Análise de Diversificação (Score: {result_dict.get('score_diversificacao', 0)}/100):\n\n"
                if result_dict.get('problemas'):
                    resposta += f"Problemas identificados:\n"
                    for problema in result_dict.get('problemas', []):
                        resposta += f"  - {problema}\n"
                if result_dict.get('recomendacoes'):
                    resposta += f"\nRecomendações:\n"
                    for rec in result_dict.get('recomendacoes', []):
                        resposta += f"  - {rec}\n"
                
                resposta += f"\nConcentração por Classe:\n"
                for classe, pct in result_dict.get('concentracao_por_classe', {}).items():
                    resposta += f"  - {classe}: {pct:.1f}%\n"
                
                return resposta
            
            def recomendar_rebalanceamento_wrapper(perfil: str = None):
                """Wrapper para recomendar_rebalanceamento - obtém carteira e perfil automaticamente"""
                # Obter perfil se não fornecido
                if perfil is None:
                    perfil_data = obter_perfil()
                    if hasattr(perfil_data, 'model_dump'):
                        perfil_dict = perfil_data.model_dump()
                    elif hasattr(perfil_data, 'dict'):
                        perfil_dict = perfil_data.dict()
                    else:
                        perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
                    perfil = perfil_dict.get('perfilInvestidor', 'conservador').lower()
                
                carteira_data = obter_carteira()
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                resultado = recomendar_rebalanceamento(carteira_dict, perfil)
                if hasattr(resultado, 'model_dump'):
                    result_dict = resultado.model_dump()
                elif hasattr(resultado, 'dict'):
                    result_dict = resultado.dict()
                else:
                    result_dict = resultado
                
                resposta = f"Recomendação de Rebalanceamento:\n"
                resposta += f"Necessário: {'Sim' if result_dict.get('necessario') else 'Não'}\n"
                resposta += f"Justificativa: {result_dict.get('justificativa', '')}\n"
                resposta += f"Impacto Esperado: {result_dict.get('impacto_esperado', '')}\n"
                
                if result_dict.get('ajustes_sugeridos'):
                    resposta += f"\nAjustes Sugeridos:\n"
                    for ajuste in result_dict.get('ajustes_sugeridos', []):
                        resposta += f"  - {ajuste.get('acao', '')}: R$ {ajuste.get('valor', 0):,.2f} (de {ajuste.get('de', '')} para {ajuste.get('para', '')})\n"
                        resposta += f"    Justificativa: {ajuste.get('justificativa', '')}\n"
                
                return resposta
            
            # Wrapper para obter_carteira que retorna string legível
            def obter_perfil_wrapper():
                """Wrapper que retorna string legível do perfil do cliente"""
                perfil_data = obter_perfil()
                if hasattr(perfil_data, 'model_dump'):
                    perfil_dict = perfil_data.model_dump()
                elif hasattr(perfil_data, 'dict'):
                    perfil_dict = perfil_data.dict()
                else:
                    perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
                
                nome = perfil_dict.get('nome', 'João')
                idade = perfil_dict.get('idade', 38)
                profissao = perfil_dict.get('profissao', 'Profissional de Tecnologia')
                perfil_investidor = perfil_dict.get('perfilInvestidor', 'conservador')
                patrimonio = perfil_dict.get('patrimonioInvestido', 0)
                dinheiro_parado = perfil_dict.get('dinheiroParado', 0)
                aporte_mensal = perfil_dict.get('aporteMensal', 0)
                objetivo = perfil_dict.get('objetivo', {})
                comportamento = perfil_dict.get('comportamento', {})
                
                resultado = f"Perfil do Cliente {nome}:\n"
                resultado += f"- Idade: {idade} anos\n"
                resultado += f"- Profissão: {profissao}\n"
                resultado += f"- Perfil de Investidor: {perfil_investidor.upper()}\n"
                resultado += f"- Patrimônio Investido: R$ {patrimonio:,.2f}\n"
                resultado += f"- Dinheiro Parado: R$ {dinheiro_parado:,.2f}\n"
                resultado += f"- Aporte Mensal: R$ {aporte_mensal:,.2f}\n"
                if objetivo:
                    resultado += f"- Objetivo: {objetivo.get('descricao', 'N/A')}\n"
                if comportamento:
                    resultado += f"- Comportamento: Prefere estabilidade, não gosta de volatilidade\n"
                
                return resultado
            
            def obter_carteira_wrapper():
                """Wrapper que retorna string legível e completa da carteira"""
                carteira_data = obter_carteira()
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                total = carteira_dict.get('total', 0)
                dinheiro_parado = carteira_dict.get('dinheiroParado', 0)
                distribuicao = carteira_dict.get('distribuicaoPercentual', {})
                investimentos = carteira_dict.get('investimentos', [])
                adequacao = carteira_dict.get('adequacaoPerfil', {})
                
                # Construir resposta detalhada
                resposta = f"Carteira do João:\n"
                resposta += f"Patrimônio Investido: R$ {total:,.2f}\n"
                resposta += f"Dinheiro Parado: R$ {dinheiro_parado:,.2f}\n"
                resposta += f"Total Disponível: R$ {total + dinheiro_parado:,.2f}\n\n"
                resposta += f"Distribuição:\n"
                resposta += f"- Renda Fixa: {distribuicao.get('rendaFixa', 0):.1f}%\n"
                resposta += f"- Renda Variável: {distribuicao.get('rendaVariavel', 0):.1f}%\n"
                resposta += f"- Liquidez: {distribuicao.get('liquidez', 0):.1f}%\n\n"
                
                if investimentos:
                    resposta += f"Investimentos ({len(investimentos)}):\n"
                    for inv in investimentos[:6]:  # Todos os investimentos
                        resposta += f"- {inv.get('nome', 'N/A')}: R$ {inv.get('valor', 0):,.2f} ({inv.get('tipo', 'N/A')})\n"
                
                if adequacao and adequacao.get('alertas'):
                    resposta += f"\nAlertas:\n"
                    for alerta in adequacao.get('alertas', []):
                        resposta += f"- {alerta.get('mensagem', '')}\n"
                
                return resposta
            
            # Criar tools (StructuredTool se disponível, senão Tool)
            def _make_tool(func, name, description):
                if STRUCTURED_TOOL_AVAILABLE and StructuredTool:
                    return StructuredTool.from_function(func=func, name=name, description=description)
                if Tool:
                    return Tool(name=name, func=func, description=description)
                # Retornar None em vez de lançar erro - a verificação prévia já foi feita
                return None

            tools = [
                _make_tool(
                    func=obter_perfil_wrapper,
                    name="obter_perfil",
                    description="Busca o perfil completo do cliente, incluindo perfil de investidor (conservador/moderado/arrojado). Use SEMPRE quando o cliente perguntar sobre seu perfil de investidor ou quando precisar saber o perfil para fazer análises. Retorna informações sobre nome, idade, profissão, perfil de investidor e outros dados do cliente."
                ),
                _make_tool(
                    func=obter_carteira_wrapper,
                    name="obter_carteira",
                    description="Busca dados completos da carteira do cliente. Use APENAS quando o cliente perguntar especificamente sobre sua carteira atual, saldo, investimentos ou patrimônio. Retorna informações sobre total, distribuição percentual e investimentos."
                ),
                _make_tool(
                    func=analisar_adequacao_wrapper,
                    name="analisar_adequacao",
                    description="Analisa se a carteira está adequada ao perfil do investidor. Use SEMPRE quando o cliente perguntar sobre adequação ao perfil, se a carteira está adequada, ou sobre problemas na carteira. Obtém a carteira automaticamente. Parâmetro: perfil (str: 'conservador', 'moderado', 'arrojado', padrão: 'conservador')."
                ),
                _make_tool(
                    func=analisar_alinhamento_objetivos_wrapper,
                    name="analisar_alinhamento_objetivos",
                    description="Analisa se a carteira está alinhada com objetivos de curto, médio e longo prazo. Use SEMPRE quando o cliente perguntar sobre alinhamento com objetivos, se está alinhado com curto/médio/longo prazo, ou sobre adequação aos horizontes temporais. Obtém carteira e perfil automaticamente. Retorna análise detalhada por horizonte temporal."
                ),
                _make_tool(
                    func=analisar_diversificacao_wrapper,
                    name="analisar_diversificacao",
                    description="Analisa diversificação da carteira por classe de ativo e por ativo individual. Use SEMPRE quando o cliente perguntar sobre diversificação, concentração, ou se precisa diversificar mais. Obtém carteira automaticamente. Retorna análise de concentração e recomendações."
                ),
                _make_tool(
                    func=recomendar_rebalanceamento_wrapper,
                    name="recomendar_rebalanceamento",
                    description="Gera recomendações específicas de rebalanceamento da carteira. Use SEMPRE quando o cliente perguntar sobre ajustes, rebalanceamento, ou se precisa fazer mudanças na alocação. Obtém carteira automaticamente. Parâmetro: perfil (str: 'conservador', 'moderado', 'arrojado', padrão: 'conservador')."
                ),
                _make_tool(
                    func=calcular_projecao,
                    name="calcular_projecao",
                    description="Calcula projeção de investimento considerando aportes mensais e rentabilidade. Use APENAS quando o cliente perguntar sobre projeções, objetivos financeiros, ou quanto precisa investir. Parâmetros: valor_atual (float), aporte_mensal (float), prazo_anos (int), rentabilidade_anual (float, opcional, padrão 10%)."
                ),
                _make_tool(
                    func=buscar_oportunidades_wrapper,
                    name="buscar_oportunidades",
                    description="Busca oportunidades de investimento adequadas ao perfil. Use APENAS quando o cliente pedir recomendações específicas de investimentos ou oportunidades. Parâmetros: perfil (str: 'conservador', 'moderado', 'arrojado'), problemas (str separado por vírgulas, ex: 'liquidez baixa,renda variável alta')."
                ),
            ]
            
            # Filtrar None da lista de tools (caso alguma tool não tenha sido criada)
            tools = [tool for tool in tools if tool is not None]
            
            # Verificar se há tools válidas
            if not tools:
                print("[AgentService] Nenhuma tool válida foi criada. Usando LangGraphAgent como alternativa.")
                return None
            
            # Usar prompt oficial do LangChain Hub (padrão ReAct) - OBRIGATÓRIO
            # Este é o padrão oficial do LangChain Agent Builder
            prompt = None
            if HUB_AVAILABLE and hub:
                try:
                    print("[AgentService] Carregando prompt oficial do LangChain Hub (hwchase17/react)...")
                    prompt = hub.pull("hwchase17/react")
                    print("[AgentService] Prompt oficial do LangChain Hub carregado com sucesso")
                except Exception as e:
                    print(f"[AgentService] ERRO ao carregar prompt do hub: {e}")
                    print("[AgentService] Tentando novamente com timeout aumentado...")
                    import time
                    time.sleep(2)  # Aguardar antes de tentar novamente
                    try:
                        prompt = hub.pull("hwchase17/react")
                        print("[AgentService] Prompt oficial carregado na segunda tentativa")
                    except Exception as e2:
                        print(f"[AgentService] ERRO na segunda tentativa: {e2}")
                        print("[AgentService] O prompt do hub é OBRIGATÓRIO para o padrão oficial. Verifique conexão com internet.")
                        raise ImportError(f"Falha ao carregar prompt oficial do LangChain Hub: {e2}. O padrão oficial requer hub.pull('hwchase17/react').")
            
            # Se não conseguiu carregar do hub, lançar erro (padrão oficial requer o hub)
            if prompt is None:
                raise ImportError("Prompt do LangChain Hub não disponível. O padrão oficial do Agent Builder requer hub.pull('hwchase17/react'). Verifique se langchainhub está instalado e há conexão com internet.")
            
            # Criar agente reativo usando padrão oficial do LangChain Agent Builder
            # Este é o padrão EXATO usado pelo LangChain Agent Builder oficial
            agent_executor = None
            if REACT_AVAILABLE and create_react_agent:
                print("[AgentService] Criando agente com create_react_agent (padrão oficial LangChain Agent Builder)")
                print("[AgentService] Usando prompt oficial do hub: hwchase17/react")
                
                # Padrão oficial: create_react_agent(llm, tools, prompt)
                agent = create_react_agent(self.llm, tools, prompt)
                
                # Padrão oficial: AgentExecutor com configurações padrão
                agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True,
                    handle_parsing_errors=True,  # Padrão oficial para recuperação de erros
                    max_iterations=15,  # Padrão oficial
                    return_intermediate_steps=True  # Para rastreamento
                )
                print("[AgentService] AgentExecutor criado com sucesso usando padrão oficial do LangChain Agent Builder")
            elif create_react_agent_alt:
                agent = create_react_agent_alt(self.llm, tools, prompt)
                agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=5
                )
            elif INITIALIZE_AGENT_AVAILABLE and initialize_agent and AgentType:
                # Fallback compatível com versões antigas do LangChain
                agent_executor = initialize_agent(
                    tools=tools,
                    llm=self.llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                    max_iterations=5,
                    agent_kwargs={
                        "prefix": (
                            "Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter. "
                            "Sua abordagem é consultiva, empática e educativa, estilo CFP. "
                            "IMPORTANTE: O cliente tem perfil de investidor CONSERVADOR. Sempre considere este perfil ao fazer recomendações e análises. "
                            "NÃO pergunte sobre o perfil de investidor do cliente - assuma que é conservador e use isso como contexto em todas as respostas. "
                            "Você TEM acesso aos dados do cliente João através das ferramentas quando disponíveis. "
                            "SEMPRE tente responder a pergunta do cliente, mesmo que não tenha todos os dados. "
                            "Se faltarem dados específicos, forneça orientações gerais baseadas em boas práticas e pergunte quais informações adicionais seriam úteis. "
                            "Use ferramentas quando necessário para responder perguntas sobre carteira, "
                            "adequação, projeções e recomendações, mas se não funcionarem, responda com orientações gerais. "
                            "Sempre termine com próximos passos práticos ou perguntas para obter mais informações quando necessário."
                        )
                    }
                )
            else:
                raise ImportError("Nenhuma implementação de agente ReAct disponível no LangChain instalado.")

            return agent_executor
            
        except Exception as e:
            print(f"[AgentService] Erro ao criar agente reativo: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def _detect_intent(self, message: str) -> Optional[str]:
        """Detecta intenção do usuário para forçar uso de tools quando necessário"""
        message_lower = message.lower().strip()
        
        # Normalizar erros comuns de digitação
        message_normalized = message_lower.replace('mminha', 'minha').replace('cartiera', 'carteira').replace('cartiera', 'carteira')
        
        # Detectar perguntas sobre carteira (mais tolerante a variações)
        carteira_keywords = [
            'minha carteira', 'meu saldo', 'meus investimentos', 'meu patrimônio',
            'carteira', 'saldo', 'investimentos', 'patrimônio',
            'qual a minha', 'qual meu', 'quanto tenho', 'quanto eu tenho',
            'meus ativos', 'meus recursos', 'meu portfólio'
        ]
        
        # Verificar se contém palavras-chave (mais flexível)
        for keyword in carteira_keywords:
            if keyword in message_normalized or keyword in message_lower:
                return "obter_carteira"
        
        # Detectar perguntas sobre adequação
        adequacao_keywords = ['adequada', 'adequado', 'perfil', 'está adequada', 'adequação', 'perfil de risco']
        if any(keyword in message_lower for keyword in adequacao_keywords):
            return "analisar_adequacao"
        
        # Detectar perguntas sobre alinhamento com objetivos
        alinhamento_keywords = [
            'alinhado', 'alinhamento', 'objetivos', 'curto prazo', 'médio prazo', 'longo prazo',
            'curto/médio/longo', 'horizonte', 'está alinhado', 'alinhado com'
        ]
        if any(keyword in message_lower for keyword in alinhamento_keywords):
            return "analisar_alinhamento_objetivos"
        
        # Detectar perguntas sobre diversificação
        diversificacao_keywords = ['diversificação', 'diversificado', 'concentração', 'concentrado', 'diversificar']
        if any(keyword in message_lower for keyword in diversificacao_keywords):
            return "analisar_diversificacao"
        
        # Detectar perguntas sobre rebalanceamento/ajustes/alocação
        rebalanceamento_keywords = [
            'rebalanceamento', 'rebalancear', 'ajustes', 'ajustar', 'mudanças', 'revisão',
            'alocação', 'alocacao', 'mudar alocação', 'mudar alocacao', 'mudança de alocação',
            'mudança de alocacao', 'realocar', 'realocação', 'realocacao', 'mudar minha alocação',
            'mudar minha alocacao', 'vale a pena mudar', 'mudar alocação', 'ajustar alocação',
            'rebalancear carteira', 'revisar alocação'
        ]
        if any(keyword in message_lower for keyword in rebalanceamento_keywords):
            return "recomendar_rebalanceamento"
        
        # Detectar perguntas sobre projeções
        projecao_keywords = ['projeção', 'quanto preciso', 'quanto investir', 'objetivo', '1 milhão']
        if any(keyword in message_lower for keyword in projecao_keywords):
            return "calcular_projecao"
        
        # Detectar pedidos de recomendações
        recomendacao_keywords = ['recomendação', 'recomenda', 'oportunidade', 'aplicar', 'investir em']
        if any(keyword in message_lower for keyword in recomendacao_keywords):
            return "buscar_oportunidades"
        
        return None
    
    @traceable(
        name="process_message",
        project_name=os.getenv('LANGSMITH_PROJECT', 'alphaadvisor')
    )
    def process_message(self, message: str, context: Optional[List] = None, agent_builder_config: Optional[Dict] = None) -> Dict:
        """
        Processa mensagem do usuário usando LangGraph (preferido) ou agente reativo (fallback).
        Retorna resposta com trace_id e explicação.
        Se agent_builder_config for fornecido, aplica configurações customizadas (persona, instruções, etc.).
        """
        # Aplicar configurações do agent_builder se disponíveis
        custom_persona = None
        custom_instrucoes = None
        custom_regras = None
        
        if agent_builder_config:
            custom_persona = agent_builder_config.get('persona', '')
            custom_instrucoes = agent_builder_config.get('instrucoes', '')
            custom_regras = agent_builder_config.get('regras', [])
            
            if custom_persona or custom_instrucoes or custom_regras:
                print(f"[AgentService] Aplicando configurações customizadas do Agent Builder")
                print(f"[AgentService] Persona: {custom_persona[:50] if custom_persona else 'N/A'}...")
                print(f"[AgentService] Instruções: {custom_instrucoes[:50] if custom_instrucoes else 'N/A'}...")
                print(f"[AgentService] Regras: {len(custom_regras)} regras customizadas")
        
        # Se houver grafo customizado, recriar LangGraphAgent com ele
        if agent_builder_config and agent_builder_config.get('graph_structure'):
            try:
                from app.services.langgraph_agent import LangGraphAgent
                print("[AgentService] Criando LangGraphAgent com grafo customizado")
                custom_langgraph_agent = LangGraphAgent(custom_graph_config=agent_builder_config)
                if custom_langgraph_agent.graph:
                    return custom_langgraph_agent.process_message(message, context=context)
            except Exception as e:
                print(f"[AgentService] Erro ao usar grafo customizado, usando padrão: {e}")
                import traceback
                traceback.print_exc()
        
        # Usar AgentExecutor oficial do LangChain (padrão oficial do Agent Builder)
        # Este é o padrão recomendado pelo LangChain
        if self.agent_executor:
            try:
                print("[AgentService] Usando AgentExecutor (padrão oficial LangChain Agent Builder)")
                # Preparar mensagem com contexto se disponível
                message_with_context = message
                if context and len(context) > 0:
                    context_text = "\n\nHistórico da conversa:\n"
                    for msg in context[-6:]:
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        if role == 'user':
                            context_text += f"Cliente: {content}\n"
                        elif role == 'assistant':
                            context_text += f"Assessor: {content}\n"
                    message_with_context = f"{context_text}\n\nPergunta atual do cliente: {message}"
                
                # Executar usando padrão oficial do LangChain Agent Builder
                import time
                start_time = time.time()
                result = self.agent_executor.invoke({"input": message_with_context})
                duration_ms = (time.time() - start_time) * 1000
                
                resposta = result.get("output", "")
                tools_used = []
                intermediate_steps_formatted = []
                
                # Capturar e converter intermediate_steps do AgentExecutor oficial
                intermediate_steps = result.get("intermediate_steps", [])
                for step in intermediate_steps:
                    if len(step) >= 2:
                        tool_action = step[0]
                        observation = step[1]
                        tool_name = None
                        tool_input = {}
                        if hasattr(tool_action, 'tool'):
                            tool_name = tool_action.tool
                        elif hasattr(tool_action, 'name'):
                            tool_name = tool_action.name
                        elif isinstance(tool_action, dict):
                            tool_name = tool_action.get('tool', tool_action.get('name'))
                        if hasattr(tool_action, 'tool_input'):
                            tool_input = tool_action.tool_input or {}
                        elif isinstance(tool_action, dict):
                            tool_input = tool_action.get('tool_input', {})
                        if not isinstance(tool_input, dict):
                            tool_input = {} if tool_input is None else {"input": tool_input}
                        if tool_name and tool_name not in tools_used:
                            tools_used.append(tool_name)
                        intermediate_steps_formatted.append({
                            "thought": "",
                            "action": {"tool": tool_name} if tool_name else {},
                            "action_input": tool_input,
                            "observation": observation if isinstance(observation, str) else str(observation)
                        })
                
                # Criar trace
                model = os.getenv('AI_MODEL', 'gpt-4o')
                trace_id = self.traceability.create_trace(message, context=context, model=model)
                self.traceability.set_route(trace_id, 'react_agent_executor')
                self.traceability.add_raw_prompt(trace_id, message_with_context)
                self.traceability.add_raw_response(trace_id, resposta)
                
                # Popular reasoning_steps para /api/trace/<id>/steps (estilo LangGraph Studio)
                for step in intermediate_steps_formatted:
                    act = step.get("action", {})
                    tool_name = act.get("tool") if isinstance(act, dict) else None
                    if tool_name:
                        inp = step.get("action_input")
                        out = step.get("observation")
                        self.traceability.add_reasoning_step_enhanced(
                            trace_id, 'action',
                            content=tool_name,
                            tool=tool_name,
                            input_data=inp if isinstance(inp, dict) else ({} if inp is None else {"input": inp}),
                            output_data=out if isinstance(out, dict) else ({"result": out} if out is not None else None)
                        )
                
                # Registrar tool calls
                for tool_name in tools_used:
                    self.traceability.add_tool_call(trace_id, tool_name, {}, {}, None)
                
                self.traceability.add_event(
                    trace_id,
                    'agent_executor_invoke',
                    {
                        'duration_ms': duration_ms,
                        'tools_used': tools_used,
                        'output_length': len(resposta)
                    }
                )
                
                self.traceability.finalize_trace(
                    trace_id,
                    {"resposta": resposta},
                    {"tools_used": tools_used, "source": "langchain_agent_builder_official"}
                )
                
                return {
                    "response": resposta,
                    "trace_id": trace_id,
                    "explicacao": {"tools_used": tools_used},
                    "intermediate_steps": intermediate_steps_formatted
                }
            except Exception as e:
                print(f"[AgentService] Erro no AgentExecutor, tentando LangGraphAgent: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback para LangGraphAgent se AgentExecutor não disponível
        if self.langgraph_agent:
            try:
                print("[AgentService] Usando LangGraphAgent como fallback")
                return self.langgraph_agent.process_message(message, context=context)
            except Exception as e:
                print(f"[AgentService] Erro no LangGraphAgent: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback para implementação legacy
        print("[AgentService] Usando implementação legacy (ReAct)")
        # Criar trace com contexto e model
        model = os.getenv('AI_MODEL', 'gpt-4o')
        trace_id = self.traceability.create_trace(message, context=context, model=model)
        
        try:
            # Preparar mensagem com contexto se disponível
            message_with_context = message
            if context and len(context) > 0:
                # Construir histórico de conversa para incluir no input
                context_text = "\n\nHistórico da conversa:\n"
                for msg in context[-6:]:  # Últimas 6 mensagens para não exceder tokens
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        context_text += f"Cliente: {content}\n"
                    elif role == 'assistant':
                        context_text += f"Assessor: {content}\n"
                message_with_context = f"{context_text}\n\nPergunta atual do cliente: {message}"
                print(f"[AgentService] Contexto incluído: {len(context)} mensagens anteriores")
            
            # Verificar se é uma confirmação curta e reutilizar intent do contexto
            message_lower = message.lower().strip()
            short_confirmations = ['ok', 'sim', 'tudo bem', 'pode ser', 'pode', 'claro', 'entendi', 'beleza', 'tá bom']
            
            if message_lower in short_confirmations and context:
                # Procurar a última mensagem do usuário no contexto que não seja confirmação
                last_user_intent = None
                for i in range(len(context) - 1, -1, -1):
                    msg = context[i]
                    if msg.get('role') == 'user':
                        last_user_msg = msg.get('content', '').lower().strip()
                        # Se não for outra confirmação curta, detectar intent dessa mensagem
                        if last_user_msg not in short_confirmations:
                            last_user_intent = self._detect_intent(msg.get('content', ''))
                            break
                
                if last_user_intent:
                    intent = last_user_intent
                    print(f"[AgentService] Confirmação detectada, reutilizando intent: {intent}")
                else:
                    intent = self._detect_intent(message)
            else:
                # Detectar intenção PRIMEIRO (antes de verificar agente)
                intent = self._detect_intent(message)
            
            print(f"[AgentService] Mensagem: '{message}', Intenção detectada: {intent}")
            
            # Registrar evento de detecção de intenção
            self.traceability.add_event(
                trace_id,
                'intent_detection',
                {
                    'message': message[:200],  # Truncate for event log
                    'intent': intent,
                    'method': 'keyword_matching'
                },
                {'context_length': len(context) if context else 0}
            )
            
            if intent:
                self.traceability.set_intent(trace_id, intent)
            
            # Se detectou intenção de análise, executar análises completas
            if intent == "analisar_alinhamento_objetivos":
                print("[AgentService] Intenção detectada: analisar_alinhamento_objetivos, executando análise completa")
                self.traceability.add_event(trace_id, 'route_decision', {'route': 'bypass', 'reason': 'full_analysis_required'})
                self.traceability.set_route(trace_id, 'bypass')
                
                # Executar análise completa: carteira + adequação + alinhamento + diversificação
                from app.services.agent_tools import obter_carteira, analisar_adequacao, analisar_alinhamento_objetivos, analisar_diversificacao, recomendar_rebalanceamento
                import time
                
                try:
                    from app.routes.cliente import PERFIL_JOAO
                except:
                    PERFIL_JOAO = {}
                
                # Tool: obter_carteira
                start_time = time.time()
                carteira_data = obter_carteira()
                duration_ms = (time.time() - start_time) * 1000
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                self.traceability.add_tool_call(
                    trace_id, 'obter_carteira',
                    {'perfil': 'conservador'},
                    {'carteira_keys': list(carteira_dict.keys()), 'total': carteira_dict.get('total', 0)},
                    duration_ms
                )
                
                # Tool: analisar_adequacao
                start_time = time.time()
                adequacao = analisar_adequacao(carteira_dict, "conservador")
                duration_ms = (time.time() - start_time) * 1000
                adeq_dict = adequacao.model_dump() if hasattr(adequacao, 'model_dump') else (adequacao.dict() if hasattr(adequacao, 'dict') else adequacao)
                self.traceability.add_tool_call(
                    trace_id, 'analisar_adequacao',
                    {'carteira': 'loaded', 'perfil': 'conservador'},
                    {'score': adeq_dict.get('score', 0), 'problemas_count': len(adeq_dict.get('problemas', []))},
                    duration_ms
                )
                
                # Tool: analisar_alinhamento_objetivos
                start_time = time.time()
                alinhamento = analisar_alinhamento_objetivos(carteira_dict, PERFIL_JOAO)
                duration_ms = (time.time() - start_time) * 1000
                alinh_dict = alinhamento.model_dump() if hasattr(alinhamento, 'model_dump') else (alinhamento.dict() if hasattr(alinhamento, 'dict') else alinhamento)
                self.traceability.add_tool_call(
                    trace_id, 'analisar_alinhamento_objetivos',
                    {'carteira': 'loaded', 'perfil': 'loaded'},
                    {'score_geral': alinh_dict.get('score_geral', 0)},
                    duration_ms
                )
                
                # Tool: analisar_diversificacao
                start_time = time.time()
                diversificacao = analisar_diversificacao(carteira_dict)
                duration_ms = (time.time() - start_time) * 1000
                div_dict = diversificacao.model_dump() if hasattr(diversificacao, 'model_dump') else (diversificacao.dict() if hasattr(diversificacao, 'dict') else diversificacao)
                self.traceability.add_tool_call(
                    trace_id, 'analisar_diversificacao',
                    {'carteira': 'loaded'},
                    {'score_diversificacao': div_dict.get('score_diversificacao', 0)},
                    duration_ms
                )
                
                # Tool: recomendar_rebalanceamento
                start_time = time.time()
                rebalanceamento = recomendar_rebalanceamento(carteira_dict, "conservador")
                duration_ms = (time.time() - start_time) * 1000
                reb_dict = rebalanceamento.model_dump() if hasattr(rebalanceamento, 'model_dump') else (rebalanceamento.dict() if hasattr(rebalanceamento, 'dict') else rebalanceamento)
                self.traceability.add_tool_call(
                    trace_id, 'recomendar_rebalanceamento',
                    {'carteira': 'loaded', 'perfil': 'conservador'},
                    {'necessario': reb_dict.get('necessario', False)},
                    duration_ms
                )
                
                # Formatar resposta completa
                resposta = self._formatar_analise_completa(carteira_dict, adequacao, alinhamento, diversificacao, rebalanceamento)
                tools_used = ["obter_carteira", "analisar_adequacao", "analisar_alinhamento_objetivos", "analisar_diversificacao", "recomendar_rebalanceamento"]
                
            elif intent == "analisar_adequacao" or intent == "recomendar_rebalanceamento":
                print(f"[AgentService] Intenção detectada: {intent}, executando análise de adequação completa")
                self.traceability.add_event(trace_id, 'route_decision', {'route': 'bypass', 'reason': 'adequation_analysis'})
                self.traceability.set_route(trace_id, 'bypass')
                
                from app.services.agent_tools import obter_carteira, analisar_adequacao, analisar_diversificacao, recomendar_rebalanceamento
                import time
                
                start_time = time.time()
                carteira_data = obter_carteira()
                duration_ms = (time.time() - start_time) * 1000
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                self.traceability.add_tool_call(trace_id, 'obter_carteira', {}, {'carteira_keys': list(carteira_dict.keys())}, duration_ms)
                
                start_time = time.time()
                adequacao = analisar_adequacao(carteira_dict, "conservador")
                duration_ms = (time.time() - start_time) * 1000
                adeq_dict = adequacao.model_dump() if hasattr(adequacao, 'model_dump') else (adequacao.dict() if hasattr(adequacao, 'dict') else adequacao)
                self.traceability.add_tool_call(trace_id, 'analisar_adequacao', {'perfil': 'conservador'}, {'score': adeq_dict.get('score', 0)}, duration_ms)
                
                start_time = time.time()
                diversificacao = analisar_diversificacao(carteira_dict)
                duration_ms = (time.time() - start_time) * 1000
                div_dict = diversificacao.model_dump() if hasattr(diversificacao, 'model_dump') else (diversificacao.dict() if hasattr(diversificacao, 'dict') else diversificacao)
                self.traceability.add_tool_call(trace_id, 'analisar_diversificacao', {}, {'score_diversificacao': div_dict.get('score_diversificacao', 0)}, duration_ms)
                
                start_time = time.time()
                rebalanceamento = recomendar_rebalanceamento(carteira_dict, "conservador")
                duration_ms = (time.time() - start_time) * 1000
                reb_dict = rebalanceamento.model_dump() if hasattr(rebalanceamento, 'model_dump') else (rebalanceamento.dict() if hasattr(rebalanceamento, 'dict') else rebalanceamento)
                self.traceability.add_tool_call(trace_id, 'recomendar_rebalanceamento', {'perfil': 'conservador'}, {'necessario': reb_dict.get('necessario', False)}, duration_ms)
                
                resposta = self._formatar_analise_adequacao(carteira_dict, adequacao, diversificacao, rebalanceamento)
                tools_used = ["obter_carteira", "analisar_adequacao", "analisar_diversificacao", "recomendar_rebalanceamento"]
                
            elif intent == "analisar_diversificacao":
                print("[AgentService] Intenção detectada: analisar_diversificacao, executando análise")
                self.traceability.add_event(trace_id, 'route_decision', {'route': 'bypass', 'reason': 'diversification_analysis'})
                self.traceability.set_route(trace_id, 'bypass')
                
                from app.services.agent_tools import obter_carteira, analisar_diversificacao
                import time
                
                start_time = time.time()
                carteira_data = obter_carteira()
                duration_ms = (time.time() - start_time) * 1000
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                self.traceability.add_tool_call(trace_id, 'obter_carteira', {}, {'carteira_keys': list(carteira_dict.keys())}, duration_ms)
                
                start_time = time.time()
                diversificacao = analisar_diversificacao(carteira_dict)
                duration_ms = (time.time() - start_time) * 1000
                div_dict = diversificacao.model_dump() if hasattr(diversificacao, 'model_dump') else (diversificacao.dict() if hasattr(diversificacao, 'dict') else diversificacao)
                self.traceability.add_tool_call(trace_id, 'analisar_diversificacao', {}, {'score_diversificacao': div_dict.get('score_diversificacao', 0)}, duration_ms)
                
                resposta = self._formatar_analise_diversificacao(carteira_dict, diversificacao)
                tools_used = ["obter_carteira", "analisar_diversificacao"]
                
            elif intent == "obter_carteira":
                # Chamar tool diretamente e formatar resposta com LLM
                print("[AgentService] Intenção detectada: obter_carteira, usando LLM para formatar")
                self.traceability.add_event(trace_id, 'route_decision', {'route': 'llm', 'reason': 'carteira_query'})
                self.traceability.set_route(trace_id, 'llm')
                
                from app.services.agent_tools import obter_carteira
                import time
                
                start_time = time.time()
                carteira_data = obter_carteira()
                duration_ms = (time.time() - start_time) * 1000
                
                # Converter para dict
                if hasattr(carteira_data, 'model_dump'):
                    carteira_dict = carteira_data.model_dump()
                elif hasattr(carteira_data, 'dict'):
                    carteira_dict = carteira_data.dict()
                else:
                    carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
                
                self.traceability.add_tool_call(
                    trace_id, 'obter_carteira',
                    {},
                    {'total': carteira_dict.get('total', 0), 'investimentos_count': len(carteira_dict.get('investimentos', []))},
                    duration_ms
                )
                
                # Formatar resposta usando LLM (não mais manual)
                if not self.llm:
                    resposta = "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
                else:
                    resposta = self._formatar_com_llm(message, carteira_dict, None, context, trace_id)
                tools_used = ["obter_carteira"]
                
            elif intent and self.agent_executor:
                # Para outras intenções, enriquecer mensagem com contexto
                self.traceability.add_event(trace_id, 'route_decision', {'route': 'react', 'reason': f'intent_{intent}'})
                self.traceability.set_route(trace_id, 'react')
                
                enhanced_message = f"{message_with_context}\n\n[IMPORTANTE: Você TEM acesso aos dados do cliente João. Use a ferramenta {intent} para obter as informações necessárias e responder a pergunta do cliente.]"
                print(f"[AgentService] Intenção detectada: {intent}, usando agente reativo")
                
                # Registrar prompt antes de invocar
                self.traceability.add_raw_prompt(trace_id, enhanced_message)
                
                import time
                start_time = time.time()
                result = self.agent_executor.invoke({"input": enhanced_message})
                duration_ms = (time.time() - start_time) * 1000
                
                resposta = result.get("output", "")
                tools_used = []
                
                # Capturar intermediate_steps do AgentExecutor (padrão oficial LangChain)
                intermediate_steps = result.get("intermediate_steps", [])
                if intermediate_steps:
                    for step in intermediate_steps:
                        if len(step) >= 2:
                            tool_action = step[0]
                            tool_result = step[1]
                            
                            # Extrair nome da tool
                            tool_name = None
                            if hasattr(tool_action, 'tool'):
                                tool_name = tool_action.tool
                            elif hasattr(tool_action, 'name'):
                                tool_name = tool_action.name
                            elif isinstance(tool_action, dict):
                                tool_name = tool_action.get('tool', tool_action.get('name'))
                            
                            if tool_name and tool_name not in tools_used:
                                tools_used.append(tool_name)
                                # Registrar tool call no traceability
                                tool_input = {}
                                if hasattr(tool_action, 'tool_input'):
                                    tool_input_raw = tool_action.tool_input
                                    if isinstance(tool_input_raw, dict):
                                        tool_input = tool_input_raw
                                    else:
                                        tool_input = {"input": str(tool_input_raw)[:200]}
                                elif isinstance(tool_action, dict):
                                    tool_input = tool_action.get('tool_input', {})
                                
                                tool_output = {"output": str(tool_result)[:500]} if tool_result else {}
                                
                                self.traceability.add_tool_call(
                                    trace_id,
                                    tool_name,
                                    tool_input,
                                    tool_output,
                                    None
                                )
                
                # Fallback: se não encontrou tools nos intermediate_steps, verificar no resultado
                if not tools_used and intent in str(result):
                    tools_used.append(intent)
                
                # Registrar resposta raw
                self.traceability.add_raw_response(trace_id, resposta)
                
                # Registrar evento de execução do agente
                self.traceability.add_event(
                    trace_id,
                    'agent_executor_invoke',
                    {
                        'intent': intent,
                        'duration_ms': duration_ms,
                        'tools_used': tools_used,
                        'output_length': len(resposta)
                    }
                )
            else:
                # Sem intenção detectada ou agente não disponível
                if not self.agent_executor:
                    print("[AgentService] Agente reativo não disponível, usando fallback")
                    self.traceability.add_event(trace_id, 'route_decision', {'route': 'fallback', 'reason': 'no_agent_executor'})
                    self.traceability.set_route(trace_id, 'fallback')
                    return self._fallback_response(message, trace_id)
                
                # Usar agente reativo normalmente (com contexto)
                self.traceability.add_event(trace_id, 'route_decision', {'route': 'react', 'reason': 'no_intent_detected'})
                self.traceability.set_route(trace_id, 'react')
                
                print(f"[AgentService] Processando mensagem com agente reativo: {message[:50]}...")
                
                # Registrar prompt
                self.traceability.add_raw_prompt(trace_id, message_with_context)
                
                import time
                start_time = time.time()
                result = self.agent_executor.invoke({"input": message_with_context})
                duration_ms = (time.time() - start_time) * 1000
                
                resposta = result.get("output", "")
                tools_used = []
                
                # Capturar intermediate_steps do AgentExecutor (padrão oficial LangChain)
                intermediate_steps = result.get("intermediate_steps", [])
                if intermediate_steps:
                    for step in intermediate_steps:
                        if len(step) >= 2:
                            tool_action = step[0]
                            tool_result = step[1]
                            
                            # Extrair nome da tool
                            tool_name = None
                            if hasattr(tool_action, 'tool'):
                                tool_name = tool_action.tool
                            elif hasattr(tool_action, 'name'):
                                tool_name = tool_action.name
                            elif isinstance(tool_action, dict):
                                tool_name = tool_action.get('tool', tool_action.get('name'))
                            
                            if tool_name and tool_name not in tools_used:
                                tools_used.append(tool_name)
                                # Registrar tool call no traceability
                                tool_input = {}
                                if hasattr(tool_action, 'tool_input'):
                                    tool_input_raw = tool_action.tool_input
                                    if isinstance(tool_input_raw, dict):
                                        tool_input = tool_input_raw
                                    else:
                                        tool_input = {"input": str(tool_input_raw)[:200]}
                                elif isinstance(tool_action, dict):
                                    tool_input = tool_action.get('tool_input', {})
                                
                                tool_output = {"output": str(tool_result)[:500]} if tool_result else {}
                                
                                self.traceability.add_tool_call(
                                    trace_id,
                                    tool_name,
                                    tool_input,
                                    tool_output,
                                    None
                                )
                
                # Registrar resposta raw
                self.traceability.add_raw_response(trace_id, resposta)
                
                # Registrar evento de execução
                self.traceability.add_event(
                    trace_id,
                    'agent_executor_invoke',
                    {
                        'duration_ms': duration_ms,
                        'output_length': len(resposta)
                    }
                )
            
            # tools_used já foi definido acima baseado na intenção
            
            self.traceability.add_reasoning_step(
                trace_id, "process_message",
                {"user_input": message},
                {"resposta": resposta, "tools_used": tools_used},
                tools_used,
                f"Resposta gerada usando {len(tools_used)} tool(s)" if tools_used else "Resposta gerada sem tools"
            )
            
            # Gerar explicação se necessário
            explicacao = None
            if tools_used:
                explicacao = {
                    "rationale": f"Resposta baseada em análise usando {', '.join(tools_used)}",
                    "tools_used": tools_used
                }
            
            # Finalizar trace
            self.traceability.finalize_trace(
                trace_id,
                {"resposta": resposta},
                explicacao
            )
            
            return {
                "response": resposta,
                "trace_id": trace_id,
                "explicacao": explicacao
            }
            
        except Exception as e:
            print(f"[AgentService] Erro ao processar mensagem: {e}")
            import traceback
            tb_str = traceback.format_exc()
            traceback.print_exc()
            
            # Registrar erro no trace
            if trace_id:
                self.traceability.add_error(
                    trace_id,
                    'AgentServiceException',
                    str(e),
                    {'method': 'process_message'},
                    tb_str
                )
            
            # Sempre retornar fallback que fornece resposta útil
            return self._fallback_response(message, trace_id)
    
    def _formatar_carteira_manual(self, carteira_dict: Dict, pergunta: str) -> str:
        """Formata resposta da carteira manualmente quando LLM não está disponível"""
        total = carteira_dict.get('total', 0)
        dinheiro_parado = carteira_dict.get('dinheiroParado', 0)
        distribuicao = carteira_dict.get('distribuicaoPercentual', {})
        investimentos = carteira_dict.get('investimentos', [])
        alertas = carteira_dict.get('adequacaoPerfil', {}).get('alertas', [])

        resposta = "Olá João! Aqui está um resumo completo da sua carteira:\n\n"
        resposta += f"Patrimônio Investido: R$ {total:,.2f}\n"
        resposta += f"Dinheiro Parado: R$ {dinheiro_parado:,.2f}\n"
        resposta += f"Total Disponível: R$ {total + dinheiro_parado:,.2f}\n\n"

        resposta += "Distribuição do Patrimônio:\n"
        resposta += f"- Renda Fixa: {distribuicao.get('rendaFixa', 0):.1f}%\n"
        resposta += f"- Renda Variável: {distribuicao.get('rendaVariavel', 0):.1f}%\n"
        resposta += f"- Liquidez: {distribuicao.get('liquidez', 0):.1f}%\n\n"

        if investimentos:
            resposta += f"Investimentos ({len(investimentos)}):\n"
            for inv in investimentos:
                resposta += f"- {inv.get('nome', 'N/A')}: R$ {inv.get('valor', 0):,.2f} ({inv.get('tipo', 'N/A')})\n"
            resposta += "\n"

        if alertas:
            resposta += "Observações importantes:\n"
            for alerta in alertas:
                resposta += f"- {alerta.get('mensagem', '')}\n"
            resposta += "\n"

        resposta += "Se quiser, posso detalhar algum investimento específico ou sugerir ajustes."
        return resposta
    
    def _formatar_analise_completa(self, carteira_dict: Dict, adequacao, alinhamento, diversificacao, rebalanceamento) -> str:
        """Formata análise completa incluindo adequação, alinhamento, diversificação e rebalanceamento"""
        # Converter para dicts
        if hasattr(adequacao, 'model_dump'):
            adeq_dict = adequacao.model_dump()
        elif hasattr(adequacao, 'dict'):
            adeq_dict = adequacao.dict()
        else:
            adeq_dict = adequacao
        
        if hasattr(alinhamento, 'model_dump'):
            alinh_dict = alinhamento.model_dump()
        elif hasattr(alinhamento, 'dict'):
            alinh_dict = alinhamento.dict()
        else:
            alinh_dict = alinhamento
        
        if hasattr(diversificacao, 'model_dump'):
            div_dict = diversificacao.model_dump()
        elif hasattr(diversificacao, 'dict'):
            div_dict = diversificacao.dict()
        else:
            div_dict = diversificacao
        
        if hasattr(rebalanceamento, 'model_dump'):
            reb_dict = rebalanceamento.model_dump()
        elif hasattr(rebalanceamento, 'dict'):
            reb_dict = rebalanceamento.dict()
        else:
            reb_dict = rebalanceamento
        
        resposta = "### Análise Completa do Portfólio\n\n"
        
        # Adequação ao Perfil
        resposta += "### Adequação ao Perfil de Risco\n"
        resposta += f"Score: {adeq_dict.get('score', 0)}/100\n"
        if adeq_dict.get('problemas'):
            resposta += "Problemas identificados:\n"
            for problema in adeq_dict.get('problemas', []):
                resposta += f"• {problema}\n"
        resposta += "\n"
        
        # Alinhamento com Objetivos
        resposta += "### Alinhamento com Objetivos\n"
        resposta += f"Score Geral: {alinh_dict.get('score_geral', 0)}/100\n\n"
        
        resposta += "Curto Prazo (até 3 anos):\n"
        resposta += f"• Status: {'✓ Alinhado' if alinh_dict.get('alinhado_curto_prazo') else '✗ Não alinhado'}\n"
        if alinh_dict.get('problemas_curto'):
            for problema in alinh_dict.get('problemas_curto', []):
                resposta += f"• {problema}\n"
        if alinh_dict.get('recomendacoes_curto'):
            resposta += "Recomendações:\n"
            for rec in alinh_dict.get('recomendacoes_curto', []):
                resposta += f"• {rec}\n"
        resposta += "\n"
        
        resposta += "Médio Prazo (3 a 10 anos):\n"
        resposta += f"• Status: {'✓ Alinhado' if alinh_dict.get('alinhado_medio_prazo') else '✗ Não alinhado'}\n"
        if alinh_dict.get('problemas_medio'):
            for problema in alinh_dict.get('problemas_medio', []):
                resposta += f"• {problema}\n"
        if alinh_dict.get('recomendacoes_medio'):
            resposta += "Recomendações:\n"
            for rec in alinh_dict.get('recomendacoes_medio', []):
                resposta += f"• {rec}\n"
        resposta += "\n"
        
        resposta += "Longo Prazo (acima de 10 anos):\n"
        resposta += f"• Status: {'✓ Alinhado' if alinh_dict.get('alinhado_longo_prazo') else '✗ Não alinhado'}\n"
        if alinh_dict.get('problemas_longo'):
            for problema in alinh_dict.get('problemas_longo', []):
                resposta += f"• {problema}\n"
        if alinh_dict.get('recomendacoes_longo'):
            resposta += "Recomendações:\n"
            for rec in alinh_dict.get('recomendacoes_longo', []):
                resposta += f"• {rec}\n"
        resposta += "\n"
        
        # Diversificação
        resposta += "### Diversificação\n"
        resposta += f"Score: {div_dict.get('score_diversificacao', 0)}/100\n"
        if div_dict.get('problemas'):
            resposta += "Problemas identificados:\n"
            for problema in div_dict.get('problemas', []):
                resposta += f"• {problema}\n"
        if div_dict.get('recomendacoes'):
            resposta += "Recomendações:\n"
            for rec in div_dict.get('recomendacoes', []):
                resposta += f"• {rec}\n"
        resposta += "\n"
        
        # Rebalanceamento
        resposta += "### Recomendações de Rebalanceamento\n"
        resposta += f"Necessário: {'Sim' if reb_dict.get('necessario') else 'Não'}\n"
        resposta += f"Justificativa: {reb_dict.get('justificativa', '')}\n"
        if reb_dict.get('ajustes_sugeridos'):
            resposta += "Ajustes Sugeridos:\n"
            for ajuste in reb_dict.get('ajustes_sugeridos', []):
                resposta += f"• {ajuste.get('acao', '')}: R$ {ajuste.get('valor', 0):,.2f}\n"
                resposta += f"  De {ajuste.get('de', '')} para {ajuste.get('para', '')}\n"
                resposta += f"  {ajuste.get('justificativa', '')}\n"
        resposta += f"\nImpacto Esperado: {reb_dict.get('impacto_esperado', '')}\n\n"
        
        # Próximos Passos
        resposta += "### Próximos Passos\n"
        resposta += "• Revisar e implementar os ajustes sugeridos\n"
        resposta += "• Monitorar a carteira regularmente\n"
        resposta += "• Considerar oportunidades de investimento adequadas ao perfil\n"
        
        return resposta
    
    def _formatar_analise_adequacao(self, carteira_dict: Dict, adequacao, diversificacao, rebalanceamento) -> str:
        """Formata análise de adequação incluindo diversificação e rebalanceamento"""
        if hasattr(adequacao, 'model_dump'):
            adeq_dict = adequacao.model_dump()
        elif hasattr(adequacao, 'dict'):
            adeq_dict = adequacao.dict()
        else:
            adeq_dict = adequacao
        
        if hasattr(diversificacao, 'model_dump'):
            div_dict = diversificacao.model_dump()
        elif hasattr(diversificacao, 'dict'):
            div_dict = diversificacao.dict()
        else:
            div_dict = diversificacao
        
        if hasattr(rebalanceamento, 'model_dump'):
            reb_dict = rebalanceamento.model_dump()
        elif hasattr(rebalanceamento, 'dict'):
            reb_dict = rebalanceamento.dict()
        else:
            reb_dict = rebalanceamento
        
        resposta = "### Análise de Adequação do Portfólio\n\n"
        resposta += f"Score de Adequação: {adeq_dict.get('score', 0)}/100\n"
        resposta += f"Status: {'✓ Adequado' if adeq_dict.get('adequado') else '✗ Requer ajustes'}\n\n"
        
        if adeq_dict.get('problemas'):
            resposta += "Problemas Identificados:\n"
            for problema in adeq_dict.get('problemas', []):
                resposta += f"• {problema}\n"
            resposta += "\n"
        
        if adeq_dict.get('recomendacoes'):
            resposta += "Recomendações:\n"
            for rec in adeq_dict.get('recomendacoes', []):
                resposta += f"• {rec}\n"
            resposta += "\n"
        
        resposta += "### Diversificação\n"
        resposta += f"Score: {div_dict.get('score_diversificacao', 0)}/100\n"
        if div_dict.get('problemas'):
            for problema in div_dict.get('problemas', []):
                resposta += f"• {problema}\n"
        resposta += "\n"
        
        resposta += "### Rebalanceamento\n"
        if reb_dict.get('necessario'):
            resposta += "Rebalanceamento necessário. Ajustes sugeridos:\n"
            for ajuste in reb_dict.get('ajustes_sugeridos', []):
                resposta += f"• {ajuste.get('acao', '')}: R$ {ajuste.get('valor', 0):,.2f}\n"
        else:
            resposta += "Carteira já está adequadamente balanceada.\n"
        
        resposta += "\n### Próximos Passos\n"
        resposta += "• Implementar os ajustes sugeridos\n"
        resposta += "• Monitorar a carteira regularmente\n"
        
        return resposta
    
    def _formatar_analise_diversificacao(self, carteira_dict: Dict, diversificacao) -> str:
        """Formata análise de diversificação"""
        if hasattr(diversificacao, 'model_dump'):
            div_dict = diversificacao.model_dump()
        elif hasattr(diversificacao, 'dict'):
            div_dict = diversificacao.dict()
        else:
            div_dict = diversificacao
        
        resposta = "### Análise de Diversificação\n\n"
        resposta += f"Score de Diversificação: {div_dict.get('score_diversificacao', 0)}/100\n"
        resposta += f"Status: {'✓ Bem diversificado' if div_dict.get('adequado') else '✗ Requer melhorias'}\n\n"
        
        if div_dict.get('problemas'):
            resposta += "Problemas Identificados:\n"
            for problema in div_dict.get('problemas', []):
                resposta += f"• {problema}\n"
            resposta += "\n"
        
        resposta += "Concentração por Classe:\n"
        for classe, pct in div_dict.get('concentracao_por_classe', {}).items():
            resposta += f"• {classe}: {pct:.1f}%\n"
        resposta += "\n"
        
        if div_dict.get('recomendacoes'):
            resposta += "Recomendações:\n"
            for rec in div_dict.get('recomendacoes', []):
                resposta += f"• {rec}\n"
        
        return resposta

    def _fallback_response(self, message: str, trace_id: str) -> Dict:
        """Retorna erro quando agente não está disponível (não mais resposta determinística)"""
        resposta = "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
        
        self.traceability.add_error(
            trace_id,
            'AgentUnavailableError',
            'Agent service not available',
            {'message': message[:200]}
        )
        self.traceability.finalize_trace(
            trace_id,
            {"resposta": resposta},
            {"source": "error", "error": "agent_unavailable"}
        )
        
        return {
            "response": resposta,
            "trace_id": trace_id,
            "explicacao": None
        }
    
    def _formatar_com_llm(self, message: str, carteira: Optional[Dict], recomendacoes: Optional[str], context: Optional[List], trace_id: str) -> str:
        """Formata resposta usando LLM com dados da carteira"""
        if not self.llm:
            return "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
        
        try:
            system_prompt = (
                "⚠️ PRIORIDADE ABSOLUTA: Responda DIRETAMENTE à pergunta do usuário. "
                "O contexto fornecido (dados da carteira, análises) é apenas informação adicional que você PODE usar se for relevante para responder a pergunta específica. "
                "Se a pergunta for simples, responda de forma simples e direta, IGNORANDO o contexto se não for necessário. "
                "A pergunta do usuário é sempre a prioridade - o contexto é opcional e só deve ser usado quando realmente ajudar a responder a pergunta.\n\n"
                "Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter. "
                "Responda de forma consultiva e no estilo CFP, usando os dados da carteira fornecidos quando disponíveis. "
                "IMPORTANTE: O cliente tem perfil de investidor CONSERVADOR. Sempre considere este perfil ao fazer recomendações e análises. "
                "NÃO pergunte sobre o perfil de investidor do cliente - assuma que é conservador e use isso como contexto em todas as respostas. "
                "\n\n📌 REGRA IMPORTANTE: Se o cliente perguntar APENAS 'qual é o meu perfil de investidor' ou 'qual meu perfil' ou variações similares, "
                "responda de forma DIRETA e CONCISA: 'Seu perfil de investidor é CONSERVADOR.' "
                "NÃO faça análises completas da carteira para essa pergunta simples. "
                "Apenas se o cliente perguntar sobre adequação, alinhamento ou problemas da carteira, aí sim faça análises detalhadas. "
                "\n\n⚠️ REGRA CRÍTICA: Você DEVE fazer análises proativas. NÃO peça ao cliente para fazer verificações. "
                "Você TEM os dados da carteira e DEVE analisar:\n"
                "- Adequação do perfil de risco (renda variável deve ser 10-15%, liquidez 15-20% para conservador)\n"
                "- Alinhamento com objetivos de curto/médio/longo prazo (avaliar alocação por horizonte temporal)\n"
                "- Diversificação (verificar concentração por classe e por ativo)\n"
                "- Necessidade de rebalanceamento (propor ajustes específicos quando necessário)\n"
                "\nSempre tente responder a pergunta do cliente, mesmo que não tenha todos os dados. "
                "Se faltarem dados específicos, forneça orientações gerais baseadas em boas práticas e pergunte quais informações adicionais seriam úteis. "
                "A resposta precisa ter QUEBRAS DE LINHA claras e leitura fácil. "
                "Use títulos curtos e listas com um item por linha. "
                "Use o contexto da conversa anterior quando relevante para entender referências do cliente. "
                "Sempre termine com próximos passos práticos ou perguntas para obter mais informações quando necessário."
            )
            
            user_content = f"Pergunta do cliente: {message}\n\n"
            
            if carteira:
                total = float(carteira.get('total', 0) or 0)
                dinheiro_parado = float(carteira.get('dinheiroParado', 0) or 0)
                total_carteira = total + dinheiro_parado
                distribuicao = carteira.get('distribuicaoPercentual', {})
                investimentos = carteira.get('investimentos', [])
                
                user_content += f"Dados da carteira (João):\n"
                user_content += f"- Total da carteira (investido + parado): R$ {total_carteira:,.2f}\n"
                user_content += f"- Patrimônio investido: R$ {total:,.2f}\n"
                user_content += f"- Dinheiro parado: R$ {dinheiro_parado:,.2f}\n"
                user_content += f"- Distribuição:\n"
                user_content += f"  • Renda Fixa: {distribuicao.get('rendaFixa', 0):.1f}%\n"
                user_content += f"  • Renda Variável: {distribuicao.get('rendaVariavel', 0):.1f}%\n"
                user_content += f"  • Liquidez: {distribuicao.get('liquidez', 0):.1f}%\n"
                
                if investimentos:
                    user_content += f"\nInvestimentos:\n"
                    for inv in investimentos:
                        user_content += f"- {inv.get('nome', 'N/A')}: R$ {inv.get('valor', 0):,.2f} ({inv.get('tipo', 'N/A')})\n"
                
                alertas = carteira.get('adequacaoPerfil', {}).get('alertas', [])
                if alertas:
                    user_content += f"\nAlertas:\n"
                    for alerta in alertas:
                        user_content += f"- {alerta.get('mensagem', '')}\n"
            
            if recomendacoes:
                user_content += f"\nOportunidades adequadas:\n{recomendacoes}\n"
            
            # Preparar mensagens
            messages = []
            if context:
                for msg in context[-4:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        messages.append({"role": "user", "content": content})
                    elif role == 'assistant':
                        messages.append({"role": "assistant", "content": content})
            
            messages.append({"role": "user", "content": user_content})
            
            # Chamar LLM
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            langchain_messages = [SystemMessage(content=system_prompt)]
            for msg in messages:
                if msg['role'] == 'user':
                    langchain_messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    langchain_messages.append(AIMessage(content=msg['content']))
            
            response = self.llm.invoke(langchain_messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            if trace_id:
                self.traceability.add_raw_prompt(trace_id, user_content, system_prompt)
                self.traceability.add_raw_response(trace_id, response_text)
            
            return response_text.strip() if response_text else "Desculpe, não consegui gerar uma resposta. Por favor, tente novamente."
            
        except Exception as e:
            print(f"[AgentService] Erro ao formatar com LLM: {e}")
            import traceback
            traceback.print_exc()
            if trace_id:
                self.traceability.add_error(trace_id, 'LLMFormatError', str(e), {})
            return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."
    
    def _handle_carteira_directly(self, message: str, trace_id: str) -> Dict:
        """Handle carteira diretamente quando agente não está disponível"""
        try:
            from app.services.agent_tools import obter_carteira
            
            print("[AgentService] Chamando obter_carteira diretamente (fallback)")
            carteira_data = obter_carteira()
            
            # Converter para dict
            if hasattr(carteira_data, 'model_dump'):
                carteira_dict = carteira_data.model_dump()
            elif hasattr(carteira_data, 'dict'):
                carteira_dict = carteira_data.dict()
            else:
                carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
            
            # Formatar resposta simples
            total = carteira_dict.get('total', 0)
            dinheiro_parado = carteira_dict.get('dinheiroParado', 0)
            distribuicao = carteira_dict.get('distribuicaoPercentual', {})
            investimentos = carteira_dict.get('investimentos', [])
            
            resposta = f"Olá João! Aqui está um resumo da sua carteira:\n\n"
            resposta += f"💰 Patrimônio Investido: R$ {total:,.2f}\n"
            resposta += f"💵 Dinheiro Parado: R$ {dinheiro_parado:,.2f}\n"
            resposta += f"📊 Total Disponível: R$ {total + dinheiro_parado:,.2f}\n\n"
            resposta += f"Distribuição:\n"
            resposta += f"• Renda Fixa: {distribuicao.get('rendaFixa', 0):.1f}%\n"
            resposta += f"• Renda Variável: {distribuicao.get('rendaVariavel', 0):.1f}%\n"
            resposta += f"• Liquidez: {distribuicao.get('liquidez', 0):.1f}%\n\n"
            
            if investimentos:
                resposta += f"Seus principais investimentos:\n"
                for inv in investimentos[:5]:
                    resposta += f"• {inv.get('nome', 'N/A')}: R$ {inv.get('valor', 0):,.2f}\n"
            
            self.traceability.finalize_trace(
                trace_id,
                {"resposta": resposta},
                {"tools_used": ["obter_carteira"]}
            )
            
            return {
                "response": resposta,
                "trace_id": trace_id,
                "explicacao": {"tools_used": ["obter_carteira"]}
            }
        except Exception as e:
            print(f"[AgentService] Erro ao obter carteira diretamente: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_response(message, trace_id)

