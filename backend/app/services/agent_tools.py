"""
Tools/Funções que o agente pode usar para análise e recomendações.
Cada tool é decorado com @traceable para rastreamento e retorna dados estruturados.
"""
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langsmith import traceable

# Helper para criar decorator traceable com project_name padrão
def traceable_tool(name: str):
    """Cria decorator traceable com project_name configurado"""
    project_name = os.getenv('LANGSMITH_PROJECT', 'alphaadvisor')
    return traceable(name=name, project_name=project_name)

# Importar dados do cliente
try:
    from app.routes.cliente import CARTEIRA, PERFIL_JOAO
except ImportError:
    # Fallback se não estiver disponível
    CARTEIRA = {}
    PERFIL_JOAO = {}

class CarteiraResponse(BaseModel):
    """Resposta estruturada da carteira"""
    total: float
    dinheiroParado: float = 0
    aporteMensal: float = 0
    objetivo: Dict = {}
    distribuicao: Dict[str, float]
    distribuicaoPercentual: Dict[str, float]
    investimentos: List[Dict]
    adequacaoPerfil: Dict

class AdequacaoResponse(BaseModel):
    """Resposta de análise de adequação"""
    score: int = Field(description="Score de adequação de 0-100")
    problemas: List[str]
    recomendacoes: List[str]
    adequado: bool

class ProjecaoResponse(BaseModel):
    """Resposta de projeção de investimento"""
    valor_atual: float
    valor_projetado: float
    aporte_mensal: float
    prazo_anos: int
    viabilidade: bool
    observacoes: str

class OportunidadeResponse(BaseModel):
    """Resposta de oportunidade de investimento"""
    nome: str
    tipo: str
    adequacao_perfil: str
    rentabilidade: str
    risco: str
    justificativa: str

class AlinhamentoObjetivosResponse(BaseModel):
    """Resposta de análise de alinhamento com objetivos"""
    alinhado_curto_prazo: bool
    alinhado_medio_prazo: bool
    alinhado_longo_prazo: bool
    problemas_curto: List[str]
    problemas_medio: List[str]
    problemas_longo: List[str]
    recomendacoes_curto: List[str]
    recomendacoes_medio: List[str]
    recomendacoes_longo: List[str]
    score_geral: int = Field(description="Score de alinhamento geral de 0-100")

class DiversificacaoResponse(BaseModel):
    """Resposta de análise de diversificação"""
    score_diversificacao: int = Field(description="Score de diversificação de 0-100")
    problemas: List[str]
    concentracao_por_classe: Dict[str, float]
    concentracao_por_ativo: Dict[str, float]
    recomendacoes: List[str]
    adequado: bool

class RebalanceamentoResponse(BaseModel):
    """Resposta de recomendações de rebalanceamento"""
    necessario: bool
    ajustes_sugeridos: List[Dict[str, Any]]
    justificativa: str
    impacto_esperado: str

class PerfilResponse(BaseModel):
    """Resposta do perfil do cliente"""
    nome: str
    idade: int
    profissao: str
    perfilInvestidor: str = Field(description="Perfil de investidor: conservador, moderado ou arrojado")
    patrimonioInvestido: float
    dinheiroParado: float
    aporteMensal: float
    objetivo: Dict
    comportamento: Dict

@traceable_tool("obter_perfil")
def obter_perfil() -> PerfilResponse:
    """
    Busca o perfil completo do cliente, incluindo perfil de investidor.
    Use SEMPRE quando o cliente perguntar sobre seu perfil de investidor ou quando precisar saber o perfil para fazer análises.
    Retorna informações sobre nome, idade, profissão, perfil de investidor (conservador/moderado/arrojado) e outros dados do cliente.
    """
    perfil_data = PERFIL_JOAO if PERFIL_JOAO else {}
    return PerfilResponse(
        nome=perfil_data.get('nome', 'João'),
        idade=perfil_data.get('idade', 38),
        profissao=perfil_data.get('profissao', 'Profissional de Tecnologia'),
        perfilInvestidor=perfil_data.get('perfilInvestidor', 'conservador'),
        patrimonioInvestido=perfil_data.get('patrimonioInvestido', 0),
        dinheiroParado=perfil_data.get('dinheiroParado', 0),
        aporteMensal=perfil_data.get('aporteMensal', 0),
        objetivo=perfil_data.get('objetivo', {}),
        comportamento=perfil_data.get('comportamento', {})
    )

