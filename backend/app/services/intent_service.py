"""
Serviço para detectar intents e aplicar fluxos configurados pelo usuário
"""
import os
from typing import Optional, Dict, List, Any
from openai import OpenAI

class IntentService:
    """Serviço para detectar intents e aplicar fluxos customizados"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY', '')
        model = os.getenv('AI_MODEL', 'gpt-4o')
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = model
    
    def detect_intent(self, message: str, available_intents: List[Dict]) -> Optional[str]:
        """
        Detecta a intenção da mensagem usando LLM classificador.
        Retorna o ID do intent detectado ou None.
        """
        if not self.client or not available_intents:
            return None
        
        # Preparar lista de intents para o prompt
        intents_list = []
        for intent in available_intents:
            examples_str = ', '.join(intent.get('examples', [])[:3])
            intents_list.append(
                f"- {intent['id']}: {intent.get('name', '')} - {intent.get('description', '')} "
                f"(exemplos: {examples_str})"
            )
        
        prompt = f"""Você é um classificador de intenções. Analise a mensagem do usuário e identifique qual intenção melhor corresponde.

Intents disponíveis:
{chr(10).join(intents_list)}

Mensagem do usuário: "{message}"

Responda APENAS com o ID do intent (ex: "perfil", "carteira", etc.) ou "none" se nenhum intent corresponder.
Não inclua explicações, apenas o ID do intent."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um classificador de intenções preciso. Responda apenas com o ID do intent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            intent_id = response.choices[0].message.content.strip().lower()
            
            # Verificar se o intent_id existe na lista
            intent_ids = [i['id'] for i in available_intents]
            if intent_id in intent_ids:
                return intent_id
            elif intent_id == 'none':
                return None
            else:
                # Tentar encontrar por similaridade parcial
                for intent in available_intents:
                    if intent_id in intent['id'] or intent['id'] in intent_id:
                        return intent['id']
                return None
        except Exception as e:
            print(f"[IntentService] Erro ao detectar intent: {e}")
            return None
    
    def get_intent_flow(self, intent_id: str, agent_builder_config: Dict) -> Optional[Dict]:
        """
        Retorna o fluxo configurado para um intent específico.
        """
        intent_flows = agent_builder_config.get('intent_flows', {})
        return intent_flows.get(intent_id)
    
    def execute_flow(self, flow: Dict, context: Dict) -> Dict:
        """
        Executa um fluxo configurado (nodes e edges).
        Por enquanto retorna estrutura básica - será expandido conforme necessário.
        """
        nodes = flow.get('nodes', [])
        edges = flow.get('edges', [])
        
        # Ordenar nodes por ordem de execução (baseado nas edges)
        execution_order = self._get_execution_order(nodes, edges)
        
        results = {}
        for node_id in execution_order:
            node = next((n for n in nodes if n.get('id') == node_id), None)
            if not node:
                continue
            
            node_type = node.get('type', 'default')
            node_data = node.get('data', {})
            
            if node_type == 'tool':
                # Executar tool
                tool_name = node_data.get('tool_name') or node.get('label', '').lower().replace(' ', '_')
                results[node_id] = {
                    'type': 'tool',
                    'tool': tool_name,
                    'result': None  # Será preenchido pela execução real
                }
            elif node_type == 'prompt':
                # Prompt customizado
                results[node_id] = {
                    'type': 'prompt',
                    'content': node_data.get('content', '')
                }
            elif node_type == 'response':
                # Resposta pré-definida
                results[node_id] = {
                    'type': 'response',
                    'content': node_data.get('content', '')
                }
        
        return results
    
    def _get_execution_order(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """
        Determina a ordem de execução dos nodes baseado nas edges.
        Retorna lista de IDs na ordem de execução.
        """
        if not nodes:
            return []
        
        if not edges:
            # Se não há edges, retornar ordem dos nodes
            return [n.get('id') for n in nodes if n.get('id')]
        
        # Encontrar o node inicial (sem arestas entrando)
        node_ids = {n.get('id') for n in nodes if n.get('id')}
        target_ids = {e.get('target') for e in edges if e.get('target')}
        start_nodes = node_ids - target_ids
        
        if not start_nodes:
            # Se todos os nodes têm arestas entrando, começar do primeiro
            start_nodes = {nodes[0].get('id')} if nodes else set()
        
        # BFS para determinar ordem
        order = []
        visited = set()
        queue = list(start_nodes)
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            order.append(current)
            
            # Adicionar nodes conectados
            for edge in edges:
                if edge.get('source') == current:
                    target = edge.get('target')
                    if target and target not in visited:
                        queue.append(target)
        
        # Adicionar nodes não conectados
        for node in nodes:
            node_id = node.get('id')
            if node_id and node_id not in visited:
                order.append(node_id)
        
        return order

