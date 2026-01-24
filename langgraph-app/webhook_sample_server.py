"""
Servidor webhook sample para receber notificações de cálculos executados.
Execute este servidor para testar o webhook de cálculos.

Uso:
    python webhook_sample_server.py

O servidor ficará escutando em http://localhost:8888/webhook/calculation
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# Armazenar histórico de cálculos (em produção, use banco de dados)
calculation_history = []


@app.route('/webhook/calculation', methods=['POST'])
def receive_calculation():
    """
    Endpoint que recebe webhooks de cálculos executados.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        # Validar estrutura do payload
        if data.get("event") != "calculation_executed":
            return jsonify({"error": "Invalid event type"}), 400
        
        calculation_data = data.get("data", {})
        
        # Registrar no histórico
        calculation_record = {
            "received_at": datetime.now().isoformat(),
            "event": data.get("event"),
            "timestamp": data.get("timestamp"),
            "calculation": calculation_data,
        }
        calculation_history.append(calculation_record)
        
        # Log no console
        print("\n" + "=" * 60)
        print("WEBHOOK RECEBIDO - Cálculo Executado")
        print("=" * 60)
        print(f"Timestamp: {calculation_record['received_at']}")
        print(f"Evento: {calculation_record['event']}")
        print(f"Expressão: {calculation_data.get('expression', 'N/A')}")
        print(f"Resultado: {calculation_data.get('result', 'N/A')}")
        print(f"Mensagem do usuário: {calculation_data.get('user_message', 'N/A')}")
        print("=" * 60 + "\n")
        
        # Retornar sucesso
        return jsonify({
            "status": "success",
            "message": "Calculation webhook received",
            "calculation_id": len(calculation_history)
        }), 200
        
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/webhook/calculation/history', methods=['GET'])
def get_calculation_history():
    """
    Endpoint para visualizar histórico de cálculos recebidos.
    """
    return jsonify({
        "total": len(calculation_history),
        "calculations": calculation_history
    }), 200


@app.route('/webhook/calculation/clear', methods=['POST'])
def clear_history():
    """
    Endpoint para limpar histórico (útil para testes).
    """
    global calculation_history
    calculation_history = []
    return jsonify({"status": "success", "message": "History cleared"}), 200


@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint de health check.
    """
    return jsonify({
        "status": "healthy",
        "service": "Calculation Webhook Sample Server",
        "total_calculations_received": len(calculation_history)
    }), 200


if __name__ == '__main__':
    print("=" * 60)
    print("Servidor Webhook Sample - Cálculos")
    print("=" * 60)
    print()
    print("Servidor iniciado em: http://localhost:8888")
    print("Endpoint do webhook: http://localhost:8888/webhook/calculation")
    print("Histórico: http://localhost:8888/webhook/calculation/history")
    print("Health check: http://localhost:8888/health")
    print()
    print("Para usar, configure no .env:")
    print("CALCULATION_WEBHOOK_URL=http://localhost:8888/webhook/calculation")
    print()
    print("Pressione Ctrl+C para parar o servidor")
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=8888, debug=True)
