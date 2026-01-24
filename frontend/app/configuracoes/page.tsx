'use client'

import { useState } from 'react'
import Toggle from '../components/Toggle'
import '../globals.css'

export default function Configuracoes() {
  const [config, setConfig] = useState({
    // Configurações Gerais
    modeloIA: 'gpt-4o',
    tomConversa: 'formal',
    tamanhoResposta: 'detalhada',
    idioma: 'pt-BR',
    ocultarValores: false,
    confirmarAcoes: true,
    escreverLogs: false,
    
    // Configurações de Ofertas
    habilitarOfertas: true,
    evitarOfertasSensiveis: true,
    modoEducativo: false,
    ofertasProativas: true,
    perfilInvestidor: 'conservador',
    estiloOfertasReativas: 'consultivo',
    estiloOfertasProativas: 'leve',
    turnosMinimos: 2,
    minutosMinimos: 30,
    tempoInatividade: 300,
    maxOfertasProativas: 3,
    horarioInicio: 9,
    horarioFim: 18,
    
    // Ferramentas
    consultaSaldo: true,
    carteiraAtual: true,
    evolucaoCarteira: true,
    ativosDisponiveis: true,
    minhasOrdens: true,
    meusResgates: true,
    inicioCarteira: true,
    simulacaoCDB: true,
    
    // Performance
    maxItens: 100,
    maxChamadas: 10,
    timeoutLLM: 30,
    diasRetencao: 90,
    
    // Alertas
    alertasVencimento: true,
    oportunidadesProativas: true,
    alertasMercado: true
  })

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="configuracoes-page">
      <h2>Configurações</h2>

      <section className="config-section">
        <h3>Configurações Gerais</h3>
        <div className="card">
          <div className="config-item">
            <label>Modelo de IA:</label>
            <select
              className="input"
              value={config.modeloIA}
              onChange={(e) => updateConfig('modeloIA', e.target.value)}
            >
              <option value="gpt-4o">GPT-4o (Recomendado)</option>
              <option value="gpt-4o-mini">GPT-4o Mini (Rápido)</option>
            </select>
          </div>

          <div className="config-item">
            <label>Tom da Conversa:</label>
            <select
              className="input"
              value={config.tomConversa}
              onChange={(e) => updateConfig('tomConversa', e.target.value)}
            >
              <option value="formal">Formal</option>
              <option value="coloquial">Coloquial</option>
            </select>
          </div>

          <div className="config-item">
            <label>Tamanho da Resposta:</label>
            <select
              className="input"
              value={config.tamanhoResposta}
              onChange={(e) => updateConfig('tamanhoResposta', e.target.value)}
            >
              <option value="detalhada">Detalhada</option>
              <option value="curta">Curta</option>
            </select>
          </div>

          <div className="config-item">
            <label>Idioma:</label>
            <select
              className="input"
              value={config.idioma}
              onChange={(e) => updateConfig('idioma', e.target.value)}
            >
              <option value="pt-BR">Português (Brasil)</option>
              <option value="en-US">English (US)</option>
            </select>
          </div>

          <div className="config-item">
            <Toggle
              checked={config.ocultarValores}
              onChange={(checked) => updateConfig('ocultarValores', checked)}
              label="Ocultar valores sensíveis"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.confirmarAcoes}
              onChange={(checked) => updateConfig('confirmarAcoes', checked)}
              label="Confirmar ações sensíveis"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.escreverLogs}
              onChange={(checked) => updateConfig('escreverLogs', checked)}
              label="Escrever logs"
            />
          </div>

          <div className="config-actions">
            <button className="btn">Salvar</button>
            <button className="btn btn-secondary">Resetar</button>
            <button className="btn btn-secondary">Exportar</button>
            <button className="btn btn-secondary">Importar</button>
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Configurações de Ofertas</h3>
        <div className="card">
          <div className="config-item">
            <Toggle
              checked={config.habilitarOfertas}
              onChange={(checked) => updateConfig('habilitarOfertas', checked)}
              label="Habilitar sistema de ofertas"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.evitarOfertasSensiveis}
              onChange={(checked) => updateConfig('evitarOfertasSensiveis', checked)}
              label="Evitar ofertas em contextos sensíveis"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.modoEducativo}
              onChange={(checked) => updateConfig('modoEducativo', checked)}
              label="Modo educativo (sem botões de ação)"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.ofertasProativas}
              onChange={(checked) => updateConfig('ofertasProativas', checked)}
              label="Habilitar ofertas proativas"
            />
          </div>

          <div className="config-item">
            <label>Perfil do investidor:</label>
            <select
              className="input"
              value={config.perfilInvestidor}
              onChange={(e) => updateConfig('perfilInvestidor', e.target.value)}
            >
              <option value="conservador">Conservador</option>
              <option value="moderado">Moderado</option>
              <option value="arrojado">Arrojado</option>
            </select>
          </div>

          <div className="config-item">
            <label>Estilo de ofertas reativas:</label>
            <select
              className="input"
              value={config.estiloOfertasReativas}
              onChange={(e) => updateConfig('estiloOfertasReativas', e.target.value)}
            >
              <option value="consultivo">Consultivo</option>
              <option value="direto">Direto</option>
              <option value="educativo">Educativo</option>
            </select>
          </div>

          <div className="config-item">
            <label>Estilo de ofertas proativas:</label>
            <select
              className="input"
              value={config.estiloOfertasProativas}
              onChange={(e) => updateConfig('estiloOfertasProativas', e.target.value)}
            >
              <option value="leve">Leve</option>
              <option value="comercial">Comercial</option>
            </select>
          </div>

          <div className="config-item">
            <label>Turnos mínimos entre ofertas:</label>
            <input
              type="number"
              className="input"
              value={config.turnosMinimos}
              onChange={(e) => updateConfig('turnosMinimos', parseInt(e.target.value))}
            />
          </div>

          <div className="config-item">
            <label>Minutos mínimos entre ofertas:</label>
            <input
              type="number"
              className="input"
              value={config.minutosMinimos}
              onChange={(e) => updateConfig('minutosMinimos', parseInt(e.target.value))}
            />
          </div>

          <div className="config-item">
            <label>Tempo de inatividade para trigger proativo (segundos):</label>
            <input
              type="number"
              className="input"
              value={config.tempoInatividade}
              onChange={(e) => updateConfig('tempoInatividade', parseInt(e.target.value))}
            />
          </div>

          <div className="config-item">
            <label>Máximo de ofertas proativas por sessão:</label>
            <input
              type="number"
              className="input"
              value={config.maxOfertasProativas}
              onChange={(e) => updateConfig('maxOfertasProativas', parseInt(e.target.value))}
            />
          </div>

          <div className="config-item">
            <label>Horário comercial - início (24h):</label>
            <input
              type="number"
              className="input"
              value={config.horarioInicio}
              onChange={(e) => updateConfig('horarioInicio', parseInt(e.target.value))}
              min="0"
              max="23"
            />
          </div>

          <div className="config-item">
            <label>Horário comercial - fim (24h):</label>
            <input
              type="number"
              className="input"
              value={config.horarioFim}
              onChange={(e) => updateConfig('horarioFim', parseInt(e.target.value))}
              min="0"
              max="23"
            />
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Ferramentas Habilitadas</h3>
        <div className="card">
          <div className="config-item">
            <Toggle
              checked={config.consultaSaldo}
              onChange={(checked) => updateConfig('consultaSaldo', checked)}
              label="Consulta de saldo/extrato"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.carteiraAtual}
              onChange={(checked) => updateConfig('carteiraAtual', checked)}
              label="Carteira atual"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.evolucaoCarteira}
              onChange={(checked) => updateConfig('evolucaoCarteira', checked)}
              label="Evolução da carteira"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.ativosDisponiveis}
              onChange={(checked) => updateConfig('ativosDisponiveis', checked)}
              label="Ativos disponíveis"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.minhasOrdens}
              onChange={(checked) => updateConfig('minhasOrdens', checked)}
              label="Minhas ordens"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.meusResgates}
              onChange={(checked) => updateConfig('meusResgates', checked)}
              label="Meus resgates"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.inicioCarteira}
              onChange={(checked) => updateConfig('inicioCarteira', checked)}
              label="Início da carteira"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.simulacaoCDB}
              onChange={(checked) => updateConfig('simulacaoCDB', checked)}
              label="Simulação de rentabilidade CDB"
            />
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Configurações de Performance</h3>
        <div className="card">
          <div className="config-item">
            <label>Máximo de itens para renderizar:</label>
            <input
              type="number"
              className="input"
              value={config.maxItens}
              onChange={(e) => updateConfig('maxItens', parseInt(e.target.value))}
            />
          </div>
          <div className="config-item">
            <label>Máximo de chamadas de ferramentas:</label>
            <input
              type="number"
              className="input"
              value={config.maxChamadas}
              onChange={(e) => updateConfig('maxChamadas', parseInt(e.target.value))}
            />
          </div>
          <div className="config-item">
            <label>Timeout do LLM (segundos):</label>
            <input
              type="number"
              className="input"
              value={config.timeoutLLM}
              onChange={(e) => updateConfig('timeoutLLM', parseInt(e.target.value))}
            />
          </div>
          <div className="config-item">
            <label>Dias de retenção do histórico:</label>
            <input
              type="number"
              className="input"
              value={config.diasRetencao}
              onChange={(e) => updateConfig('diasRetencao', parseInt(e.target.value))}
            />
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Alertas Inteligentes</h3>
        <div className="card">
          <div className="config-item">
            <Toggle
              checked={config.alertasVencimento}
              onChange={(checked) => updateConfig('alertasVencimento', checked)}
              label="Alertas de vencimento automáticos"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.oportunidadesProativas}
              onChange={(checked) => updateConfig('oportunidadesProativas', checked)}
              label="Oportunidades proativas"
            />
          </div>
          <div className="config-item">
            <Toggle
              checked={config.alertasMercado}
              onChange={(checked) => updateConfig('alertasMercado', checked)}
              label="Alertas de mercado"
            />
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Telemetria</h3>
        <div className="card">
          <div className="telemetria-stats">
            <div className="telemetria-item">
              <span className="telemetria-label">Sessões hoje:</span>
              <span className="telemetria-value">47</span>
            </div>
            <div className="telemetria-item">
              <span className="telemetria-label">Tempo médio:</span>
              <span className="telemetria-value">12min</span>
            </div>
            <div className="telemetria-item">
              <span className="telemetria-label">Taxa de conversão:</span>
              <span className="telemetria-value">68%</span>
            </div>
          </div>
          <button className="btn btn-secondary" style={{ marginTop: '1rem' }}>
            Ver Detalhes Completos
          </button>
        </div>
      </section>
    </div>
  )
}