@traceable_tool("obter_carteira")
def obter_carteira() -> CarteiraResponse:
    """
    Busca dados completos da carteira do cliente.
    Retorna estrutura detalhada com investimentos e adequação ao perfil.
    """
    # Por enquanto retorna dados mockados, depois será integrado com API real
    carteira_data = CARTEIRA if CARTEIRA else {}
    return CarteiraResponse(
        total=carteira_data.get('total', 0),
        dinheiroParado=carteira_data.get('dinheiroParado', 0),
        aporteMensal=carteira_data.get('aporteMensal', 0),
        objetivo=carteira_data.get('objetivo', {}),
        distribuicao=carteira_data.get('distribuicao', {}),
        distribuicaoPercentual=carteira_data.get('distribuicaoPercentual', {}),
        investimentos=carteira_data.get('investimentos', []),
        adequacaoPerfil=carteira_data.get('adequacaoPerfil', {})
    )

@traceable_tool("analisar_adequacao")
def analisar_adequacao(carteira: Dict, perfil: str) -> AdequacaoResponse:
    """
    Analisa adequação da carteira ao perfil do investidor.
    Identifica problemas e gera recomendações de rebalanceamento.
    """
    problemas = []
    recomendacoes = []
    score = 100
    
    # Análise de adequação para perfil conservador
    if perfil.lower() == 'conservador':
        # Se carteira é um dict com distribuicaoPercentual
        if isinstance(carteira, dict):
            distribuicao = carteira.get('distribuicaoPercentual', {})
            total = carteira.get('total', 0)
            dinheiro_parado = carteira.get('dinheiroParado', 0)
            total_carteira = total + dinheiro_parado
        else:
            # Se é um objeto Pydantic
            distribuicao = getattr(carteira, 'distribuicaoPercentual', {}) if hasattr(carteira, 'distribuicaoPercentual') else {}
            total = getattr(carteira, 'total', 0) if hasattr(carteira, 'total') else 0
            dinheiro_parado = getattr(carteira, 'dinheiroParado', 0) if hasattr(carteira, 'dinheiroParado') else 0
            total_carteira = total + dinheiro_parado
        
        # Verificar renda variável (deve ser 10-15% para conservador)
        renda_variavel_pct = distribuicao.get('rendaVariavel', 0) if isinstance(distribuicao, dict) else 0
        if renda_variavel_pct > 15:
            excesso = renda_variavel_pct - 15
            valor_excesso = (excesso / 100) * total_carteira
            problemas.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) acima do recomendado (10-15%)")
            score -= 20
            recomendacoes.append(f"Reduzir exposição a renda variável para 10-15% do patrimônio. Sugestão: realocar R$ {valor_excesso:,.2f} para renda fixa")
        
        # Verificar liquidez (deve ser 15-20% para conservador)
        liquidez_pct = distribuicao.get('liquidez', 0) if isinstance(distribuicao, dict) else 0
        if liquidez_pct < 15:
            deficit = 15 - liquidez_pct
            valor_deficit = (deficit / 100) * total_carteira
            problemas.append(f"Liquidez ({liquidez_pct:.1f}%) abaixo do ideal (15-20%)")
            score -= 15
            recomendacoes.append(f"Aumentar reserva de emergência para 15-20% do patrimônio. Sugestão: alocar R$ {valor_deficit:,.2f} do dinheiro parado em produtos de liquidez diária")
        
        # Verificar renda fixa (deve ser 70-85% para conservador)
        renda_fixa_pct = distribuicao.get('rendaFixa', 0) if isinstance(distribuicao, dict) else 0
        if renda_fixa_pct < 70:
            problemas.append(f"Renda fixa ({renda_fixa_pct:.1f}%) abaixo do ideal para perfil conservador (70-85%)")
            score -= 10
            recomendacoes.append("Aumentar exposição a renda fixa para melhor adequação ao perfil conservador")
    
    adequado = score >= 70
    
    return AdequacaoResponse(
        score=score,
        problemas=problemas,
        recomendacoes=recomendacoes,
        adequado=adequado
    )

