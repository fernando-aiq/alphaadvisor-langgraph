"""
Tools do backend adaptadas para uso no LangGraph Server.
Baseado em backend/app/services/agent_tools.py
"""
import os
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from agent.mock_data import CARTEIRA, PERFIL_JOAO


@tool
def obter_perfil() -> Dict[str, Any]:
    """
    Busca o perfil completo do cliente, incluindo perfil de investidor.
    Use SEMPRE quando o cliente perguntar sobre seu perfil de investidor ou quando precisar saber o perfil para fazer análises.
    Retorna informações sobre nome, idade, profissão, perfil de investidor (conservador/moderado/arrojado) e outros dados do cliente.
    """
    perfil_data = PERFIL_JOAO if PERFIL_JOAO else {}
    return {
        'nome': perfil_data.get('nome', 'João'),
        'idade': perfil_data.get('idade', 38),
        'profissao': perfil_data.get('profissao', 'Profissional de Tecnologia'),
        'perfilInvestidor': perfil_data.get('perfilInvestidor', 'conservador'),
        'patrimonioInvestido': perfil_data.get('patrimonioInvestido', 0),
        'dinheiroParado': perfil_data.get('dinheiroParado', 0),
        'aporteMensal': perfil_data.get('aporteMensal', 0),
        'objetivo': perfil_data.get('objetivo', {}),
        'comportamento': perfil_data.get('comportamento', {})
    }


@tool
def obter_carteira() -> Dict[str, Any]:
    """
    Busca dados completos da carteira do cliente.
    Use APENAS quando o cliente perguntar especificamente sobre sua carteira atual, saldo, investimentos ou patrimônio.
    Retorna informações sobre total, distribuição percentual e investimentos.
    """
    carteira_data = CARTEIRA if CARTEIRA else {}
    return {
        'total': carteira_data.get('total', 0),
        'dinheiroParado': carteira_data.get('dinheiroParado', 0),
        'aporteMensal': carteira_data.get('aporteMensal', 0),
        'objetivo': carteira_data.get('objetivo', {}),
        'distribuicao': carteira_data.get('distribuicao', {}),
        'distribuicaoPercentual': carteira_data.get('distribuicaoPercentual', {}),
        'investimentos': carteira_data.get('investimentos', []),
        'adequacaoPerfil': carteira_data.get('adequacaoPerfil', {})
    }


@tool
def analisar_adequacao(carteira: Dict[str, Any], perfil: str) -> Dict[str, Any]:
    """
    Analisa se a carteira está adequada ao perfil do investidor.
    Use SEMPRE quando o cliente perguntar sobre adequação ao perfil, se a carteira está adequada, ou sobre problemas na carteira.
    Obtém a carteira automaticamente. Parâmetro: perfil (str: 'conservador', 'moderado', 'arrojado', padrão: 'conservador').
    
    Args:
        carteira: Dicionário com dados da carteira (obtido via obter_carteira)
        perfil: Perfil de investidor ('conservador', 'moderado', 'arrojado')
    
    Returns:
        Dict com score, problemas, recomendações e se está adequado
    """
    problemas = []
    recomendacoes = []
    score = 100
    
    # Análise de adequação para perfil conservador
    if perfil.lower() == 'conservador':
        distribuicao = carteira.get('distribuicaoPercentual', {})
        total = carteira.get('total', 0)
        dinheiro_parado = carteira.get('dinheiroParado', 0)
        total_carteira = total + dinheiro_parado
        
        # Verificar renda variável (deve ser 10-15% para conservador)
        renda_variavel_pct = distribuicao.get('rendaVariavel', 0)
        if renda_variavel_pct > 15:
            excesso = renda_variavel_pct - 15
            valor_excesso = (excesso / 100) * total_carteira
            problemas.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) acima do recomendado (10-15%)")
            score -= 20
            recomendacoes.append(f"Reduzir exposição a renda variável para 10-15% do patrimônio. Sugestão: realocar R$ {valor_excesso:,.2f} para renda fixa")
        
        # Verificar liquidez (deve ser 15-20% para conservador)
        liquidez_pct = distribuicao.get('liquidez', 0)
        if liquidez_pct < 15:
            deficit = 15 - liquidez_pct
            valor_deficit = (deficit / 100) * total_carteira
            problemas.append(f"Liquidez ({liquidez_pct:.1f}%) abaixo do ideal (15-20%)")
            score -= 15
            recomendacoes.append(f"Aumentar reserva de emergência para 15-20% do patrimônio. Sugestão: alocar R$ {valor_deficit:,.2f} do dinheiro parado em produtos de liquidez diária")
        
        # Verificar renda fixa (deve ser 70-85% para conservador)
        renda_fixa_pct = distribuicao.get('rendaFixa', 0)
        if renda_fixa_pct < 70:
            problemas.append(f"Renda fixa ({renda_fixa_pct:.1f}%) abaixo do ideal para perfil conservador (70-85%)")
            score -= 10
            recomendacoes.append("Aumentar exposição a renda fixa para melhor adequação ao perfil conservador")
    
    adequado = score >= 70
    
    return {
        'score': score,
        'problemas': problemas,
        'recomendacoes': recomendacoes,
        'adequado': adequado
    }


