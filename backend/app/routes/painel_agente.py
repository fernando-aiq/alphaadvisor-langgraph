"""
Rotas para o Painel do Agente - Analytics e Compliance
Fornece endpoints para visualizar interações, redirecionamentos e compliance
"""
import json
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request
from app.services.traceability_service import TraceabilityService
from datetime import datetime, timedelta

painel_agente_bp = Blueprint('painel_agente', __name__)
traceability = TraceabilityService()

@painel_agente_bp.route('/api/painel-agente/summary', methods=['GET'])
def get_summary():
    """Retorna resumo geral do painel"""
    client_id = request.args.get('client_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Se não especificado, usar últimos 30 dias
    if not end_date:
        end_date = datetime.utcnow().isoformat()
    if not start_date:
        start_dt = datetime.utcnow() - timedelta(days=30)
        start_date = start_dt.isoformat()
    
    stats = traceability.get_aggregated_stats(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'summary': stats,
        'period': {
            'start_date': start_date,
            'end_date': end_date
        }
    }), 200

@painel_agente_bp.route('/api/painel-agente/traces', methods=['GET'])
def list_traces_panel():
    """Lista traces com filtros para o painel"""
    limit = request.args.get('limit', 50, type=int)
    client_id = request.args.get('client_id')
    status = request.args.get('status')
    intent = request.args.get('intent')
    route = request.args.get('route')
    has_handoff = request.args.get('has_handoff')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Converter has_handoff string para bool
    has_handoff_bool = None
    if has_handoff:
        has_handoff_bool = has_handoff.lower() == 'true'
    
    traces = traceability.list_traces_filtered(
        limit=limit,
        client_id=client_id,
        status=status,
        intent=intent,
        route=route,
        has_handoff=has_handoff_bool,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'traces': traces,
        'total': len(traces)
    }), 200

@painel_agente_bp.route('/api/painel-agente/handoffs', methods=['GET'])
def list_handoffs():
    """Lista redirecionamentos (handoffs)"""
    limit = request.args.get('limit', 50, type=int)
    client_id = request.args.get('client_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    handoffs = traceability.get_handoffs(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return jsonify({
        'handoffs': handoffs,
        'total': len(handoffs)
    }), 200

@painel_agente_bp.route('/api/painel-agente/compliance/list', methods=['GET'])
def list_compliance():
    """Lista traces com dados de compliance para a tabela da página Compliance"""
    limit = request.args.get('limit', 100, type=int)
    client_id = request.args.get('client_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    traces = traceability.list_traces_filtered(
        limit=limit,
        client_id=client_id,
        start_date=start_date,
        end_date=end_date
    )

    compliance_list = []
    for trace_info in traces:
        compliance = traceability.get_compliance_info(trace_info['trace_id'])
        if compliance:
            compliance_list.append({
                **trace_info,
                'trace_age_days': compliance.get('trace_age_days'),
                'has_pii_masked': compliance.get('has_pii_masked'),
                'lgpd_base_legal': compliance.get('lgpd', {}).get('base_legal'),
                'lgpd_consent': compliance.get('lgpd', {}).get('consent'),
                'retention_days': compliance.get('retention_days'),
                'access_events_count': compliance.get('audit', {}).get('access_events', 0),
            })

    return jsonify({
        'compliance_list': compliance_list,
        'total': len(compliance_list)
    }), 200


@painel_agente_bp.route('/api/painel-agente/compliance/summary', methods=['GET'])
def compliance_summary():
    """Retorna totais/counts de compliance para os cards da página"""
    client_id = request.args.get('client_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    traces = traceability.list_traces_filtered(
        limit=10000,
        client_id=client_id,
        start_date=start_date,
        end_date=end_date
    )

    total = len(traces)
    with_consent = 0
    with_pii_masked = 0
    retention_days_default = 90

    for trace_info in traces:
        compliance = traceability.get_compliance_info(trace_info['trace_id'])
        if compliance:
            if compliance.get('lgpd', {}).get('consent'):
                with_consent += 1
            if compliance.get('has_pii_masked'):
                with_pii_masked += 1

    return jsonify({
        'total_traces': total,
        'with_consent': with_consent,
        'with_pii_masked': with_pii_masked,
        'retention_days': retention_days_default
    }), 200


# Políticas fixas de compliance (fonte única para backend e agente de compliance)
COMPLIANCE_POLICIES_FIXED = [
    {
        "id": "lgpd",
        "title": "LGPD",
        "description": "Todos os traces são armazenados com base legal e consentimento quando aplicável. Base legal e status de consentimento devem ser verificados por interação."
    },
    {
        "id": "cvm",
        "title": "CVM – Regras do assessor",
        "description": "Conformidade com as regras da CVM para assessoria de investimentos. Recomendações e explicações devem ser registradas para auditoria."
    },
    {
        "id": "auditoria",
        "title": "Auditoria",
        "description": "Trilha completa de eventos e acessos é mantida para cada interação. Logs de acesso disponíveis por trace."
    },
    {
        "id": "pii",
        "title": "Mascaramento de PII",
        "description": "Dados sensíveis (PII) são mascarados automaticamente quando necessário. Verificar status de mascaramento por trace."
    },
    {
        "id": "retencao",
        "title": "Retenção",
        "description": "Traces são mantidos por 90 dias (configurável) para fins de auditoria e compliance."
    },
]