@traceable_tool("calcular_projecao")
def calcular_projecao(valor_atual=None, aporte_mensal=None, 
                     prazo_anos=None, rentabilidade_anual: float = 0.10,
                     carteira: Optional[Dict] = None, perfil: Optional[Dict] = None) -> ProjecaoResponse:
    """
    Calcula projeção de investimento considerando aportes mensais e rentabilidade.
    Usa juros compostos para cálculo.
    
    Aceita dois formatos de entrada:
    1. Valores numéricos: valor_atual (float), aporte_mensal (float), prazo_anos (int)
    2. Dicionários: carteira (dict), perfil (dict) - extrai valores automaticamente
    """
    # Se recebeu dicionários, extrair valores (apenas se valores numéricos não foram fornecidos)
    if carteira is not None or perfil is not None:
        # Extrair valor_atual da carteira (apenas se não foi fornecido explicitamente)
        if valor_atual is None and carteira and isinstance(carteira, dict):
            valor_atual = carteira.get('total', 0.0)
            if valor_atual == 0:
                valor_atual = carteira.get('patrimonioInvestido', 0.0)
        
        # Extrair aporte_mensal da carteira ou perfil (apenas se não foi fornecido explicitamente)
        if aporte_mensal is None:
            if carteira and isinstance(carteira, dict):
                aporte_mensal = carteira.get('aporteMensal', 0.0)
            if (aporte_mensal is None or aporte_mensal == 0) and perfil and isinstance(perfil, dict):
                aporte_mensal = perfil.get('aporteMensal', 0.0)
        
        # Extrair prazo_anos do objetivo no perfil ou carteira (apenas se não foi fornecido explicitamente)
        if prazo_anos is None:
            objetivo = None
            if perfil and isinstance(perfil, dict):
                objetivo = perfil.get('objetivo', {})
            if (not objetivo or not isinstance(objetivo, dict)) and carteira and isinstance(carteira, dict):
                objetivo = carteira.get('objetivo', {})
            
            if objetivo and isinstance(objetivo, dict):
                prazo_anos = objetivo.get('prazo', 5)  # Default 5 anos se não especificado
            else:
                prazo_anos = 5  # Default se não encontrado
    
    # Validar valores extraídos ou fornecidos
    if valor_atual is None:
        valor_atual = 0.0
    if aporte_mensal is None:
        aporte_mensal = 0.0
    if prazo_anos is None:
        prazo_anos = 5  # Default 5 anos
    
    # Converter para tipos corretos
    try:
        valor_atual = float(valor_atual)
        aporte_mensal = float(aporte_mensal)
        prazo_anos = int(prazo_anos)
    except (ValueError, TypeError):
        raise ValueError(f"Valores inválidos para calcular_projecao: valor_atual={valor_atual}, aporte_mensal={aporte_mensal}, prazo_anos={prazo_anos}")
    
    meses = prazo_anos * 12
    rentabilidade_mensal = (1 + rentabilidade_anual) ** (1/12) - 1
    
    # Valor futuro com juros compostos
    valor_futuro = valor_atual * ((1 + rentabilidade_mensal) ** meses)
    
    # Aportes mensais com juros compostos
    if aporte_mensal > 0:
        valor_aportes = aporte_mensal * (((1 + rentabilidade_mensal) ** meses - 1) / rentabilidade_mensal)
        valor_futuro += valor_aportes
    
    # Extrair objetivo do perfil ou carteira, ou usar default
    objetivo = 1000000  # Default
    if perfil and isinstance(perfil, dict):
        obj_perfil = perfil.get('objetivo', {})
        if isinstance(obj_perfil, dict):
            objetivo = obj_perfil.get('valor', objetivo)
    if objetivo == 1000000 and carteira and isinstance(carteira, dict):
        obj_carteira = carteira.get('objetivo', {})
        if isinstance(obj_carteira, dict):
            objetivo = obj_carteira.get('valor', objetivo)
    
    viabilidade = valor_futuro >= objetivo
    
    observacoes = ""
    if not viabilidade:
        deficit = objetivo - valor_futuro
        observacoes = f"Para atingir o objetivo, seria necessário aumentar o aporte mensal ou o prazo."
    
    return ProjecaoResponse(
        valor_atual=valor_atual,
        valor_projetado=valor_futuro,
        aporte_mensal=aporte_mensal,
        prazo_anos=prazo_anos,
        viabilidade=viabilidade,
        observacoes=observacoes
    )

