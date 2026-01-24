'use client'

import Card from '../Card'

export default function TraceHelpPanel() {
  return (
    <Card style={{ padding: '1.5rem' }}>
      <h3 style={{ margin: 0, marginBottom: '1.5rem' }}>Ajuda - Visualização de Trace</h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {/* O que é um Trace */}
        <div>
          <h4 style={{ margin: 0, marginBottom: '0.75rem', fontSize: '1.1rem' }}>O que é um Trace?</h4>
          <p style={{ margin: 0, color: '#666', lineHeight: '1.6' }}>
            Um trace é um registro completo de como o agente processou sua mensagem. Ele mostra todos os passos,
            decisões, ferramentas utilizadas e o raciocínio por trás da resposta gerada. Isso permite transparência
            e auditoria do processo de decisão do agente.
          </p>
        </div>

        {/* Nós do Grafo */}
        <div>
          <h4 style={{ margin: 0, marginBottom: '0.75rem', fontSize: '1.1rem' }}>Nós do Grafo</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ padding: '0.75rem', backgroundColor: '#E8F5E9', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>🔷 Detect Intent</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Detecta a intenção da mensagem do usuário usando análise de palavras-chave.
                Identifica se a pergunta é sobre carteira, adequação, diversificação, etc.
              </div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: '#E3F2FD', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>🔷 Route Decision</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Decide qual rota seguir baseado na intenção detectada:
                <ul style={{ margin: '0.5rem 0 0 1.5rem', padding: 0 }}>
                  <li><strong>bypass</strong>: Para análises simples (obter carteira, adequação, etc.)</li>
                  <li><strong>react</strong>: Para raciocínio complexo que requer múltiplas ferramentas</li>
                </ul>
              </div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: '#FFF3E0', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>🔷 Bypass Analysis</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Análise direta sem agente ReAct. Usado para intenções simples como obter carteira,
                onde uma sequência fixa de ferramentas é suficiente.
              </div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: '#F3E5F5', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>🔷 React Agent</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Agente ReAct que usa ferramentas e raciocina passo a passo. Usado para perguntas
                complexas que requerem múltiplas iterações de pensamento, ação e observação.
              </div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: '#FFEBEE', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>🔷 Format Response</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Formata a resposta final para o usuário, garantindo que seja clara, estruturada e útil.
              </div>
            </div>
          </div>
        </div>

        {/* Edges */}
        <div>
          <h4 style={{ margin: 0, marginBottom: '0.75rem', fontSize: '1.1rem' }}>Edges (Transições)</h4>
          <p style={{ margin: 0, color: '#666', lineHeight: '1.6' }}>
            As setas (edges) mostram o fluxo de execução entre os nós. Uma edge sólida e colorida indica
            que foi percorrida durante a execução, enquanto uma edge tracejada e cinza indica um caminho
            que não foi seguido.
          </p>
        </div>

        {/* Tipos de Passos */}
        <div>
          <h4 style={{ margin: 0, marginBottom: '0.75rem', fontSize: '1.1rem' }}>Tipos de Passos</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ padding: '0.75rem', backgroundColor: '#E8F5E9', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>🔷 graph_step</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Execução de um nó do grafo LangGraph. Mostra quando cada nó foi executado e seus resultados.
              </div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: '#E3F2FD', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>💭 thought</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Raciocínio do agente ReAct - o que o agente está pensando antes de tomar uma ação.
              </div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: '#FFF3E0', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>⚡ action</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Ação executada - chamada de uma ferramenta (tool) para obter informações ou realizar uma análise.
              </div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: '#F3E5F5', borderRadius: '4px' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>👁️ observation</div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                Observação/resultado de uma ação - o que a ferramenta retornou após ser executada.
              </div>
            </div>
          </div>
        </div>

        {/* Campos */}
        <div>
          <h4 style={{ margin: 0, marginBottom: '0.75rem', fontSize: '1.1rem' }}>Campos do Trace</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div>
              <strong>Intent:</strong> Intenção detectada da mensagem (ex: carteira_analysis, buscar_oportunidades)
            </div>
            <div>
              <strong>Route:</strong> Rota escolhida pelo grafo (bypass, react, llm_direct)
            </div>
            <div>
              <strong>Status:</strong> Status do trace (in_progress, completed, error)
            </div>
            <div>
              <strong>Tools Utilizadas:</strong> Lista de ferramentas que foram chamadas durante o processamento
            </div>
          </div>
        </div>

        {/* Legenda de Cores */}
        <div>
          <h4 style={{ margin: 0, marginBottom: '0.75rem', fontSize: '1.1rem' }}>Legenda de Cores</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ display: 'inline-block', width: '20px', height: '20px', backgroundColor: '#4CAF50', borderRadius: '4px' }}></span>
              <span>Nó visitado (executado)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ display: 'inline-block', width: '20px', height: '20px', backgroundColor: '#e0e0e0', borderRadius: '4px' }}></span>
              <span>Nó não visitado (não executado)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ display: 'inline-block', width: '20px', height: '20px', border: '2px solid #2196F3', borderRadius: '4px' }}></span>
              <span>Edge percorrida (transição executada)</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