@painel_agente_bp.route('/api/painel-agente/compliance/policies', methods=['GET'])
def get_compliance_policies():
    """
    Retorna políticas fixas e/ou regras customizadas de compliance.
    Query opcional: id (lgpd, cvm, auditoria, pii, retencao, rules).
    Sem id: retorna policies + rules completos.
    """
    policy_id = request.args.get('id', '').strip().lower()
    if policy_id == 'rules':
        data = _load_compliance_rules()
        return jsonify({"rules": data.get("rules", [])}), 200
    if policy_id:
        for p in COMPLIANCE_POLICIES_FIXED:
            if p["id"] == policy_id:
                return jsonify({"policy": p}), 200
        return jsonify({"error": f"Política não encontrada: {policy_id}"}), 404
    # Sem id: retornar todas as políticas fixas + regras
    data = _load_compliance_rules()
    return jsonify({
        "policies": COMPLIANCE_POLICIES_FIXED,
        "rules": data.get("rules", [])
    }), 200


def _compliance_rules_path():
    """Caminho do arquivo de regras de compliance (data/compliance_rules.json)"""
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        base_dir = Path("/tmp")
        data_dir = base_dir / "alphaadvisor_data"
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "compliance_rules.json"


def _load_compliance_rules():
    """Carrega regras de compliance do arquivo JSON"""
    path = _compliance_rules_path()
    if not path.exists():
        return {"rules": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"rules": []}


def _save_compliance_rules(data):
    """Salva regras de compliance no arquivo JSON"""
    path = _compliance_rules_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@painel_agente_bp.route('/api/painel-agente/compliance/rules', methods=['GET'])
def list_compliance_rules():
    """Lista regras de compliance customizadas"""
    data = _load_compliance_rules()
    return jsonify({"rules": data.get("rules", [])}), 200


@painel_agente_bp.route('/api/painel-agente/compliance/rules', methods=['POST'])
def create_compliance_rule():
    """Cria uma nova regra de compliance"""
    body = request.get_json() or {}
    title = (body.get("title") or "").strip()
    description = (body.get("description") or "").strip()
    category = (body.get("category") or "").strip() or None
    if not title:
        return jsonify({"error": "title é obrigatório"}), 400

    data = _load_compliance_rules()
    rules = data.get("rules", [])
    new_rule = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "category": category,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    rules.append(new_rule)
    data["rules"] = rules
    _save_compliance_rules(data)
    return jsonify(new_rule), 201


@painel_agente_bp.route('/api/painel-agente/compliance/<trace_id>', methods=['GET'])
def get_compliance_info(trace_id):
    """Retorna informações de compliance para um trace"""
    compliance = traceability.get_compliance_info(trace_id)
    
    if not compliance:
        return jsonify({'error': 'Trace não encontrado'}), 404
    
    return jsonify(compliance), 200

@painel_agente_bp.route('/api/painel-agente/compliance/export', methods=['GET'])
def export_compliance_data():
    """Exporta dados de compliance para auditoria (CSV/JSON)"""
    client_id = request.args.get('client_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_type = request.args.get('format', 'json')  # json ou csv
    
    # Buscar todos os traces no período
    traces = traceability.list_traces_filtered(
        limit=10000,
        client_id=client_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Coletar dados de compliance
    compliance_data = []
    for trace_info in traces:
        compliance = traceability.get_compliance_info(trace_info['trace_id'])
        if compliance:
            compliance_data.append({
                'trace_id': trace_info['trace_id'],
                'timestamp': trace_info.get('timestamp'),
                'client_id': trace_info.get('client_id'),
                'client_name': trace_info.get('client_name'),
                'intent': trace_info.get('intent'),
                'route': trace_info.get('route'),
                'trace_age_days': compliance.get('trace_age_days'),
                'has_pii_masked': compliance.get('has_pii_masked'),
                'lgpd_base_legal': compliance.get('lgpd', {}).get('base_legal'),
                'lgpd_consent': compliance.get('lgpd', {}).get('consent'),
                'retention_days': compliance.get('retention_days'),
                'access_events_count': compliance.get('audit', {}).get('access_events', 0)
            })
    
    if format_type == 'csv':
        # Gerar CSV
        import io
        output = io.StringIO()
        if compliance_data:
            headers = compliance_data[0].keys()
            output.write(','.join(headers) + '\n')
            for row in compliance_data:
                values = [str(v).replace(',', ';') for v in row.values()]
                output.write(','.join(values) + '\n')
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=compliance_export.csv'}
        )
    else:
        # JSON
        return jsonify({
            'compliance_data': compliance_data,
            'total': len(compliance_data),
            'export_date': datetime.utcnow().isoformat()
        }), 200

@painel_agente_bp.route('/api/painel-agente/clients', methods=['GET'])
def list_clients():
    """Lista clientes únicos que têm traces"""
    all_traces = traceability.list_traces_filtered(limit=10000)
    
    clients = {}
    for trace in all_traces:
        client_id = trace.get('client_id')
        client_name = trace.get('client_name')
        if client_id:
            if client_id not in clients:
                clients[client_id] = {
                    'client_id': client_id,
                    'client_name': client_name or f'Cliente {client_id}',
                    'traces_count': 0
                }
            clients[client_id]['traces_count'] += 1
    
    clients_list = list(clients.values())
    clients_list.sort(key=lambda x: x['traces_count'], reverse=True)
    
    return jsonify({
        'clients': clients_list,
        'total': len(clients_list)
    }), 200