@traceable_tool("buscar_oportunidades")
def buscar_oportunidades(perfil: str, problemas: List[str]) -> List[OportunidadeResponse]:
    """
    Busca oportunidades de investimento adequadas ao perfil e problemas identificados.
    """
    oportunidades = []
    
    # Para perfil conservador com problemas identificados
    if perfil.lower() == 'conservador':
        # Se liquidez baixa, recomendar produtos líquidos
        if any('liquidez' in p.lower() for p in problemas):
            oportunidades.append(OportunidadeResponse(
                nome="CDB Liquidez Diária",
                tipo="CDB",
                adequacao_perfil="Alta",
                rentabilidade="100% CDI",
                risco="Baixo",
                justificativa="Produto adequado para aumentar liquidez mantendo rentabilidade"
            ))
            
            oportunidades.append(OportunidadeResponse(
                nome="Tesouro Selic",
                tipo="Tesouro Direto",
                adequacao_perfil="Alta",
                rentabilidade="SELIC",
                risco="Baixíssimo",
                justificativa="Liquidez diária com segurança do governo federal"
            ))
        
        # Se renda variável alta, recomendar reduzir e realocar em renda fixa
        if any('renda variável' in p.lower() for p in problemas):
            oportunidades.append(OportunidadeResponse(
                nome="CDB 110% CDI 2 anos",
                tipo="CDB",
                adequacao_perfil="Alta",
                rentabilidade="110% CDI",
                risco="Baixo",
                justificativa="Alternativa conservadora para substituir parte da renda variável"
            ))
            
            oportunidades.append(OportunidadeResponse(
                nome="LCI 95% CDI 3 anos",
                tipo="LCI",
                adequacao_perfil="Alta",
                rentabilidade="95% CDI",
                risco="Baixo",
                justificativa="Isenção de IR e IOF, adequado para perfil conservador"
            ))
    
    return oportunidades