@tool
def analisar_alinhamento_objetivos(carteira: Dict[str, Any], perfil: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa se a carteira está alinhada com objetivos de curto, médio e longo prazo.
    Use SEMPRE quando o cliente perguntar sobre alinhamento com objetivos, se está alinhado com curto/médio/longo prazo, ou sobre adequação aos horizontes temporais.
    Obtém carteira e perfil automaticamente. Retorna análise detalhada por horizonte temporal.
    
    Args:
        carteira: Dicionário com dados da carteira
        perfil: Dicionário com dados do perfil do cliente
    
    Returns:
        Dict com análise de alinhamento para curto, médio e longo prazo
    """
    distribuicao = carteira.get('distribuicaoPercentual', {})
    total = carteira.get('total', 0)
    dinheiro_parado = carteira.get('dinheiroParado', 0)
    objetivo = carteira.get('objetivo', {})
    
    perfil_investidor = perfil.get('perfilInvestidor', 'conservador')
    objetivo_valor = objetivo.get('valor', 0) if isinstance(objetivo, dict) else 0
    objetivo_prazo = objetivo.get('prazo', 0) if isinstance(objetivo, dict) else 0
    
    total_carteira = total + dinheiro_parado
    liquidez_pct = distribuicao.get('liquidez', 0)
    renda_fixa_pct = distribuicao.get('rendaFixa', 0)
    renda_variavel_pct = distribuicao.get('rendaVariavel', 0)
    
    # Análise para CURTO PRAZO (até 3 anos)
    problemas_curto = []
    recomendacoes_curto = []
    alinhado_curto = True
    
    if liquidez_pct < 20:
        problemas_curto.append(f"Liquidez insuficiente ({liquidez_pct:.1f}%) para objetivos de curto prazo (recomendado: 20-30%)")
        alinhado_curto = False
        recomendacoes_curto.append(f"Aumentar liquidez para 20-30% do patrimônio para garantir acesso a recursos de curto prazo")
    
    if renda_variavel_pct > 10:
        problemas_curto.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) alta para objetivos de curto prazo (recomendado: até 10%)")
        alinhado_curto = False
        recomendacoes_curto.append("Reduzir exposição a renda variável para objetivos de curto prazo devido à volatilidade")
    
    # Análise para MÉDIO PRAZO (3 a 10 anos)
    problemas_medio = []
    recomendacoes_medio = []
    alinhado_medio = True
    
    if perfil_investidor == 'conservador':
        if renda_variavel_pct > 20:
            problemas_medio.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) acima do ideal para perfil conservador em médio prazo (recomendado: 10-20%)")
            alinhado_medio = False
            recomendacoes_medio.append("Ajustar alocação para médio prazo: manter 10-20% em renda variável e 70-80% em renda fixa")
    
    # Análise para LONGO PRAZO (acima de 10 anos)
    problemas_longo = []
    recomendacoes_longo = []
    alinhado_longo = True
    
    if perfil_investidor == 'conservador':
        if renda_variavel_pct > 15:
            problemas_longo.append(f"Exposição a renda variável ({renda_variavel_pct:.1f}%) acima do recomendado para perfil conservador mesmo em longo prazo (recomendado: 10-15%)")
            alinhado_longo = False
            recomendacoes_longo.append("Para longo prazo com perfil conservador, manter 10-15% em renda variável e 75-85% em renda fixa")
    
    if objetivo_valor > 0 and objetivo_prazo > 0:
        if objetivo_prazo <= 3:
            if not alinhado_curto:
                problemas_curto.append(f"Alocação atual pode não ser adequada para atingir objetivo de R$ {objetivo_valor:,.2f} em {objetivo_prazo} anos")
        elif objetivo_prazo <= 10:
            if not alinhado_medio:
                problemas_medio.append(f"Alocação atual pode não ser adequada para atingir objetivo de R$ {objetivo_valor:,.2f} em {objetivo_prazo} anos")
        else:
            if not alinhado_longo:
                problemas_longo.append(f"Alocação atual pode não ser adequada para atingir objetivo de R$ {objetivo_valor:,.2f} em {objetivo_prazo} anos")
    
    score_geral = 100
    if not alinhado_curto:
        score_geral -= 25
    if not alinhado_medio:
        score_geral -= 25
    if not alinhado_longo:
        score_geral -= 25
    
    return {
        'alinhado_curto_prazo': alinhado_curto,
        'alinhado_medio_prazo': alinhado_medio,
        'alinhado_longo_prazo': alinhado_longo,
        'problemas_curto': problemas_curto,
        'problemas_medio': problemas_medio,
        'problemas_longo': problemas_longo,
        'recomendacoes_curto': recomendacoes_curto,
        'recomendacoes_medio': recomendacoes_medio,
        'recomendacoes_longo': recomendacoes_longo,
        'score_geral': score_geral
    }


@tool
def analisar_diversificacao(carteira: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa a diversificação da carteira do cliente.
    Identifica concentrações excessivas e sugere melhorias.
    
    Args:
        carteira: Dicionário com dados da carteira
    
    Returns:
        Dict com score de diversificação, problemas, concentrações e recomendações
    """
    problemas = []
    recomendacoes = []
    score = 100
    
    investimentos = carteira.get('investimentos', [])
    total = carteira.get('total', 0)
    distribuicao = carteira.get('distribuicaoPercentual', {})
    
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
    
    # Verificar concentração excessiva por classe
    for classe, pct in concentracao_classe_pct.items():
        if pct > 80:
            problemas.append(f"Concentração excessiva em {classe} ({pct:.1f}%) - acima do recomendado (máximo 80%)")
            score -= 20
            recomendacoes.append(f"Diversificar reduzindo exposição a {classe} e distribuindo para outras classes")
    
    # Verificar concentração excessiva por ativo
    for ativo, pct in concentracao_ativo.items():
        if pct > 30:
            problemas.append(f"Concentração excessiva no ativo {ativo} ({pct:.1f}%) - acima do recomendado (máximo 30%)")
            score -= 15
            recomendacoes.append(f"Reduzir exposição ao ativo {ativo} e diversificar em outros investimentos")
    
    # Verificar número de ativos
    num_ativos = len(investimentos)
    if num_ativos < 3:
        problemas.append(f"Poucos investimentos ({num_ativos}) - recomendado ter pelo menos 3-5 ativos diferentes")
        score -= 10
        recomendacoes.append("Aumentar número de investimentos para melhor diversificação")
    
    adequado = score >= 70
    
    return {
        'score_diversificacao': score,
        'problemas': problemas,
        'concentracao_por_classe': concentracao_classe_pct,
        'concentracao_por_ativo': concentracao_ativo,
        'recomendacoes': recomendacoes,
        'adequado': adequado
    }


@tool
def recomendar_rebalanceamento(carteira: Dict[str, Any], perfil: str) -> Dict[str, Any]:
    """
    Gera recomendações específicas de rebalanceamento da carteira.
    
    Args:
        carteira: Dicionário com dados da carteira
        perfil: Perfil de investidor ('conservador', 'moderado', 'arrojado')
    
    Returns:
        Dict com recomendações de rebalanceamento
    """
    # Analisar adequação primeiro
    adequacao_result = analisar_adequacao(carteira, perfil)
    adequacao_dict = adequacao_result if isinstance(adequacao_result, dict) else adequacao_result
    
    necessario = not adequacao_dict.get('adequado', True)
    ajustes_sugeridos = []
    
    if necessario:
        distribuicao = carteira.get('distribuicaoPercentual', {})
        total = carteira.get('total', 0)
        dinheiro_parado = carteira.get('dinheiroParado', 0)
        total_carteira = total + dinheiro_parado
        
        renda_variavel_pct = distribuicao.get('rendaVariavel', 0)
        liquidez_pct = distribuicao.get('liquidez', 0)
        renda_fixa_pct = distribuicao.get('rendaFixa', 0)
        
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
    
    return {
        'necessario': necessario,
        'ajustes_sugeridos': ajustes_sugeridos,
        'justificativa': justificativa,
        'impacto_esperado': impacto_esperado
    }


@tool
def calcular_projecao(
    valor_atual: Optional[float] = None,
    aporte_mensal: Optional[float] = None,
    prazo_anos: Optional[int] = None,
    rentabilidade_anual: float = 0.10,
    carteira: Optional[Dict[str, Any]] = None,
    perfil: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calcula projeção de investimento considerando aportes mensais e rentabilidade.
    Usa juros compostos para cálculo.
    
    Aceita dois formatos de entrada:
    1. Valores numéricos: valor_atual (float), aporte_mensal (float), prazo_anos (int)
    2. Dicionários: carteira (dict), perfil (dict) - extrai valores automaticamente
    
    Args:
        valor_atual: Valor atual investido (opcional se fornecer carteira)
        aporte_mensal: Aporte mensal (opcional se fornecer carteira/perfil)
        prazo_anos: Prazo em anos (opcional se fornecer perfil/carteira)
        rentabilidade_anual: Rentabilidade anual esperada (padrão: 10%)
        carteira: Dicionário com dados da carteira (opcional)
        perfil: Dicionário com dados do perfil (opcional)
    
    Returns:
        Dict com projeção de investimento
    """
    # Extrair valores de carteira/perfil se não fornecidos
    if carteira is not None and valor_atual is None:
        valor_atual = carteira.get('total', 0.0)
        if valor_atual == 0:
            valor_atual = carteira.get('patrimonioInvestido', 0.0)
    
    if aporte_mensal is None:
        if carteira and isinstance(carteira, dict):
            aporte_mensal = carteira.get('aporteMensal', 0.0)
        if (aporte_mensal is None or aporte_mensal == 0) and perfil and isinstance(perfil, dict):
            aporte_mensal = perfil.get('aporteMensal', 0.0)
    
    if prazo_anos is None:
        objetivo = None
        if perfil and isinstance(perfil, dict):
            objetivo = perfil.get('objetivo', {})
        if (not objetivo or not isinstance(objetivo, dict)) and carteira and isinstance(carteira, dict):
            objetivo = carteira.get('objetivo', {})
        
        if objetivo and isinstance(objetivo, dict):
            prazo_anos = objetivo.get('prazo', 5)
        else:
            prazo_anos = 5
    
    # Valores padrão
    if valor_atual is None:
        valor_atual = 0.0
    if aporte_mensal is None:
        aporte_mensal = 0.0
    if prazo_anos is None:
        prazo_anos = 5
    
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
    
    # Extrair objetivo
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
    
    return {
        'valor_atual': valor_atual,
        'valor_projetado': valor_futuro,
        'aporte_mensal': aporte_mensal,
        'prazo_anos': prazo_anos,
        'viabilidade': viabilidade,
        'observacoes': observacoes
    }


@tool
def buscar_oportunidades(perfil: str, problemas: List[str]) -> List[Dict[str, Any]]:
    """
    Busca oportunidades de investimento adequadas ao perfil e problemas identificados.
    
    Args:
        perfil: Perfil de investidor ('conservador', 'moderado', 'arrojado')
        problemas: Lista de problemas identificados na carteira
    
    Returns:
        Lista de oportunidades de investimento
    """
    oportunidades = []
    
    if perfil.lower() == 'conservador':
        if any('liquidez' in p.lower() for p in problemas):
            oportunidades.append({
                'nome': 'CDB Liquidez Diária',
                'tipo': 'CDB',
                'adequacao_perfil': 'Alta',
                'rentabilidade': '100% CDI',
                'risco': 'Baixo',
                'justificativa': 'Produto adequado para aumentar liquidez mantendo rentabilidade'
            })
            
            oportunidades.append({
                'nome': 'Tesouro Selic',
                'tipo': 'Tesouro Direto',
                'adequacao_perfil': 'Alta',
                'rentabilidade': 'SELIC',
                'risco': 'Baixíssimo',
                'justificativa': 'Liquidez diária com segurança do governo federal'
            })
        
        if any('renda variável' in p.lower() for p in problemas):
            oportunidades.append({
                'nome': 'CDB 110% CDI 2 anos',
                'tipo': 'CDB',
                'adequacao_perfil': 'Alta',
                'rentabilidade': '110% CDI',
                'risco': 'Baixo',
                'justificativa': 'Alternativa conservadora para substituir parte da renda variável'
            })
            
            oportunidades.append({
                'nome': 'LCI 95% CDI 3 anos',
                'tipo': 'LCI',
                'adequacao_perfil': 'Alta',
                'rentabilidade': '95% CDI',
                'risco': 'Baixo',
                'justificativa': 'Isenção de IR e IOF, adequado para perfil conservador'
            })
    
    return oportunidades
