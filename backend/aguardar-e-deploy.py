#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aguardar processamento da versão e fazer deploy automaticamente
"""

import subprocess
import time
import json
import sys

ENV_NAME = "Alphaadvisor-v4-env"
REGION = "us-east-1"
APP_NAME = "alphaadvisor-backend"
VERSION_LABEL = "app-20260109_152054"

def run_aws_command(cmd):
    """Executa comando AWS CLI e retorna resultado"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def get_version_status():
    """Obtém status da versão"""
    cmd = f'aws elasticbeanstalk describe-application-versions --application-name {APP_NAME} --version-labels {VERSION_LABEL} --region {REGION} --query ApplicationVersions[0].Status --output text'
    output, code = run_aws_command(cmd)
    return output if code == 0 else None

def deploy_version():
    """Faz deploy da versão"""
    cmd = f'aws elasticbeanstalk update-environment --application-name {APP_NAME} --environment-name {ENV_NAME} --version-label {VERSION_LABEL} --region {REGION}'
    output, code = run_aws_command(cmd)
    return output, code

def main():
    print("=" * 60)
    print("Aguardando Processamento e Deploy")
    print("=" * 60)
    print()
    print(f"Versão: {VERSION_LABEL}")
    print()
    
    # Aguardar processamento
    print("Aguardando versão ser processada...")
    max_wait = 120
    interval = 5
    waited = 0
    
    while waited < max_wait:
        status = get_version_status()
        
        if status == "PROCESSED":
            print()
            print("OK: Versao processada!")
            break
        
        print(f"Aguardando... ({waited}/{max_wait} segundos) - Status: {status}")
        time.sleep(interval)
        waited += interval
    
    if waited >= max_wait:
        print()
        print("AVISO: Timeout aguardando processamento")
        print(f"Status atual: {get_version_status()}")
        print("Tentando fazer deploy mesmo assim...")
    
    # Fazer deploy
    print()
    print(f"Fazendo deploy da versão {VERSION_LABEL}...")
    output, code = deploy_version()
    
    if code == 0:
        print()
        print("OK: Deploy iniciado!")
        print()
        print("O deploy pode levar 5-10 minutos para completar.")
        print()
        print("Para monitorar:")
        print(f"  aws elasticbeanstalk describe-environments --environment-names {ENV_NAME} --region {REGION} --query Environments[0].[Status,Health,VersionLabel] --output table")
    else:
        print()
        print("ERRO: Falha ao fazer deploy")
        print(output)
        print()
        print("A versao pode ainda estar sendo processada. Tente novamente em alguns minutos ou via AWS Console")
    
    print()

if __name__ == "__main__":
    main()