@traceable_tool("analisar_alinhamento_objetivos")
def analisar_alinhamento_objetivos(carteira: Dict, perfil: Dict) -> AlinhamentoObjetivosResponse:
    """
    Analisa alinhamento da carteira com objetivos de curto, médio e longo prazo.
    Avalia adequação da alocação considerando horizontes temporais.
    """
    # Obter dados da carteira
    if isinstance(carteira, dict):
        distribuicao = carteira.get('distribuicaoPercentual', {})
        total = carteira.get('total', 0)
        dinheiro_parado = carteira.get('dinheiroParado', 0)
        objetivo = carteira.get('objetivo', {})
    else:
        distribuicao = getattr(carteira, 'distribuicaoPercentual', {}) if hasattr(carteira, 'distribuicaoPercentual') else {}
        total = getattr(carteira, 'total', 0) if hasattr(carteira, 'total') else 0
        dinheiro_parado = getattr(carteira, 'dinheiroParado', 0) if hasattr(carteira, 'dinheiroParado') else 0
        objetivo = getattr(carteira, 'objetivo', {}) if hasattr(carteira, 'objetivo') else {}
    
    # Obter dados do perfil
    if isinstance(perfil, dict):
        perfil_investidor = perfil.get('perfilInvestidor', 'conservador')
        objetivo_valor = objetivo.get('valor', 0) if isinstance(objetivo, dict) else 0
        objetivo_prazo = objetivo.get('prazo', 0) if isinstance(objetivo, dict) else 0
    else:
        perfil_investidor = getattr(perfil, 'perfilInvestidor', 'conservador') if hasattr(perfil, 'perfilInvestidor') else 'conservador'
        objetivo_valor = objetivo.get('valor', 0) if isinstance(objetivo, dict) else 0
        objetivo_prazo = objetivo.get('prazo', 0) if isinstance(objetivo, dict) else 0
    
    total_carteira = total + dinheiro_parado
    liquidez_pct = distribuicao.get('liquidez', 0) if isinstance(distribuicao, dict) else 0
    renda_fixa_pct = distribuicao.get('rendaFixa', 0) if isinstance(distribuicao, dict) else 0
    renda_variavel_pct = distribuicao.get('rendaVariavel', 0) if isinstance(distribuicao, dict) else 0
    
    # Análise para CURTO PRAZO (até 3 anos)
    problemas_curto = []
    recomendacoes_curto = []
    alinhado_curto = True
    
    # Curto prazo precisa de alta liquidez (20-30% para objetivos de curto prazo)
    if liquidez_pct < 20:
        problemas_curto.append(f"Liquidez insuficiente ({liquidez_pct:.1f}%) para objetivos de curto prazo (recomendado: 20-30%)")
        alinhado_curto = False
        recomendacoes_curto.append(f"Aumentar liquidez para 20-30% do patrimônio para garantir acesso a recursos de curto prazo")
    
    # Curto prazo deve ter baixa exposição a renda variável (máximo 10%)
    if renda_variavel_pct > 10:
        problemas_curto.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) alta para objetivos de curto prazo (recomendado: até 10%)")
        alinhado_curto = False
        recomendacoes_curto.append("Reduzir exposição a renda variável para objetivos de curto prazo devido à volatilidade")
    
    # Análise para MÉDIO PRAZO (3 a 10 anos)
    problemas_medio = []
    recomendacoes_medio = []
    alinhado_medio = True
    
    # Médio prazo pode ter mais renda fixa e alguma renda variável (10-20%)
    if perfil_investidor == 'conservador':
        if renda_variavel_pct > 20:
            problemas_medio.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) acima do ideal para perfil conservador em médio prazo (recomendado: 10-20%)")
            alinhado_medio = False
            recomendacoes_medio.append("Ajustar alocação para médio prazo: manter 10-20% em renda variável e 70-80% em renda fixa")
    
    # Análise para LONGO PRAZO (acima de 10 anos)
    problemas_longo = []
    recomendacoes_longo = []
    alinhado_longo = True
    
    # Longo prazo pode tolerar mais renda variável, mas para conservador ainda limitado
    if perfil_investidor == 'conservador':
        if renda_variavel_pct > 15:
            problemas_longo.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) acima do recomendado para perfil conservador mesmo em longo prazo (recomendado: 10-15%)")
            alinhado_longo = False
            recomendacoes_longo.append("Para longo prazo com perfil conservador, manter 10-15% em renda variável e 75-85% em renda fixa")
    
    # Verificar se há objetivo específico e se a carteira está alinhada
    if objetivo_valor > 0 and objetivo_prazo > 0:
        # Calcular se o objetivo é viável (simplificado)
        if objetivo_prazo <= 3:  # Curto prazo
            if not alinhado_curto:
                problemas_curto.append(f"Alocação atual pode não ser adequada para atingir objetivo de R$ {objetivo_valor:,.2f} em {objetivo_prazo} anos")
        elif objetivo_prazo <= 10:  # Médio prazo
            if not alinhado_medio:
                problemas_medio.append(f"Alocação atual pode não ser adequada para atingir objetivo de R$ {objetivo_valor:,.2f} em {objetivo_prazo} anos")
        else:  # Longo prazo
            if not alinhado_longo:
                problemas_longo.append(f"Alocação atual pode não ser adequada para atingir objetivo de R$ {objetivo_valor:,.2f} em {objetivo_prazo} anos")
    
    # Calcular score geral
    score_geral = 100
    if not alinhado_curto:
        score_geral -= 25
    if not alinhado_medio:
        score_geral -= 25
    if not alinhado_longo:
        score_geral -= 25
    
    return AlinhamentoObjetivosResponse(
        alinhado_curto_prazo=alinhado_curto,
        alinhado_medio_prazo=alinhado_medio,
        alinhado_longo_prazo=alinhado_longo,
        problemas_curto=problemas_curto,
        problemas_medio=problemas_medio,
        problemas_longo=problemas_longo,
        recomendacoes_curto=recomendacoes_curto,
        recomendacoes_medio=recomendacoes_medio,
        recomendacoes_longo=recomendacoes_longo,
        score_geral=score_geral
    )

