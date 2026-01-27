"""
Serviço de Traceability para rastreamento completo de decisões e raciocínio do agente.
Armazena traces localmente para auditoria CVM e integra com LangSmith.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class TraceabilityService:
    def __init__(self):
        # Criar diretório de traces (relativo ao diretório do backend)
        # No Elastic Beanstalk, usar /tmp se o diretório padrão não tiver permissões
        base_dir = Path(__file__).parent.parent.parent
        traces_dir_default = base_dir / "data" / "traces"
        
        # Tentar criar diretório padrão
        try:
            traces_dir_default.mkdir(parents=True, exist_ok=True)
            # Testar escrita
            test_file = traces_dir_default / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            self.traces_dir = traces_dir_default
            print(f"[TraceabilityService] Usando diretório padrão: {self.traces_dir}")
        except (PermissionError, OSError) as e:
            # Se falhar, usar /tmp (disponível no EB)
            print(f"[TraceabilityService] Erro ao criar diretório padrão: {e}")
            print("[TraceabilityService] Usando /tmp para traces")
            self.traces_dir = Path("/tmp") / "alphaadvisor_traces"
            self.traces_dir.mkdir(parents=True, exist_ok=True)
            print(f"[TraceabilityService] Diretório de traces: {self.traces_dir}")
        
        self.langsmith_enabled = bool(os.getenv('LANGSMITH_API_KEY'))
        
        # Detail level: 'minimal', 'detailed', 'full'
        # Controls what level of detail is stored (prompts, raw responses, etc.)
        detail_level = os.getenv('TRACE_DETAIL_LEVEL', 'detailed').lower()
        if detail_level not in ['minimal', 'detailed', 'full']:
            detail_level = 'detailed'
        self.detail_level = detail_level
        print(f"[TraceabilityService] Detail level: {self.detail_level}")
        
    def create_trace(self, user_input: str, context: Optional[List] = None, model: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """Cria um novo trace e retorna o trace_id"""
        trace_id = str(uuid.uuid4())
        trace = {
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat(),
            'user_input': user_input,
            'intent': None,
            'route': None,
            'model': model or os.getenv('AI_MODEL', 'gpt-4o'),
            'context': self._sanitize_context(context) if context else None,
            'agent_reasoning': [],
            'graph_steps': [],
            'edges_taken': [],
            'state_snapshots': [],
            'node_timings': {},
            'reasoning_steps': [],
            'events': [],  # Generic event log
            'tool_calls': [],  # Detailed tool call history
            'raw_prompt': None,  # Will be populated if detail_level allows
            'raw_response': None,  # Will be populated if detail_level allows
            'errors': [],  # Error log
            'final_output': None,
            'explanation': None,
            'status': 'in_progress',
            'metadata': metadata or {}  # Metadata para client_id, compliance, etc.
        }
        self._save_trace(trace_id, trace)
        return trace_id
    
    def _sanitize_context(self, context: Optional[List]) -> Optional[List]:
        """Sanitize context based on detail level"""
        if not context:
            return None
        if self.detail_level == 'minimal':
            # Only keep count and roles
            return [{'role': msg.get('role', 'unknown'), 'length': len(str(msg.get('content', '')))} 
                   for msg in context[-6:]]
        elif self.detail_level == 'detailed':
            # Keep content but truncate long messages
            sanitized = []
            for msg in context[-6:]:
                content = str(msg.get('content', ''))
                if len(content) > 500:
                    content = content[:500] + '... [truncated]'
                sanitized.append({
                    'role': msg.get('role', 'unknown'),
                    'content': content
                })
            return sanitized
        else:  # full
            return context[-6:] if len(context) > 6 else context
    
    def add_reasoning_step(self, trace_id: str, step: str, input_data: Dict, 
                          output_data: Dict, tools_used: List[str], 
                          decision: str):
        """Adiciona um passo de raciocínio ao trace"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        reasoning_step = {
            'step': step,
            'input': input_data,
            'output': output_data,
            'tools_used': tools_used,
            'decision': decision,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        trace['agent_reasoning'].append(reasoning_step)
        self._save_trace(trace_id, trace)
    
    def finalize_trace(self, trace_id: str, final_output: Dict, 
                      explanation: Dict):
        """Finaliza o trace com output e explicação"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        trace['final_output'] = final_output
        trace['explanation'] = explanation
        trace['status'] = 'completed'
        trace['completed_at'] = datetime.utcnow().isoformat()
        
        self._save_trace(trace_id, trace)
    
    def add_graph_step(self, trace_id: str, node: str, state_snapshot: Dict, 
                      output: Dict, duration_ms: float = None):
        """Registra execução de um nó do grafo"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        step = {
            'node': node,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': duration_ms,
            'state_snapshot': state_snapshot,
            'output': output
        }
        
        trace['graph_steps'].append(step)
        if duration_ms is not None:
            trace['node_timings'][node] = duration_ms
        self._save_trace(trace_id, trace)
    
    def add_edge(self, trace_id: str, from_node: str, to_node: str, 
                condition: str = None):
        """Registra uma transição (edge) no grafo"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        edge = {
            'from': from_node,
            'to': to_node,
            'condition': condition,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        trace['edges_taken'].append(edge)
        self._save_trace(trace_id, trace)
    
    def add_state_snapshot(self, trace_id: str, node: str, state: Dict):
        """Salva snapshot do estado em um nó específico"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        snapshot = {
            'node': node,
            'timestamp': datetime.utcnow().isoformat(),
            'state': state
        }
        
        trace['state_snapshots'].append(snapshot)
        self._save_trace(trace_id, trace)
    
    def add_reasoning_step_enhanced(self, trace_id: str, step_type: str, 
                                   content: str, tool: str = None, 
                                   input_data: Dict = None, output_data: Dict = None):
        """Adiciona passo de raciocínio melhorado (Thought/Action/Observation)"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        reasoning_step = {
            'type': step_type,  # 'thought', 'action', 'observation'
            'content': content,
            'tool': tool,
            'input': input_data,
            'output': output_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        trace['reasoning_steps'].append(reasoning_step)
        self._save_trace(trace_id, trace)
    
    def set_intent(self, trace_id: str, intent: str):
        """Define a intenção detectada"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        trace['intent'] = intent
        self._save_trace(trace_id, trace)
    
    def set_route(self, trace_id: str, route: str):
        """Define o caminho escolhido (bypass/react)"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        trace['route'] = route
        self._save_trace(trace_id, trace)
    
    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Recupera um trace completo"""
        return self._load_trace(trace_id)
    
    def list_traces(self, limit: int = 50) -> List[Dict]:
        """Lista traces recentes"""
        traces = []
        trace_files = sorted(self.traces_dir.glob("*.json"), 
                           key=lambda x: x.stat().st_mtime, 
                           reverse=True)
        
        for trace_file in trace_files[:limit]:
            try:
                trace = self._load_trace(trace_file.stem)
                if trace:
                    # Retornar apenas informações básicas
                    traces.append({
                        'trace_id': trace.get('trace_id'),
                        'timestamp': trace.get('timestamp'),
                        'user_input': trace.get('user_input'),
                        'intent': trace.get('intent'),
                        'route': trace.get('route'),
                        'status': trace.get('status')
                    })
            except Exception as e:
                print(f"[TraceabilityService] Erro ao carregar trace {trace_file.stem}: {e}")
        
        return traces
    
    def _save_trace(self, trace_id: str, trace: Dict):
        """Salva trace em arquivo JSON"""
        trace_file = self.traces_dir / f"{trace_id}.json"
        with open(trace_file, 'w', encoding='utf-8') as f:
            json.dump(trace, f, indent=2, ensure_ascii=False)
    
    def add_event(self, trace_id: str, event_type: str, payload: Dict, 
                  metadata: Optional[Dict] = None):
        """Adiciona um evento genérico ao trace"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'payload': payload,
            'metadata': metadata or {}
        }
        
        trace['events'].append(event)
        self._save_trace(trace_id, trace)
    
    def add_tool_call(self, trace_id: str, tool_name: str, 
                     input_data: Dict, output_data: Dict,
                     duration_ms: Optional[float] = None,
                     error: Optional[str] = None):
        """Registra uma chamada de tool com detalhes"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        tool_call = {
            'tool_name': tool_name,
            'timestamp': datetime.utcnow().isoformat(),
            'input': input_data,
            'output': self._sanitize_output(output_data) if output_data else None,
            'duration_ms': duration_ms,
            'error': error
        }
        
        trace['tool_calls'].append(tool_call)
        self._save_trace(trace_id, trace)
    
    def add_raw_prompt(self, trace_id: str, prompt: str, 
                      system_prompt: Optional[str] = None):
        """Adiciona prompt raw ao trace (respeitando detail_level)"""
        if self.detail_level == 'minimal':
            return  # Skip raw prompts in minimal mode
        
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        if self.detail_level == 'detailed':
            # Truncate long prompts
            prompt_truncated = prompt[:2000] + '... [truncated]' if len(prompt) > 2000 else prompt
            system_truncated = None
            if system_prompt:
                system_truncated = system_prompt[:1000] + '... [truncated]' if len(system_prompt) > 1000 else system_prompt
            trace['raw_prompt'] = {
                'user_prompt': prompt_truncated,
                'system_prompt': system_truncated
            }
        else:  # full
            trace['raw_prompt'] = {
                'user_prompt': prompt,
                'system_prompt': system_prompt
            }
        
        self._save_trace(trace_id, trace)
    
    def add_raw_response(self, trace_id: str, response: str):
        """Adiciona resposta raw ao trace (respeitando detail_level)"""
        if self.detail_level == 'minimal':
            return  # Skip raw responses in minimal mode
        
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        if self.detail_level == 'detailed':
            # Truncate long responses
            response_truncated = response[:2000] + '... [truncated]' if len(response) > 2000 else response
            trace['raw_response'] = response_truncated
        else:  # full
            trace['raw_response'] = response
        
        self._save_trace(trace_id, trace)
    
    def add_error(self, trace_id: str, error_type: str, error_message: str,
                 error_details: Optional[Dict] = None, stack_trace: Optional[str] = None):
        """Registra um erro no trace"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        error_entry = {
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'details': error_details or {},
            'stack_trace': stack_trace if self.detail_level in ['detailed', 'full'] else None
        }
        
        trace['errors'].append(error_entry)
        trace['status'] = 'error'
        self._save_trace(trace_id, trace)
    
    def _sanitize_output(self, output_data: Any) -> Any:
        """Sanitize output data based on detail level"""
        if self.detail_level == 'minimal':
            # Return summary only
            if isinstance(output_data, dict):
                return {k: f"[{type(v).__name__}]" if not isinstance(v, (str, int, float, bool, type(None))) else v 
                       for k, v in list(output_data.items())[:5]}
            elif isinstance(output_data, (list, tuple)):
                return f"[{len(output_data)} items]"
            else:
                return str(output_data)[:200] if len(str(output_data)) > 200 else output_data
        elif self.detail_level == 'detailed':
            # Truncate large outputs
            if isinstance(output_data, str) and len(output_data) > 1000:
                return output_data[:1000] + '... [truncated]'
            elif isinstance(output_data, dict):
                sanitized = {}
                for k, v in list(output_data.items())[:20]:  # Limit to 20 keys
                    if isinstance(v, str) and len(v) > 500:
                        sanitized[k] = v[:500] + '... [truncated]'
                    else:
                        sanitized[k] = v
                return sanitized
            elif isinstance(output_data, (list, tuple)) and len(output_data) > 50:
                return list(output_data[:50]) + ['... [truncated]']
            return output_data
        else:  # full
            return output_data
    
    def _load_trace(self, trace_id: str) -> Optional[Dict]:
        """Carrega trace de arquivo JSON"""
        trace_file = self.traces_dir / f"{trace_id}.json"
        if not trace_file.exists():
            return None
        
        try:
            with open(trace_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[TraceabilityService] Erro ao carregar trace {trace_id}: {e}")
            return None
    
    def list_traces_filtered(self, limit: int = 50, client_id: Optional[str] = None,
                             status: Optional[str] = None, intent: Optional[str] = None,
                             route: Optional[str] = None, has_handoff: Optional[bool] = None,
                             start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Lista traces com filtros aplicados"""
        traces = []
        trace_files = sorted(self.traces_dir.glob("*.json"), 
                           key=lambda x: x.stat().st_mtime, 
                           reverse=True)
        
        for trace_file in trace_files:
            try:
                trace = self._load_trace(trace_file.stem)
                if not trace:
                    continue
                
                # Aplicar filtros
                if client_id and trace.get('metadata', {}).get('client_id') != client_id:
                    continue
                if status and trace.get('status') != status:
                    continue
                if intent and trace.get('intent') != intent:
                    continue
                if route and trace.get('route') != route:
                    continue
                
                # Filtro de handoff
                if has_handoff is not None:
                    has_handoff_event = any(
                        e.get('type') == 'handoff' for e in trace.get('events', [])
                    )
                    if has_handoff != has_handoff_event:
                        continue
                
                # Filtro de data
                if start_date or end_date:
                    trace_timestamp = trace.get('timestamp')
                    if trace_timestamp:
                        try:
                            trace_dt = datetime.fromisoformat(trace_timestamp.replace('Z', '+00:00'))
                            if start_date:
                                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                                if trace_dt < start_dt:
                                    continue
                            if end_date:
                                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                                if trace_dt > end_dt:
                                    continue
                        except:
                            pass
                
                # Adicionar informações enriquecidas
                trace_info = {
                    'trace_id': trace.get('trace_id'),
                    'timestamp': trace.get('timestamp'),
                    'user_input': trace.get('user_input'),
                    'intent': trace.get('intent'),
                    'route': trace.get('route'),
                    'status': trace.get('status'),
                    'client_id': trace.get('metadata', {}).get('client_id'),
                    'client_name': trace.get('metadata', {}).get('client_name'),
                    'tool_calls_count': len(trace.get('tool_calls', [])),
                    'has_handoff': any(e.get('type') == 'handoff' for e in trace.get('events', [])),
                    'errors_count': len(trace.get('errors', [])),
                    'completed_at': trace.get('completed_at')
                }
                
                traces.append(trace_info)
                
                if len(traces) >= limit:
                    break
                    
            except Exception as e:
                print(f"[TraceabilityService] Erro ao carregar trace {trace_file.stem}: {e}")
        
        return traces
    
    def get_aggregated_stats(self, client_id: Optional[str] = None,
                            start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Retorna estatísticas agregadas dos traces"""
        all_traces = self.list_traces_filtered(
            limit=10000,  # Alto limite para estatísticas
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )
        
        total_traces = len(all_traces)
        total_tool_calls = sum(t.get('tool_calls_count', 0) for t in all_traces)
        total_handoffs = sum(1 for t in all_traces if t.get('has_handoff'))
        total_errors = sum(t.get('errors_count', 0) for t in all_traces)
        
        # Contar por status
        status_counts = {}
        for trace in all_traces:
            status = trace.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Contar por intent
        intent_counts = {}
        for trace in all_traces:
            intent = trace.get('intent') or 'unknown'
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Contar por route
        route_counts = {}
        for trace in all_traces:
            route = trace.get('route') or 'unknown'
            route_counts[route] = route_counts.get(route, 0) + 1
        
        # Top intents
        top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_traces': total_traces,
            'total_tool_calls': total_tool_calls,
            'total_handoffs': total_handoffs,
            'total_errors': total_errors,
            'status_counts': status_counts,
            'intent_counts': intent_counts,
            'route_counts': route_counts,
            'top_intents': [{'intent': k, 'count': v} for k, v in top_intents]
        }
    
    def get_handoffs(self, client_id: Optional[str] = None,
                    start_date: Optional[str] = None, end_date: Optional[str] = None,
                    limit: int = 50) -> List[Dict]:
        """Retorna lista de handoffs (redirecionamentos)"""
        traces = self.list_traces_filtered(
            limit=limit * 2,  # Buscar mais para garantir que temos handoffs suficientes
            client_id=client_id,
            has_handoff=True,
            start_date=start_date,
            end_date=end_date
        )
        
        handoffs = []
        for trace_info in traces:
            trace = self._load_trace(trace_info['trace_id'])
            if not trace:
                continue
            
            # Encontrar eventos de handoff
            for event in trace.get('events', []):
                if event.get('type') == 'handoff':
                    handoff_info = {
                        'trace_id': trace_info['trace_id'],
                        'timestamp': event.get('timestamp'),
                        'reason': event.get('payload', {}).get('reason', 'Não especificado'),
                        'rule': event.get('payload', {}).get('rule', 'Não especificado'),
                        'client_id': trace_info.get('client_id'),
                        'client_name': trace_info.get('client_name'),
                        'user_input': trace_info.get('user_input', '')[:100],  # Primeiros 100 chars
                        'intent': trace_info.get('intent'),
                        'route': trace_info.get('route')
                    }
                    handoffs.append(handoff_info)
        
        # Ordenar por timestamp (mais recente primeiro)
        handoffs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return handoffs[:limit]
    
    def get_compliance_info(self, trace_id: str) -> Dict:
        """Retorna informações de compliance para um trace"""
        trace = self._load_trace(trace_id)
        if not trace:
            return {}
        
        # Calcular idade do trace
        trace_age_days = None
        if trace.get('timestamp'):
            try:
                trace_dt = datetime.fromisoformat(trace.get('timestamp').replace('Z', '+00:00'))
                now = datetime.utcnow()
                trace_age_days = (now - trace_dt.replace(tzinfo=None)).days
            except:
                pass
        
        # Verificar mascaramento de PII
        has_pii_masked = trace.get('metadata', {}).get('pii_masked', False)
        
        # Base legal LGPD
        lgpd_base_legal = trace.get('metadata', {}).get('lgpd_base_legal', 'Não especificado')
        lgpd_consent = trace.get('metadata', {}).get('lgpd_consent', False)
        
        # Auditoria - eventos de acesso (se disponível)
        access_events = [e for e in trace.get('events', []) if e.get('type') == 'access']
        
        return {
            'trace_id': trace_id,
            'trace_age_days': trace_age_days,
            'has_pii_masked': has_pii_masked,
            'lgpd': {
                'base_legal': lgpd_base_legal,
                'consent': lgpd_consent
            },
            'audit': {
                'access_events': len(access_events),
                'access_log': access_events[-10:] if access_events else []  # Últimos 10
            },
            'retention_days': trace.get('metadata', {}).get('retention_days', 90)
        }
    
    def set_trace_metadata(self, trace_id: str, metadata: Dict):
        """Define metadados do trace (client_id, compliance, etc.)"""
        trace = self._load_trace(trace_id)
        if not trace:
            return
        
        if 'metadata' not in trace:
            trace['metadata'] = {}
        
        trace['metadata'].update(metadata)
        self._save_trace(trace_id, trace)

