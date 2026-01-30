"""
API de regulacoes: normas completas (CVM, Lei Mercado de Capitais, LGPD, ANBIMA)
para o sistema consultar (agente, painel, explainability).
"""
import logging

from flask import Blueprint, jsonify

from app.services.regulacoes_service import get_regulacao as service_get_regulacao, list_regulacoes as service_list_regulacoes

logger = logging.getLogger(__name__)

regulacoes_bp = Blueprint("regulacoes", __name__)


@regulacoes_bp.route("/api/regulacoes", methods=["GET"])
def list_regulacoes():
    """
    Lista todas as regulacoes: id, titulo, norma, fonte_url, vigencia, resumo.
    Não inclui texto_completo.
    """
    result = service_list_regulacoes()
    return jsonify({"regulacoes": result}), 200


@regulacoes_bp.route("/api/regulacoes/<id>", methods=["GET"])
def get_regulacao(id):
    """
    Retorna uma regulacao pelo id, com todos os campos incluindo texto_completo.
    O id pode ser o valor do campo id no JSON ou o nome do arquivo sem .json.
    """
    if not (id or "").strip():
        return jsonify({"error": "id é obrigatório"}), 400
    data = service_get_regulacao(id)
    if data is None:
        return jsonify({"error": f"Regulacao não encontrada: {id}"}), 404
    return jsonify(data), 200
