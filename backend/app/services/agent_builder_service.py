"""
Serviço para processar comandos conversacionais do Agent Builder
e gerenciar configurações de agentes estilo LangSmith.
"""
import os
import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from app.services.agent_tools import (
    obter_carteira, obter_perfil, analisar_adequacao, calcular_projecao,
    buscar_oportunidades, analisar_alinhamento_objetivos,
    analisar_diversificacao, recomendar_rebalanceamento
)

# Lista de tools disponíveis com metadados
AVAILABLE_TOOLS = {
    'obter_perfil': {
        'name': 'obter_perfil',
        'description': 'Busca o perfil completo do cliente, incluindo perfil de investidor.',
        'function': obter_perfil,
        'parameters': {}
    },
    'obter_carteira': {
        'name': 'obter_carteira',
        'description': 'Busca dados completos da carteira do cliente.',
        'function': obter_carteira,
        'parameters': {}
    },
    'analisar_adequacao': {
        'name': 'analisar_adequacao',
        'description': 'Analisa se a carteira está adequada ao perfil de investidor do cliente.',
        'function': analisar_adequacao,
        'parameters': {}
    },
    'analisar_alinhamento_objetivos': {
        'name': 'analisar_alinhamento_objetivos',
        'description': 'Analisa se a carteira está alinhada com os objetivos do cliente.',
        'function': analisar_alinhamento_objetivos,
        'parameters': {}
    },
    'analisar_diversificacao': {
        'name': 'analisar_diversificacao',
        'description': 'Analisa a diversificação da carteira do cliente.',
        'function': analisar_diversificacao,
        'parameters': {}
    },
    'recomendar_rebalanceamento': {
        'name': 'recomendar_rebalanceamento',
        'description': 'Gera recomendações específicas de rebalanceamento da carteira.',
        'function': recomendar_rebalanceamento,
        'parameters': {}
    },
    'calcular_projecao': {
        'name': 'calcular_projecao',
        'description': 'Calcula projeção de investimento baseada em objetivos e horizonte.',
        'function': calcular_projecao,
        'parameters': {}
    },
    'buscar_oportunidades': {
        'name': 'buscar_oportunidades',
        'description': 'Busca oportunidades de investimento adequadas ao perfil do cliente.',
        'function': buscar_oportunidades,
        'parameters': {}
    }
}

class AgentBuilderService:
    """Serviço para processar comandos conversacionais do Agent Builder"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY', '')
        model = os.getenv('AI_MODEL', 'gpt-4o')
        
        if api_key:
            self.llm = ChatOpenAI(model=model, temperature=0.7, api_key=api_key)
        else:
            self.llm = None
    
    def process_builder_message(self, message: str, current_config: Dict[str, Any], context: List[Dict] = None) -> Dict[str, Any]:
        """
        Processa mensagem do usuário no builder conversacional.
        Retorna resposta do builder e atualizações na configuração.
        """
        if not self.llm:
            return {
                'response': 'Erro: OpenAI API Key não configurada.',
                'config_updates': {},
                'action': None
            }
        
        # Construir prompt para o builder
        system_prompt = """Você é um assistente especializado em ajudar usuários a criar e configurar agentes de IA usando o padrão LangChain Agent Builder.

Você entende comandos como:
- "Quero criar um agente que..." - Cria nova configuração
- "Adicione a tool X" - Adiciona uma tool à lista de tools habilitadas
- "Remova a tool Y" - Remove uma tool
- "Configure a persona para..." - Atualiza a persona (system message)
- "Adicione a instrução..." - Adiciona instrução customizada
- "Configure temperatura para X" - Ajusta temperatura do modelo
- "Configure max_iterations para X" - Ajusta máximo de iterações
- "Teste o agente com..." - Sugere testar o agente

Sua resposta deve ser:
1. Uma resposta conversacional amigável ao usuário
2. Um objeto JSON com as atualizações na configuração (se houver)
3. Uma ação sugerida (se houver)

