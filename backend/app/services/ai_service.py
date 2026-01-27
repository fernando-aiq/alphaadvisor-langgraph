import os
from typing import Optional, Dict

# Importar AgentService (nova implementação)
AGENT_IMPORT_ERROR = None
try:
    from app.services.agent_service import AgentService
    AGENT_AVAILABLE = True
except Exception as e:
    AGENT_AVAILABLE = False
    AGENT_IMPORT_ERROR = str(e)
    print(f"[AIService] AgentService não disponível, usando implementação legacy: {e}")

# Importar TraceabilityService para criar traces mesmo no fallback
try:
    from app.services.traceability_service import TraceabilityService
    TRACEABILITY_AVAILABLE = True
except Exception as e:
    TRACEABILITY_AVAILABLE = False
    print(f"[AIService] TraceabilityService não disponível: {e}")

class AIService:
    def __init__(self):
        self.agent_error = None
        self.last_client_error = None
        self.last_openai_error = None
        # Tentar usar AgentService se disponível
        if AGENT_AVAILABLE:
            try:
                self.agent_service = AgentService()
                self.use_agent = True
                print("[AIService] Usando AgentService com LangGraph")
            except Exception as e:
                print(f"[AIService] Erro ao inicializar AgentService: {e}")
                self.agent_error = str(e)
                self.agent_service = None
                self.use_agent = False
        else:
            self.agent_service = None
            self.use_agent = False
            if AGENT_IMPORT_ERROR:
                self.agent_error = AGENT_IMPORT_ERROR
        
        # Inicializar TraceabilityService para criar traces mesmo no fallback
        if TRACEABILITY_AVAILABLE:
            try:
                print("[AIService] Tentando inicializar TraceabilityService...")
                self.traceability = TraceabilityService()
                print(f"[AIService] TraceabilityService inicializado com sucesso: {self.traceability}")
            except Exception as e:
                print(f"[AIService] Erro ao inicializar TraceabilityService: {e}")
                import traceback
                traceback.print_exc()
                self.traceability = None
        else:
            print("[AIService] TRACEABILITY_AVAILABLE = False, TraceabilityService não será inicializado")
            self.traceability = None
        
        # Cliente será inicializado lazy (quando necessário) - fallback
        self._client = None
        self._last_api_key = None
        
    def _get_client(self):
        """Obtém o cliente OpenAI, recarregando a chave se necessário"""
        # Ler variáveis de ambiente a cada vez (podem ter mudado)
        api_key = os.getenv('OPENAI_API_KEY', '')
        model = os.getenv('AI_MODEL', 'gpt-4o')
        
        # Se a chave mudou ou o cliente não existe, recriar
        if api_key != self._last_api_key or self._client is None:
            self._last_api_key = api_key
            
            # Log para debug
            print(f"[AIService] Verificando API_KEY... presente: {bool(api_key)}")
            print(f"[AIService] Model: {model}")
            
            if api_key:
                try:
                    from openai import OpenAI
                    # Inicializar cliente OpenAI - versão 1.3.0 usa api_key diretamente
                    # Não passar proxies ou outros argumentos que podem causar problemas
                    self._client = OpenAI(api_key=api_key)
                    print("[AIService] Cliente OpenAI inicializado com sucesso")
                    self.last_client_error = None
                except ImportError:
                    print("[AIService] ERRO: Biblioteca openai não instalada")
                    self._client = None
                    self.last_client_error = "Biblioteca openai não instalada"
                except TypeError as e:
                    # Erro de argumentos inesperados - pode ser problema de versão
                    print(f"[AIService] ERRO de tipo ao inicializar OpenAI: {e}")
                    print("[AIService] Tentando método alternativo...")
                    try:
                        # Tentar sem passar api_key no construtor
                        import openai
                        # Para versões mais antigas, pode precisar setar globalmente
                        self._client = OpenAI()
                        # Tentar setar a chave de outra forma
                        if hasattr(self._client, 'api_key'):
                            self._client.api_key = api_key
                        print("[AIService] Cliente OpenAI inicializado com método alternativo")
                        self.last_client_error = None
                    except Exception as e2:
                        print(f"[AIService] ERRO ao inicializar OpenAI (método alternativo): {e2}")
                        import traceback
                        traceback.print_exc()
                        self._client = None
                        self.last_client_error = str(e2)
                except Exception as e:
                    print(f"[AIService] ERRO ao inicializar OpenAI: {e}")
                    import traceback
                    traceback.print_exc()
                    self._client = None
                    self.last_client_error = str(e)
            else:
                print("[AIService] OPENAI_API_KEY não configurada, usando respostas mockadas")
                self._client = None
                self.last_client_error = "OPENAI_API_KEY não configurada"
        
        return self._client
        
    def _normalize_message(self, message: str) -> str:
        message_lower = message.lower().strip()
        return (
            message_lower
            .replace("mminha", "minha")
            .replace("cartiera", "carteira")
            .replace("carteira", "carteira")
        )

    def _is_carteira_intent(self, message: str) -> bool:
        msg = self._normalize_message(message)
        keywords = ["carteira", "saldo", "investimento", "patrimônio", "meu patrimônio", "meu saldo"]
        return any(k in msg for k in keywords)

    def _is_recomendacao_intent(self, message: str) -> bool:
        msg = self._normalize_message(message)
        keywords = ["recomenda", "recomendação", "o que voce recomenda", "o que você recomenda", "ajuste", "ajustar"]
        return any(k in msg for k in keywords)

    def _get_carteira_data(self) -> Optional[Dict]:
        try:
            from app.services.agent_tools import obter_carteira
            carteira_data = obter_carteira()
            if hasattr(carteira_data, 'model_dump'):
                return carteira_data.model_dump()
            if hasattr(carteira_data, 'dict'):
                return carteira_data.dict()
            return carteira_data if isinstance(carteira_data, dict) else {}
        except Exception as e:
            print(f"[AIService] ERRO ao obter carteira via tool: {e}")
            return None

    def _get_recomendacoes(self, carteira: Dict) -> Optional[str]:
        try:
            from app.services.agent_tools import buscar_oportunidades
            perfil = "conservador"
            alertas = carteira.get("adequacaoPerfil", {}).get("alertas", [])
            problemas = [a.get("mensagem", "") for a in alertas if a.get("mensagem")]
            oportunidades = buscar_oportunidades(perfil, problemas)
            linhas = []
            for op in oportunidades:
                if hasattr(op, 'model_dump'):
                    op = op.model_dump()
                elif hasattr(op, 'dict'):
                    op = op.dict()
                linhas.append(f"- {op.get('nome', 'N/A')} ({op.get('tipo', 'N/A')}): {op.get('justificativa', '')}")
            return "\n".join(linhas) if linhas else None
        except Exception as e:
            print(f"[AIService] ERRO ao obter oportunidades via tool: {e}")
            return None

    def _format_carteira_manual(self, carteira: Dict) -> str:
        total = carteira.get('total', 0)
        dinheiro_parado = carteira.get('dinheiroParado', 0)
        distribuicao = carteira.get('distribuicaoPercentual', {})
        investimentos = carteira.get('investimentos', [])
        alertas = carteira.get('adequacaoPerfil', {}).get('alertas', [])
        total_carteira = float(total or 0) + float(dinheiro_parado or 0)

        resposta = "### Visão geral\n"
        resposta += f"• Total da carteira: R$ {total_carteira:,.2f}\n"
        resposta += f"• Patrimônio investido: R$ {total:,.2f}\n"
        resposta += f"• Dinheiro parado: R$ {dinheiro_parado:,.2f}\n\n"
        resposta += "### Distribuição\n"
        resposta += f"• Renda Fixa: {distribuicao.get('rendaFixa', 0):.1f}%\n"
        resposta += f"• Renda Variável: {distribuicao.get('rendaVariavel', 0):.1f}%\n"
        resposta += f"• Liquidez: {distribuicao.get('liquidez', 0):.1f}%\n\n"
        if investimentos:
            resposta += "### Investimentos\n"
            for inv in investimentos[:6]:
                resposta += f"• {inv.get('nome', 'N/A')}: R$ {inv.get('valor', 0):,.2f} ({inv.get('tipo', 'N/A')})\n"
        if alertas:
            resposta += "\n### Alertas\n"
            for alerta in alertas:
                resposta += f"• {alerta.get('mensagem', '')}\n"
        return resposta

    def _extract_liquidez_valor(self, carteira: Dict) -> float:
        investimentos = carteira.get('investimentos', [])
        total = 0.0
        for inv in investimentos:
            classe = (inv.get('classe') or "").lower()
            tipo = (inv.get('tipo') or "").lower()
            nome = (inv.get('nome') or "").lower()
            if classe == "liquidez" or tipo == "liquidez" or "conta corrente" in nome:
                total += float(inv.get('valor', 0) or 0)
        return total

    def _format_investimentos_list(self, carteira: Dict) -> str:
        investimentos = carteira.get('investimentos', [])
        linhas = []
        for inv in investimentos:
            linhas.append(
                f"- {inv.get('nome', 'N/A')}: R$ {inv.get('valor', 0):,.2f} ({inv.get('tipo', 'N/A')})"
            )
        return "\n".join(linhas) if linhas else "- Sem investimentos cadastrados"

    def _format_alertas_list(self, carteira: Dict) -> str:
        alertas = carteira.get('adequacaoPerfil', {}).get('alertas', [])
        linhas = [f"- {a.get('mensagem', '')}" for a in alertas if a.get('mensagem')]
        return "\n".join(linhas) if linhas else "- Nenhum alerta"

    def _llm_with_carteira(self, client, message: str, carteira: Dict, recomendacoes: Optional[str] = None, mode: str = "carteira", context: Optional[list] = None) -> Optional[str]:
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
                "\n\n⚠️ REGRA CRÍTICA: Você DEVE fazer análises proativas. NÃO peça ao cliente para fazer verificações. "
                "Você TEM os dados da carteira e DEVE analisar:\n"
                "- Adequação do perfil de risco (renda variável deve ser 10-15%, liquidez 15-20% para conservador)\n"
                "- Alinhamento com objetivos de curto/médio/longo prazo (avaliar alocação por horizonte temporal)\n"
                "- Diversificação (verificar concentração por classe e por ativo)\n"
                "- Necessidade de rebalanceamento (propor ajustes específicos quando necessário)\n"
                "\nPara perguntas sobre adequação, alinhamento, diversificação ou ajustes, você DEVE:\n"
                "1. Analisar os dados fornecidos\n"
                "2. Identificar problemas específicos\n"
                "3. Propor ajustes concretos com valores\n"
                "4. Explicar o impacto esperado\n"
                "\nSempre tente responder a pergunta do cliente, mesmo que não tenha todos os dados. "
                "Se faltarem dados específicos, forneça orientações gerais baseadas em boas práticas e pergunte quais informações adicionais seriam úteis. "
                "A resposta precisa ter QUEBRAS DE LINHA claras e leitura fácil. "
                "Use títulos curtos e listas com um item por linha. "
                "Use o contexto da conversa anterior quando relevante para entender referências do cliente. "
                "Sempre termine com próximos passos práticos ou perguntas para obter mais informações quando necessário."
            )

            dinheiro_parado = float(carteira.get('dinheiroParado', 0) or 0)
            patrimonio_investido = float(carteira.get('total', 0) or 0)
            total_carteira = patrimonio_investido + dinheiro_parado
            liquidez_valor = self._extract_liquidez_valor(carteira)
            distribuicao = carteira.get('distribuicaoPercentual', {})
            investimentos_list = self._format_investimentos_list(carteira)
            alertas_list = self._format_alertas_list(carteira)
            # Obter objetivo do cliente
            objetivo = carteira.get('objetivo', {})
            objetivo_valor = objetivo.get('valor', 0) if isinstance(objetivo, dict) else 0
            objetivo_prazo = objetivo.get('prazo', 0) if isinstance(objetivo, dict) else 0
            objetivo_desc = objetivo.get('descricao', '') if isinstance(objetivo, dict) else ''
            
            # Análise proativa básica
            renda_variavel_pct = distribuicao.get('rendaVariavel', 0)
            liquidez_pct = distribuicao.get('liquidez', 0)
            renda_fixa_pct = distribuicao.get('rendaFixa', 0)
            
            analise_adequacao = []
            if renda_variavel_pct > 15:
                analise_adequacao.append(f"⚠️ Renda variável ({renda_variavel_pct:.1f}%) acima do recomendado para conservador (10-15%)")
            if liquidez_pct < 15:
                analise_adequacao.append(f"⚠️ Liquidez ({liquidez_pct:.1f}%) abaixo do ideal para conservador (15-20%)")
            if renda_fixa_pct < 70:
                analise_adequacao.append(f"⚠️ Renda fixa ({renda_fixa_pct:.1f}%) abaixo do ideal para conservador (70-85%)")
            
            user_content = (
                f"Pergunta do cliente: {message}\n\n"
                f"Dados da carteira (João):\n"
                f"- Total da carteira (investido + parado): R$ {total_carteira:,.2f}\n"
                f"- Patrimônio investido: R$ {patrimonio_investido:,.2f}\n"
                f"- Dinheiro parado: R$ {dinheiro_parado:,.2f}\n"
                f"- Liquidez (valor em conta): R$ {liquidez_valor:,.2f}\n"
                f"- Distribuição:\n"
                f"  • Renda Fixa: {distribuicao.get('rendaFixa', 0):.1f}%\n"
                f"  • Renda Variável: {distribuicao.get('rendaVariavel', 0):.1f}%\n"
                f"  • Liquidez: {distribuicao.get('liquidez', 0):.1f}%\n"
            )
            
            if objetivo_valor > 0:
                user_content += f"\nObjetivo do cliente:\n"
                user_content += f"- {objetivo_desc if objetivo_desc else f'R$ {objetivo_valor:,.2f} em {objetivo_prazo} anos'}\n"
            
            user_content += f"\nInvestimentos:\n{investimentos_list}\n\n"
            user_content += f"Alertas:\n{alertas_list}\n"
            
            if analise_adequacao:
                user_content += f"\nAnálise Proativa de Adequação:\n"
                for item in analise_adequacao:
                    user_content += f"  {item}\n"
                user_content += "\n"
            if recomendacoes:
                user_content += f"\nOportunidades adequadas:\n{recomendacoes}\n"
            user_content += (
                f"\nModo de resposta: {mode}\n"
                "Regras de formatação:\n"
                "- Nunca repita TODA a carteira em respostas de recomendação/impacto.\n"
                "- Só liste investimentos se o usuário pedir detalhes da carteira.\n"
                "- Sempre use títulos com '###' e itens com '•'.\n"
                "- Use o contexto da conversa para entender referências como 'o investimento que falei acima', 'o CDB', etc.\n"
                "\n⚠️ IMPORTANTE: Se a pergunta for sobre adequação, alinhamento, diversificação ou ajustes:\n"
                "- Você DEVE fazer a análise proativa usando os dados fornecidos\n"
                "- Identifique problemas específicos com valores e percentuais\n"
                "- Proponha ajustes concretos (ex: 'realocar R$ X de renda variável para renda fixa')\n"
                "- Avalie alinhamento por horizonte temporal (curto/médio/longo prazo)\n"
                "- Analise diversificação e concentração\n"
                "- NÃO peça ao cliente para fazer verificações - você já tem os dados\n"
                "\nFormato esperado (obrigatório):\n"
                "### Resumo / Diagnóstico\n"
                "• ...\n\n"
                "### Adequação ao Perfil (se relevante)\n"
                "• ...\n\n"
                "### Alinhamento com Objetivos (se relevante)\n"
                "• Curto prazo: ...\n"
                "• Médio prazo: ...\n"
                "• Longo prazo: ...\n\n"
                "### Diversificação (se relevante)\n"
                "• ...\n\n"
                "### Ajustes e Rebalanceamento Sugeridos (se relevante)\n"
                "• ...\n\n"
                "### Próximos passos\n"
                "• ...\n"
            )
            
            # Preparar mensagens com contexto
            messages = [{"role": "system", "content": system_prompt}]
            
            # Adicionar contexto histórico se disponível
            if context:
                for msg in context[-4:]:  # Últimas 4 mensagens para não exceder tokens
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role in ['user', 'assistant']:
                        messages.append({"role": role, "content": content})
            
            # Adicionar mensagem atual
            messages.append({"role": "user", "content": user_content})
            
            response = client.chat.completions.create(
                model=os.getenv('AI_MODEL', 'gpt-4o'),
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            if response and response.choices:
                content = response.choices[0].message.content
                result = content.strip() if content else None
                if result:
                    # Criar trace para resposta com carteira
                    trace_id = ""
                    print(f"[AIService] Verificando traceability para _llm_with_carteira: {self.traceability is not None}")
                    if self.traceability:
                        try:
                            print(f"[AIService] Criando trace para mensagem sobre carteira: {message[:50]}...")
                            model = os.getenv('AI_MODEL', 'gpt-4o')
                            trace_id = self.traceability.create_trace(message, context=context, model=model)
                            print(f"[AIService] Trace criado: {trace_id}")
                            
                            # Adicionar intent e route
                            self.traceability.set_intent(trace_id, 'carteira_analysis')
                            self.traceability.set_route(trace_id, 'llm_direct')
                            
                            # Adicionar prompt raw
                            self.traceability.add_raw_prompt(trace_id, user_content, system_prompt)
                            
                            # Adicionar resposta raw
                            self.traceability.add_raw_response(trace_id, result)
                            
                            # Adicionar evento de LLM call
                            self.traceability.add_event(
                                trace_id,
                                'llm_call_with_carteira',
                                {
                                    'mode': mode,
                                    'carteira_total': total_carteira,
                                    'patrimonio_investido': patrimonio_investido,
                                    'dinheiro_parado': dinheiro_parado,
                                    'response_length': len(result)
                                }
                            )
                            
                            # Adicionar reasoning step
                            self.traceability.add_reasoning_step(
                                trace_id,
                                "Análise de Carteira via LLM",
                                {
                                    "mensagem": message[:200],
                                    "modo": mode,
                                    "carteira_total": total_carteira,
                                    "patrimonio_investido": patrimonio_investido,
                                    "dinheiro_parado": dinheiro_parado
                                },
                                {
                                    "resposta_gerada": result[:200] + "..." if len(result) > 200 else result
                                },
                                ["llm_with_carteira"],
                                f"Análise realizada usando LLM direto com dados da carteira (modo: {mode})"
                            )
                            
                            # Adicionar graph step simulando o fluxo
                            self.traceability.add_graph_step(
                                trace_id,
                                "llm_with_carteira",
                                {
                                    "message": message[:200],
                                    "mode": mode,
                                    "carteira_data": {
                                        "total": total_carteira,
                                        "investido": patrimonio_investido,
                                        "parado": dinheiro_parado,
                                        "distribuicao": distribuicao
                                    }
                                },
                                {"response_length": len(result)}
                            )
                            
                            self.traceability.finalize_trace(trace_id, {"resposta": result}, {
                                "source": "llm_with_carteira",
                                "mode": mode,
                                "intent": "carteira_analysis",
                                "route": "llm_direct",
                                "tools_used": ["llm_with_carteira"]
                            })
                            print(f"[AIService] Trace finalizado: {trace_id}")
                        except Exception as e:
                            print(f"[AIService] Erro ao criar trace: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print("[AIService] TraceabilityService não disponível, trace_id será vazio")
                    # Retornar dict com trace_id
                    return {"response": result, "trace_id": trace_id, "explicacao": None}
                return None
            return None
        except Exception as e:
            print(f"[AIService] ERRO ao formatar com LLM usando carteira: {e}")
            return None

    def process_message(self, message: str, context: Optional[list] = None, agent_builder_config: Optional[dict] = None) -> str:
        """
        Processa uma mensagem do usuário e retorna resposta da IA.
        Usa AgentService (com grafo LangGraph) se disponível, senão usa implementação legacy.
        Se agent_builder_config for fornecido, aplica fluxos customizados por intent.
        """
        print(f"[AIService] Processando mensagem: {message[:50]}...")
        
        # Se há configuração de agent_builder, tentar detectar intent e aplicar fluxo
        if agent_builder_config and agent_builder_config.get('intents'):
            try:
                from app.services.intent_service import IntentService
                intent_service = IntentService()
                
                # Detectar intent
                detected_intent = intent_service.detect_intent(message, agent_builder_config.get('intents', []))
                
                if detected_intent:
                    print(f"[AIService] Intent detectado: {detected_intent}")
                    flow = intent_service.get_intent_flow(detected_intent, agent_builder_config)
                    
                    if flow:
                        print(f"[AIService] Aplicando fluxo customizado para intent: {detected_intent}")
                        # Executar fluxo customizado
                        flow_results = intent_service.execute_flow(flow, {'message': message, 'context': context})
                        
                        # Se o fluxo tem resposta pré-definida, usar ela
                        for node_id, result in flow_results.items():
                            if result.get('type') == 'response' and result.get('content'):
                                return {"response": result['content'], "trace_id": "", "explicacao": None}
                        
                        # Se o fluxo tem tools, executá-las e continuar com processamento normal
                        # (isso será expandido conforme necessário)
            except Exception as e:
                print(f"[AIService] Erro ao aplicar fluxo customizado: {e}")
                import traceback
                traceback.print_exc()

        # Tentar usar AgentService primeiro (que usa o grafo LangGraph)
        # O grafo vai detectar a intenção automaticamente e decidir a rota
        # REMOVIDO: bypass que chamava _llm_with_carteira() diretamente
        # Agora todas as mensagens passam pelo grafo LangGraph
        if self.use_agent and self.agent_service:
            try:
                # Se o AgentService não tem executor, tentar usar mesmo assim ou cair no fallback
                agent_executor = getattr(self.agent_service, "agent_executor", None)
                if agent_executor is None:
                    # Tentar usar AgentService mesmo sem executor (pode ter fallback interno)
                    print("[AIService] AgentService sem executor, tentando usar mesmo assim")
                    try:
                        result = self.agent_service.process_message(message, context=context, agent_builder_config=agent_builder_config)
                        # Retornar dict completo com trace_id e explicacao para compatibilidade
                        if isinstance(result, dict):
                            return result  # Retornar dict completo
                        # Se não for dict, criar dict com resposta
                        return {"response": str(result), "trace_id": "", "explicacao": None}
                    except Exception as e:
                        print(f"[AIService] AgentService sem executor falhou, usando fallback legacy: {e}")
                        # Continuar para fallback legacy que sempre responde
                        pass
                else:
                    print("[AIService] Usando AgentService (LangGraph) com contexto")
                    result = self.agent_service.process_message(message, context=context, agent_builder_config=agent_builder_config)
                    # Retornar dict completo com trace_id e explicacao para compatibilidade
                    if isinstance(result, dict):
                        return result  # Retornar dict completo
                    # Se não for dict, criar dict com resposta
                    return {"response": str(result), "trace_id": "", "explicacao": None}
            except Exception as e:
                print(f"[AIService] Erro no AgentService, usando fallback: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback para implementação legacy
        print("[AIService] Usando implementação legacy")
        
        # Obter cliente (lazy initialization)
        client = self._get_client()
        api_key = os.getenv('OPENAI_API_KEY', '')
        model = os.getenv('AI_MODEL', 'gpt-4o')
        
        print(f"[AIService] API_KEY presente: {bool(api_key)}")
        print(f"[AIService] Cliente disponível: {client is not None}")
        
        try:
            # Se não houver API key, retornar resposta mockada
            if not api_key:
                print("[AIService] Usando resposta mockada (OPENAI_API_KEY não configurada)")
                result = self._mock_response(message)
                print(f"[AIService] Resposta mockada gerada: {result[:50] if result else 'VAZIA'}...")
                # Criar trace mesmo para resposta mockada
                trace_id = ""
                if self.traceability:
                    try:
                        model = os.getenv('AI_MODEL', 'gpt-4o')
                        trace_id = self.traceability.create_trace(message, context=context, model=model)
                        self.traceability.set_route(trace_id, 'mock_fallback')
                        self.traceability.add_event(
                            trace_id,
                            'mock_fallback',
                            {
                                'reason': 'no_api_key',
                                'response_length': len(result)
                            }
                        )
                        self.traceability.finalize_trace(trace_id, {"resposta": result}, {"source": "mock"})
                        print(f"[AIService] Trace criado com sucesso: {trace_id}")
                    except Exception as e:
                        print(f"[AIService] Erro ao criar trace: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("[AIService] TraceabilityService não disponível")
                return {"response": result, "trace_id": trace_id, "explicacao": None}
            
            # Preparar mensagens para o contexto
            messages = [
                {
                    "role": "system",
                    "content": "⚠️ PRIORIDADE ABSOLUTA: Responda DIRETAMENTE à pergunta do usuário. "
                              "O contexto fornecido (dados da carteira, análises) é apenas informação adicional que você PODE usar se for relevante para responder a pergunta específica. "
                              "Se a pergunta for simples, responda de forma simples e direta, IGNORANDO o contexto se não for necessário. "
                              "A pergunta do usuário é sempre a prioridade - o contexto é opcional e só deve ser usado quando realmente ajudar a responder a pergunta.\n\n"
                              "Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter. "
                              "Você ajuda clientes e assessores com questões sobre investimentos, "
                              "carteiras, oportunidades e análises financeiras. "
                              "IMPORTANTE: O cliente tem perfil de investidor CONSERVADOR. Sempre considere este perfil ao fazer recomendações e análises. "
                              "NÃO pergunte sobre o perfil de investidor do cliente - assuma que é conservador e use isso como contexto em todas as respostas. "
                              "\n\n📌 REGRA IMPORTANTE: Se o cliente perguntar APENAS 'qual é o meu perfil de investidor' ou 'qual meu perfil' ou variações similares, "
                              "responda de forma DIRETA e CONCISA: 'Seu perfil de investidor é CONSERVADOR.' "
                              "NÃO faça análises completas da carteira para essa pergunta simples. "
                              "Apenas se o cliente perguntar sobre adequação, alinhamento ou problemas da carteira, aí sim faça análises detalhadas. "
                              "\n\n⚠️ REGRA CRÍTICA: Você DEVE fazer análises proativas. NÃO peça ao cliente para fazer verificações. "
                              "Para perguntas sobre adequação, alinhamento com objetivos, diversificação ou ajustes:\n"
                              "- Analise os dados disponíveis proativamente\n"
                              "- Identifique problemas específicos (ex: 'renda variável 28.6% vs ideal 10-15%')\n"
                              "- Proponha ajustes concretos com valores (ex: 'realocar R$ X para renda fixa')\n"
                              "- Avalie alinhamento por horizonte temporal (curto/médio/longo prazo)\n"
                              "- Analise diversificação e concentração\n"
                              "- NÃO delegue análises ao cliente - você é o assessor e DEVE fazer as análises\n"
                              "\nSempre tente responder a pergunta do cliente, mesmo que não tenha todos os dados. "
                              "Se faltarem dados específicos, forneça orientações gerais baseadas em boas práticas e pergunte quais informações adicionais seriam úteis. "
                              "Seja profissional, claro e útil. Sempre termine com próximos passos práticos ou perguntas para obter mais informações quando necessário."
                }
            ]
            
            # Adicionar histórico se disponível
            if context:
                messages.extend(context)
            
            # Adicionar mensagem atual
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Chamar API da OpenAI
            if client:
                print("[AIService] Chamando API da OpenAI...")
                print(f"[AIService] Model: {model}")
                print(f"[AIService] Número de mensagens: {len(messages)}")
                
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                print(f"[AIService] Resposta recebida da OpenAI (tipo: {type(response)})")
                
                if response and response.choices and len(response.choices) > 0:
                    result = response.choices[0].message.content
                    if result:
                        result = result.strip()
                        print(f"[AIService] Resposta processada: {result[:50]}...")
                        print(f"[AIService] Tamanho da resposta: {len(result)} caracteres")
                        self.last_openai_error = None
                        # Criar trace para resposta da OpenAI
                        trace_id = ""
                        print(f"[AIService] Verificando traceability: {self.traceability is not None}")
                        if self.traceability:
                            try:
                                print(f"[AIService] Criando trace para mensagem: {message[:50]}...")
                                model = os.getenv('AI_MODEL', 'gpt-4o')
                                trace_id = self.traceability.create_trace(message, context=context, model=model)
                                print(f"[AIService] Trace criado: {trace_id}")
                                
                                # Adicionar prompt e resposta raw
                                system_msg = messages[0].get('content', '') if messages and messages[0].get('role') == 'system' else None
                                user_msg = message
                                self.traceability.add_raw_prompt(trace_id, user_msg, system_msg)
                                self.traceability.add_raw_response(trace_id, result)
                                
                                # Adicionar evento de LLM call
                                self.traceability.add_event(
                                    trace_id,
                                    'llm_call_openai',
                                    {
                                        'model': model,
                                        'messages_count': len(messages),
                                        'response_length': len(result)
                                    }
                                )
                                
                                self.traceability.finalize_trace(trace_id, {"resposta": result}, {"source": "openai"})
                                print(f"[AIService] Trace finalizado: {trace_id}")
                            except Exception as e:
                                print(f"[AIService] Erro ao criar trace: {e}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print("[AIService] TraceabilityService não disponível, trace_id será vazio")
                        print(f"[AIService] Retornando com trace_id: {trace_id}")
                        return {"response": result, "trace_id": trace_id, "explicacao": None}
                    else:
                        print("[AIService] AVISO: Resposta da OpenAI está vazia")
                        self.last_openai_error = "Resposta vazia da OpenAI"
                        result = self._mock_response(message)
                        trace_id = ""
                        if self.traceability:
                            try:
                                model = os.getenv('AI_MODEL', 'gpt-4o')
                                trace_id = self.traceability.create_trace(message, context=context, model=model)
                                self.traceability.add_error(trace_id, 'EmptyResponseError', 'OpenAI returned empty response', {})
                                self.traceability.set_route(trace_id, 'mock_fallback')
                                self.traceability.finalize_trace(trace_id, {"resposta": result}, {"source": "mock", "error": "empty_response"})
                            except Exception as e:
                                print(f"[AIService] Erro ao criar trace: {e}")
                        return {"response": result, "trace_id": trace_id, "explicacao": None}
                else:
                    print("[AIService] AVISO: Resposta da OpenAI não tem choices válidas")
                    self.last_openai_error = "Resposta da OpenAI sem choices válidas"
                    result = self._mock_response(message)
                    trace_id = ""
                    if self.traceability:
                        try:
                            model = os.getenv('AI_MODEL', 'gpt-4o')
                            trace_id = self.traceability.create_trace(message, context=context, model=model)
                            self.traceability.add_error(trace_id, 'InvalidResponseError', 'OpenAI response has no valid choices', {})
                            self.traceability.set_route(trace_id, 'mock_fallback')
                            self.traceability.finalize_trace(trace_id, {"resposta": result}, {"source": "mock", "error": "no_choices"})
                        except Exception as e:
                            print(f"[AIService] Erro ao criar trace: {e}")
                    return {"response": result, "trace_id": trace_id, "explicacao": None}
            else:
                print("[AIService] Cliente OpenAI não disponível, usando resposta mockada")
                self.last_openai_error = "Cliente OpenAI indisponível"
                result = self._mock_response(message)
                print(f"[AIService] Resposta mockada gerada: {result[:50] if result else 'VAZIA'}...")
                trace_id = ""
                if self.traceability:
                    try:
                        model = os.getenv('AI_MODEL', 'gpt-4o')
                        trace_id = self.traceability.create_trace(message, context=context, model=model)
                        self.traceability.add_error(trace_id, 'ClientUnavailableError', 'OpenAI client not available', {})
                        self.traceability.set_route(trace_id, 'mock_fallback')
                        self.traceability.finalize_trace(trace_id, {"resposta": result}, {"source": "mock", "error": "client_unavailable"})
                    except Exception as e:
                        print(f"[AIService] Erro ao criar trace: {e}")
                return {"response": result, "trace_id": trace_id, "explicacao": None}
            
        except Exception as e:
            print(f"[AIService] ERRO ao processar mensagem com IA: {e}")
            import traceback
            tb_str = traceback.format_exc()
            traceback.print_exc()
            self.last_openai_error = str(e)
            result = self._mock_response(message)
            print(f"[AIService] Resposta de fallback gerada: {result[:50] if result else 'VAZIA'}...")
            trace_id = ""
            if self.traceability:
                try:
                    model = os.getenv('AI_MODEL', 'gpt-4o')
                    trace_id = self.traceability.create_trace(message, context=context, model=model)
                    self.traceability.add_error(
                        trace_id,
                        'AIServiceException',
                        str(e),
                        {'method': 'process_message'},
                        tb_str
                    )
                    self.traceability.set_route(trace_id, 'error_fallback')
                    self.traceability.finalize_trace(trace_id, {"resposta": result}, {"error": str(e), "source": "error_fallback"})
                except Exception as e2:
                    print(f"[AIService] Erro ao criar trace: {e2}")
            return {"response": result, "trace_id": trace_id, "explicacao": None}
    
    def _mock_response(self, message: str) -> str:
        """
        Retorna erro quando IA não está configurada (não mais resposta determinística)
        """
        print(f"[AIService] LLM não disponível para: {message[:50]}...")
        return (
            "Desculpe, o serviço de IA não está disponível no momento. "
            "Isso pode ocorrer se a chave da API não estiver configurada ou se houver um problema temporário. "
            "Por favor, verifique as configurações ou tente novamente mais tarde. "
            "Se o problema persistir, entre em contato com o suporte técnico."
        )