@traceable_tool("analisar_diversificacao")
def analisar_diversificacao(carteira: Dict) -> DiversificacaoResponse:
    """
    Analisa diversificação da carteira por classe de ativo e por ativo individual.
    Identifica concentrações excessivas e sugere melhorias.
    """
    problemas = []
    recomendacoes = []
    score = 100
    
    # Obter dados da carteira
    if isinstance(carteira, dict):
        investimentos = carteira.get('investimentos', [])
        total = carteira.get('total', 0)
        distribuicao = carteira.get('distribuicaoPercentual', {})
    else:
        investimentos = getattr(carteira, 'investimentos', []) if hasattr(carteira, 'investimentos') else []
        total = getattr(carteira, 'total', 0) if hasattr(carteira, 'total') else 0
        distribuicao = getattr(carteira, 'distribuicaoPercentual', {}) if hasattr(carteira, 'distribuicaoPercentual') else {}
    
    # Calcular concentração por classe
    concentracao_classe = {}
    for inv in investimentos:
        classe = inv.get('classe', 'outros')
        valor = float(inv.get('valor', 0) or 0)
        if classe not in concentracao_classe:
            concentracao_classe[classe] = 0
        concentracao_classe[classe] += valor
    
    # Converter para percentuais
    concentracao_classe_pct = {}
    for classe, valor in concentracao_classe.items():
        if total > 0:
            concentracao_classe_pct[classe] = (valor / total) * 100
        else:
            concentracao_classe_pct[classe] = 0
    
    # Calcular concentração por ativo individual
    concentracao_ativo = {}
    for inv in investimentos:
        nome = inv.get('nome', 'Desconhecido')
        valor = float(inv.get('valor', 0) or 0)
        if total > 0:
            pct = (valor / total) * 100
            concentracao_ativo[nome] = pct
    
    # Verificar concentração excessiva por classe (mais de 80% em uma classe)
    for classe, pct in concentracao_classe_pct.items():
        if pct > 80:
            problemas.append(f"Concentração excessiva em {classe} ({pct:.1f}%) - acima do recomendado (máximo 80%)")
            score -= 20
            recomendacoes.append(f"Diversificar reduzindo exposição a {classe} e distribuindo para outras classes")
    
    # Verificar concentração excessiva por ativo (mais de 30% em um único ativo)
    for ativo, pct in concentracao_ativo.items():
        if pct > 30:
            problemas.append(f"Concentração excessiva no ativo {ativo} ({pct:.1f}%) - acima do recomendado (máximo 30%)")
            score -= 15
            recomendacoes.append(f"Reduzir exposição ao ativo {ativo} e diversificar em outros investimentos")
    
    # Verificar número de ativos (pouca diversificação)
    num_ativos = len(investimentos)
    if num_ativos < 3:
        problemas.append(f"Poucos investimentos ({num_ativos}) - recomendado ter pelo menos 3-5 ativos diferentes")
        score -= 10
        recomendacoes.append("Aumentar número de investimentos para melhor diversificação")
    
    # Verificar se há diversificação geográfica/institucional (simplificado)
    instituicoes = set()
    for inv in investimentos:
        nome = inv.get('nome', '')
        # Extrair instituição do nome (simplificado)
        if 'XP' in nome:
            instituicoes.add('XP')
        elif 'Banco do Brasil' in nome or 'BB' in nome:
            instituicoes.add('BB')
        elif 'Tesouro' in nome:
            instituicoes.add('Tesouro Direto')
        elif 'B3' in nome or 'PETR' in nome:
            instituicoes.add('B3')
    
    if len(instituicoes) < 2 and num_ativos >= 3:
        problemas.append(f"Concentração em poucas instituições ({len(instituicoes)}) - recomendado diversificar entre diferentes instituições")
        score -= 5
        recomendacoes.append("Considerar diversificar entre diferentes instituições financeiras para reduzir risco")
    
    adequado = score >= 70
    
    return DiversificacaoResponse(
        score_diversificacao=score,
        problemas=problemas,
        concentracao_por_classe=concentracao_classe_pct,
        concentracao_por_ativo=concentracao_ativo,
        recomendacoes=recomendacoes,
        adequado=adequado
    )