Formato da resposta:
{
    "response": "sua resposta ao usuário",
    "config_updates": {
        "persona": "...",
        "instrucoes": "...",
        "tools_enabled": {...},
        "temperature": 0.7,
        "max_iterations": 15
    },
    "action": "test" | "save" | null
}

IMPORTANTE: Retorne APENAS JSON válido, sem markdown, sem explicações adicionais."""

        # Construir contexto da conversa
        context_text = ""
        if context:
            context_text = "\n\nHistórico da conversa:\n"
            for msg in context[-5:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    context_text += f"Usuário: {content}\n"
                elif role == 'assistant':
                    context_text += f"Builder: {content}\n"
        
        # Configuração atual
        config_text = f"""
Configuração atual do agente:
- Persona: {current_config.get('persona', 'Não definida')}
- Instruções: {current_config.get('instrucoes', 'Não definidas')}
- Tools habilitadas: {', '.join([k for k, v in current_config.get('tools_enabled', {}).items() if v]) or 'Nenhuma'}
- Temperature: {current_config.get('temperature', 0.7)}
- Max Iterations: {current_config.get('max_iterations', 15)}
"""
        
        user_prompt = f"""{config_text}

{context_text}

Mensagem do usuário: {message}

Responda no formato JSON especificado."""
        
        try:
            # Chamar LLM usando ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Extrair JSON da resposta
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Tentar extrair JSON da resposta
            try:
                # Remover markdown se houver
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Se não conseguir parsear JSON, retornar resposta como texto
                return {
                    'response': response_text,
                    'config_updates': {},
                    'action': None
                }
            
            return result
            
        except Exception as e:
            print(f"[AgentBuilderService] Erro ao processar mensagem: {e}")
            import traceback
            traceback.print_exc()
            return {
                'response': f'Erro ao processar comando: {str(e)}',
                'config_updates': {},
                'action': None
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Retorna lista de tools disponíveis"""
        return [
            {
                'id': tool_id,
                'name': tool_data['name'],
                'description': tool_data['description'],
                'enabled': False  # Será preenchido pela configuração atual
            }
            for tool_id, tool_data in AVAILABLE_TOOLS.items()
        ]
    
    def apply_config_updates(self, current_config: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica atualizações na configuração"""
        updated_config = current_config.copy()
        
        for key, value in updates.items():
            if key == 'tools_enabled' and isinstance(value, dict):
                # Mesclar tools habilitadas
                if 'tools_enabled' not in updated_config:
                    updated_config['tools_enabled'] = {}
                updated_config['tools_enabled'].update(value)
            elif key in ['persona', 'instrucoes', 'temperature', 'max_iterations']:
                updated_config[key] = value
            elif key == 'regras' and isinstance(value, list):
                updated_config['regras'] = value
            elif key == 'exemplos' and isinstance(value, list):
                updated_config['exemplos'] = value
        
        return updated_config
    
    def test_agent(self, message: str, config: Dict[str, Any], context: List[Dict] = None) -> Dict[str, Any]:
        """
        Testa o agente com uma mensagem usando a configuração fornecida.
        Retorna resposta e intermediate steps.
        """
        try:
            from app.services.agent_service import AgentService
            
            # Criar instância temporária do AgentService com configuração customizada
            agent_service = AgentService()
            
            # Processar mensagem com configuração do builder
            result = agent_service.process_message(
                message,
                context=context,
                agent_builder_config=config
            )
            
            if isinstance(result, dict):
                return {
                    'response': result.get('response', ''),
                    'trace_id': result.get('trace_id', ''),
                    'tools_used': result.get('explicacao', {}).get('tools_used', []),
                    'intermediate_steps': result.get('intermediate_steps') or []
                }
            else:
                return {
                    'response': str(result),
                    'trace_id': '',
                    'tools_used': [],
                    'intermediate_steps': []
                }
        except Exception as e:
            print(f"[AgentBuilderService] Erro ao testar agente: {e}")
            import traceback
            traceback.print_exc()
            return {
                'response': f'Erro ao testar agente: {str(e)}',
                'trace_id': '',
                'tools_used': [],
                'intermediate_steps': []
            }

