"""
Serviço de Explicability para gerar explicações claras das recomendações do agente.
Inclui racional, dados utilizados, regras aplicadas e conformidade CVM.
"""
from typing import Dict, List, Any
from pydantic import BaseModel

class Explanation(BaseModel):
    """Modelo de explicação estruturada"""
    rationale: str
    data_used: List[str]
    rules_applied: List[str]
    alternatives: List[Dict[str, Any]]
    risks: List[Dict[str, str]]
    compliance: Dict[str, Any]

class ExplainabilityService:
    def __init__(self):
        pass
    
    def generate_explanation(self, recommendation: Dict, 
                            analysis_data: Dict,
                            rules_applied: List[str],
                            alternatives: List[Dict],
                            risks: List[Dict]) -> Explanation:
        """
        Gera explicação completa para uma recomendação
        
        Args:
            recommendation: Recomendação gerada pelo agente
            analysis_data: Dados utilizados na análise
            rules_applied: Regras de compliance aplicadas
            alternatives: Alternativas consideradas
            risks: Riscos identificados
        
        Returns:
            Explanation: Explicação estruturada
        """
        rationale = self._build_rationale(recommendation, analysis_data)
        data_used = self._extract_data_sources(analysis_data)
        compliance = self._check_compliance(recommendation, rules_applied)
        
        return Explanation(
            rationale=rationale,
            data_used=data_used,
            rules_applied=rules_applied,
            alternatives=alternatives,
            risks=risks,
            compliance=compliance
        )
    
    def _build_rationale(self, recommendation: Dict, analysis_data: Dict) -> str:
        """Constrói o racional da recomendação"""
        rationale_parts = []
        
        if 'tipo' in recommendation:
            rationale_parts.append(f"Recomendação: {recommendation.get('tipo', 'N/A')}")
        
        if 'motivo' in recommendation:
            rationale_parts.append(f"Motivo: {recommendation['motivo']}")
        
        if 'perfil' in analysis_data:
            rationale_parts.append(f"Baseado no perfil {analysis_data['perfil']} do cliente")
        
        if 'carteira' in analysis_data:
            carteira = analysis_data['carteira']
            if 'problemas' in carteira:
                rationale_parts.append(f"Problemas identificados: {', '.join(carteira['problemas'])}")
        
        return ". ".join(rationale_parts) if rationale_parts else "Recomendação baseada em análise da carteira e perfil do cliente."
    
    def _extract_data_sources(self, analysis_data: Dict) -> List[str]:
        """Extrai fontes de dados utilizadas"""
        sources = []
        
        if 'carteira' in analysis_data:
            sources.append("Carteira atual do cliente")
        
        if 'perfil' in analysis_data:
            sources.append("Perfil de investidor")
        
        if 'objetivo' in analysis_data:
            sources.append("Objetivos financeiros")
        
        if 'historico' in analysis_data:
            sources.append("Histórico de investimentos")
        
        return sources
    
    def _check_compliance(self, recommendation: Dict, rules_applied: List[str]) -> Dict:
        """Verifica conformidade com regras CVM"""
        return {
            'cvm_539': 'adequacao_verificada' in rules_applied,
            'cvm_30': 'suitability_verificada' in rules_applied,
            'regras_aplicadas': rules_applied,
            'conformidade': len(rules_applied) > 0
        }

