"""
Script de diagnóstico completo para conexão LangSmith Studio
Verifica todos os aspectos: servidor, CORS, endpoints, porta, etc.
"""
import requests
import json
import sys
import socket

BASE_URL = "http://127.0.0.1:8555"
PORT = 8555

def check_port_open(port):
    """Verifica se a porta está aberta"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def test_cors_preflight():
    """Testa CORS preflight como o Studio faria"""
    try:
        response = requests.options(
            f"{BASE_URL}/assistants",
            headers={
                "Origin": "https://smith.langchain.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        return response.status_code == 200, cors_headers, response.status_code
    except Exception as e:
        return False, {}, str(e)

def test_endpoints():
    """Testa todos os endpoints críticos"""
    endpoints = [
        ("GET", "/", "Endpoint raiz"),
        ("POST", "/assistants/search", "Busca assistentes", {"limit": 10}),
        ("GET", "/assistants", "Lista assistentes"),
        ("GET", "/threads", "Lista threads"),
    ]
    
    results = {}
    for endpoint in endpoints:
        method = endpoint[0]
        path = endpoint[1]
        desc = endpoint[2]
        data = endpoint[3] if len(endpoint) > 3 else None
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{path}", timeout=10)
            elif method == "POST":
                response = requests.post(
                    f"{BASE_URL}{path}",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            
            results[path] = {
                "status": response.status_code,
                "ok": response.status_code == 200,
                "description": desc
            }
        except Exception as e:
            results[path] = {
                "status": "ERROR",
                "ok": False,
                "error": str(e),
                "description": desc
            }
    
    return results

def main():
    """Executa diagnóstico completo"""
    print("=" * 70)
    print("Diagnóstico de Conexão - LangSmith Studio")
    print("=" * 70)
    
    issues = []
    warnings = []
    
    # 1. Verificar se porta está aberta
    print("\n[1] Verificando se porta 8555 está aberta...")
    if check_port_open(PORT):
        print(f"   [OK] Porta {PORT} está aberta")
    else:
        print(f"   [ERRO] Porta {PORT} não está aberta")
        issues.append(f"Porta {PORT} não está acessível. Inicie o servidor com: langgraph dev --port 8555")
    
    # 2. Verificar se servidor responde
    print("\n[2] Verificando se servidor responde...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"   [OK] Servidor respondendo (Status {response.status_code})")
        else:
            print(f"   [AVISO] Servidor respondeu com status {response.status_code}")
            warnings.append(f"Servidor retornou status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"   [ERRO] Não foi possível conectar ao servidor")
        issues.append(f"Servidor não está rodando em {BASE_URL}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        issues.append(f"Erro ao conectar: {e}")
    
    # 3. Testar CORS
    print("\n[3] Testando CORS (preflight)...")
    cors_ok, cors_headers, status = test_cors_preflight()
    if cors_ok:
        print(f"   [OK] CORS preflight funcionando (Status {status})")
        print(f"   Access-Control-Allow-Origin: {cors_headers.get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')}")
        print(f"   Access-Control-Allow-Methods: {cors_headers.get('Access-Control-Allow-Methods', 'NÃO ENCONTRADO')}")
        
        if cors_headers.get('Access-Control-Allow-Origin') != 'https://smith.langchain.com':
            warnings.append("CORS pode não estar configurado corretamente para LangSmith Studio")
    else:
        print(f"   [ERRO] CORS preflight falhou")
        issues.append("CORS não está configurado corretamente")
    
    # 4. Testar endpoints
    print("\n[4] Testando endpoints críticos...")
    endpoint_results = test_endpoints()
    for path, result in endpoint_results.items():
        if result["ok"]:
            print(f"   [OK] {result['description']} ({path}) - Status {result['status']}")
        else:
            error_msg = result.get('error', f"Status {result['status']}")
            print(f"   [ERRO] {result['description']} ({path}) - {error_msg}")
            issues.append(f"Endpoint {path} não está funcionando: {error_msg}")
    
    # 5. Verificar formato de resposta
    print("\n[5] Verificando formato de resposta /assistants/search...")
    try:
        response = requests.post(
            f"{BASE_URL}/assistants/search",
            json={"limit": 10},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                assistant = data[0]
                required_fields = ['assistant_id', 'graph_id', 'name']
                missing = [f for f in required_fields if f not in assistant]
                if not missing:
                    print(f"   [OK] Formato de resposta correto")
                else:
                    print(f"   [AVISO] Campos faltando: {missing}")
                    warnings.append(f"Formato de resposta pode estar incompleto: faltam {missing}")
            else:
                print(f"   [AVISO] Resposta não é uma lista ou está vazia")
                warnings.append("Formato de resposta pode estar incorreto")
    except Exception as e:
        print(f"   [ERRO] {e}")
        issues.append(f"Erro ao verificar formato: {e}")
    
    # Resumo
    print("\n" + "=" * 70)
    print("Resumo do Diagnóstico")
    print("=" * 70)
    
    if not issues:
        print("\n[OK] Nenhum problema crítico encontrado!")
        print("\nPara conectar no LangSmith Studio:")
        print(f"1. Base URL: {BASE_URL}")
        print("2. Em Advanced Settings > Allowed Origins, adicione:")
        print(f"   - {BASE_URL}")
        print(f"   - http://localhost:8555")
        
        if warnings:
            print("\n[AVISOS]:")
            for warning in warnings:
                print(f"  - {warning}")
    else:
        print("\n[ERROS ENCONTRADOS]:")
        for issue in issues:
            print(f"  - {issue}")
        
        print("\n[Soluções]:")
        print("1. Inicie o servidor: cd langgraph-app && langgraph dev --port 8555")
        print("2. Verifique se a porta 8555 está livre")
        print("3. Verifique os logs do servidor para erros")
        sys.exit(1)

if __name__ == "__main__":
    main()