@traceable_tool("recomendar_rebalanceamento")
def recomendar_rebalanceamento(carteira: Dict, perfil: str) -> RebalanceamentoResponse:
    """
    Gera recomendações específicas de rebalanceamento baseadas na análise de adequação.
    """
    # Obter carteira e analisar adequação
    if isinstance(carteira, dict):
        carteira_dict = carteira
    else:
        if hasattr(carteira, 'model_dump'):
            carteira_dict = carteira.model_dump()
        elif hasattr(carteira, 'dict'):
            carteira_dict = carteira.dict()
        else:
            carteira_dict = carteira if isinstance(carteira, dict) else {}
    
    adequacao = analisar_adequacao(carteira_dict, perfil)
    adequacao_dict = adequacao.model_dump() if hasattr(adequacao, 'model_dump') else adequacao.dict() if hasattr(adequacao, 'dict') else adequacao
    
    necessario = not adequacao_dict.get('adequado', True)
    ajustes_sugeridos = []
    
    if necessario:
        distribuicao = carteira_dict.get('distribuicaoPercentual', {})
        total = carteira_dict.get('total', 0)
        dinheiro_parado = carteira_dict.get('dinheiroParado', 0)
        total_carteira = total + dinheiro_parado
        
        renda_variavel_pct = distribuicao.get('rendaVariavel', 0)
        liquidez_pct = distribuicao.get('liquidez', 0)
        renda_fixa_pct = distribuicao.get('rendaFixa', 0)
        
        # Ajuste 1: Reduzir renda variável se acima de 15%
        if renda_variavel_pct > 15:
            excesso_pct = renda_variavel_pct - 15
            valor_ajuste = (excesso_pct / 100) * total_carteira
            ajustes_sugeridos.append({
                'acao': 'Reduzir renda variável',
                'valor': valor_ajuste,
                'de': f'{renda_variavel_pct:.1f}%',
                'para': '15%',
                'justificativa': 'Adequar ao perfil conservador'
            })
        
        # Ajuste 2: Aumentar liquidez se abaixo de 15%
        if liquidez_pct < 15:
            deficit_pct = 15 - liquidez_pct
            valor_ajuste = (deficit_pct / 100) * total_carteira
            ajustes_sugeridos.append({
                'acao': 'Aumentar liquidez',
                'valor': valor_ajuste,
                'de': f'{liquidez_pct:.1f}%',
                'para': '15%',
                'justificativa': 'Garantir reserva de emergência adequada'
            })
        
        # Ajuste 3: Aumentar renda fixa se abaixo de 70%
        if renda_fixa_pct < 70:
            deficit_pct = 70 - renda_fixa_pct
            valor_ajuste = (deficit_pct / 100) * total_carteira
            ajustes_sugeridos.append({
                'acao': 'Aumentar renda fixa',
                'valor': valor_ajuste,
                'de': f'{renda_fixa_pct:.1f}%',
                'para': '70%',
                'justificativa': 'Adequar ao perfil conservador'
            })
        
        justificativa = f"Rebalanceamento necessário para adequar carteira ao perfil {perfil}. Score atual: {adequacao_dict.get('score', 0)}/100"
        impacto_esperado = f"Após rebalanceamento, espera-se score de adequação acima de 70/100, melhorando alinhamento com perfil conservador"
    else:
        justificativa = "Carteira já está adequadamente balanceada para o perfil"
        impacto_esperado = "Manter alocação atual"
    
    return RebalanceamentoResponse(
        necessario=necessario,
        ajustes_sugeridos=ajustes_sugeridos,
        justificativa=justificativa,
        impacto_esperado=impacto_esperado
    )

@traceable_tool("gerar_explicacao")
def gerar_explicacao(recomendacao: Dict, dados_utilizados: Dict, 
                    regras_aplicadas: List[str]) -> Dict:
    """
    Gera explicação estruturada do raciocínio e recomendação.
    """
    return {
        'recomendacao': recomendacao,
        'dados_utilizados': dados_utilizados,
        'regras_aplicadas': regras_aplicadas,
        'timestamp': datetime.utcnow().isoformat()
    }

