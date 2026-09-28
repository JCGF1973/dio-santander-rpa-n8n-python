"""
RPA de Análise de Investimentos por Perfil de Investidor
Bootcamp Santander & DIO - Automação com n8n e Python
"""

import sys
import json
import os
import csv
import urllib.request
from datetime import datetime

# Garante suporte UTF-8 no stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

INPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "input")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "output")

def ensure_directories():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_investidores():
    csv_file = os.path.join(INPUT_DIR, "investidores.csv")
    investidores = []
    
    if os.path.exists(csv_file):
        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                investidores.append({
                    "id_cliente": int(row["id_cliente"]),
                    "nome": row["nome"],
                    "email": row["email"],
                    "perfil": row["perfil"],
                    "ativo_interesse": row["ativo_interesse"],
                    "gatilho_variacao_max": float(row["gatilho_variacao_max"])
                })
    else:
        investidores = [
            {"id_cliente": 1, "nome": "Carlos Silva", "email": "carlos.silva@email.com", "perfil": "Conservador", "ativo_interesse": "USD", "gatilho_variacao_max": -0.50},
            {"id_cliente": 2, "nome": "Mariana Souza", "email": "mariana.souza@email.com", "perfil": "Moderado", "ativo_interesse": "EUR", "gatilho_variacao_max": -0.80},
            {"id_cliente": 3, "nome": "Lucas Mendes", "email": "lucas.mendes@email.com", "perfil": "Agressivo", "ativo_interesse": "BTC", "gatilho_variacao_max": -1.50}
        ]
    return investidores

def fetch_market_data():
    url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 Santander-RPA-Investment-Agent"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        content = response.read().decode("utf-8")
        return json.loads(content)

def analyze_opportunities(investidores, raw_market):
    recomendacoes = []
    
    market_map = {
        "USD": raw_market.get("USDBRL", {}),
        "EUR": raw_market.get("EURBRL", {}),
        "BTC": raw_market.get("BTCBRL", {})
    }
    
    for inv in investidores:
        ativo = inv["ativo_interesse"]
        market_info = market_map.get(ativo, {})
        
        cotacao = float(market_info.get("bid", 0.0))
        variacao_pct = float(market_info.get("pctChange", 0.0))
        maxima = float(market_info.get("high", 0.0))
        minima = float(market_info.get("low", 0.0))
        
        oportunidade_compra = variacao_pct <= inv["gatilho_variacao_max"] or variacao_pct <= 0
        
        if oportunidade_compra:
            status_acao = "HORA DE INVESTIR"
            motivo = f"O ativo {ativo} teve variacao de {variacao_pct:.2f}% (abaixo do gatilho de {inv['gatilho_variacao_max']}%)."
        else:
            status_acao = "AGUARDAR"
            motivo = f"O ativo {ativo} subiu {variacao_pct:.2f}%. Recomendamos aguardar correcao."
            
        corpo_email = (
            f"Ola {inv['nome']},\n\n"
            f"Analise de Mercado para o seu Perfil: {inv['perfil']}\n"
            f"Ativo de Interesse: {ativo} | Cotacao Atual: R$ {cotacao:,.2f}\n"
            f"Variacao Diaria: {variacao_pct:.2f}% (Min: R$ {minima:,.2f} | Max: R$ {maxima:,.2f})\n\n"
            f"Recomendacao: {status_acao}\n"
            f"Motivo: {motivo}\n\n"
            f"Atenciosamente,\nEquipe Santander Automacao & Investimentos"
        )
        
        recomendacoes.append({
            "id_cliente": inv["id_cliente"],
            "nome": inv["nome"],
            "email": inv["email"],
            "perfil": inv["perfil"],
            "ativo": ativo,
            "cotacao_atual": round(cotacao, 4),
            "variacao_pct": round(variacao_pct, 2),
            "oportunidade_compra": oportunidade_compra,
            "recomendacao": status_acao,
            "corpo_email": corpo_email
        })
        
    return recomendacoes

def save_outputs(recomendacoes):
    ensure_directories()
    csv_path = os.path.join(OUTPUT_DIR, "relatorio_recomendacoes_investimento.csv")
    if recomendacoes:
        fieldnames = ["id_cliente", "nome", "email", "perfil", "ativo", "cotacao_atual", "variacao_pct", "oportunidade_compra", "recomendacao"]
        with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(recomendacoes)
            
    json_path = os.path.join(OUTPUT_DIR, "recomendacoes_investimento.json")
    with open(json_path, mode="w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, ensure_ascii=False, indent=2)
        
    return csv_path, json_path

def main():
    try:
        investidores = load_investidores()
        raw_market = fetch_market_data()
        recomendacoes = analyze_opportunities(investidores, raw_market)
        csv_path, json_path = save_outputs(recomendacoes)
        
        compras = [r for r in recomendacoes if r["oportunidade_compra"]]
        
        result = {
            "status": "SUCESSO",
            "executado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_investidores": len(investidores),
            "oportunidades_identificadas": len(compras),
            "recomendacoes": recomendacoes,
            "arquivos": {
                "csv": os.path.abspath(csv_path).replace("\\", "/"),
                "json": os.path.abspath(json_path).replace("\\", "/")
            }
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    except Exception as e:
        error = {"status": "ERRO", "mensagem": str(e)}
        print(json.dumps(error, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
