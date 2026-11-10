import logging
import requests
from flask import Flask, request, render_template_string
import os
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configurações fornecidas pelo ambiente Devel Lab
URL_LLM = "https://llm-internal.softex:9001/api/generate"
MODELO = "qwen3.5:9b-q4_K_M"

# Interface visual básica (HTML)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Extrator de Despesas</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
        .container { background: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
        input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        pre { background: #eee; padding: 15px; border-radius: 4px; overflow-x: auto; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Extrator de Despesas para Motoristas</h2>
        <form method="POST">
            <label for="gasto">Descreva o seu gasto (Ex: "abasteci 50 de etanol"):</label>
            <input type="text" id="gasto" name="gasto" required>
            <button type="submit">Processar Despesa</button>
        </form>

        {% if resultado %}
            <h3>Resultado Extraído:</h3>
            <pre>{{ resultado }}</pre>
        {% endif %}
        
        {% if erro %}
            <h3 class="error">Erro de Comunicação:</h3>
            <pre class="error">{{ erro }}</pre>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    erro = None

    if request.method == "POST":
        texto_usuario = request.form.get("gasto")
        logging.info(f"Texto recebido: {texto_usuario}")
        
        # O prompt precisa ser claro para o modelo Ollama local
        prompt = f"""
        Você é um assistente financeiro. Leia o texto abaixo e extraia a despesa.
        Retorne APENAS um objeto JSON válido, sem texto antes ou depois.
        O JSON deve conter exatamente as chaves: 
        - "categoria" (escolha uma: "Combustivel", "Alimentacao" ou "Manutencao")
        - "valor" (apenas o numero decimal)
        - "descricao" (resumo curto do gasto)
        
        Texto: {texto_usuario}
        """
        
        payload = {
            "model": MODELO,
            "prompt": prompt,
            "stream": False,
            "format": "json" # Força o modelo a responder em JSON
        }
        
        try:
            # Envia a requisição para a IA interna do Devel Lab.
            # verify=False é usado conforme dica do manual para testes temporários.
            llm_host = os.getenv("OLLAMA_HOST", "https://llm-internal.softex:9001")
            resposta = requests.post(llm_host + "/api/generate", json=payload, verify=False, timeout=120)
            resposta.raise_for_status() 
            
            # A API do Ollama retorna o texto dentro da chave 'response'
            texto_json = resposta.json().get("response", "")
            
            # Tenta limpar e reformatar o JSON para ficar bonito na tela
            try:
                parsed_json = json.loads(texto_json)
                resultado = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                logging.info("Extracao realizada com sucesso.")
            except json.JSONDecodeError:
                resultado = texto_json # Se falhar, mostra o texto bruto
                logging.warning("O modelo nao retornou um JSON perfeito.")

        except requests.exceptions.RequestException as e:
            logging.error(f"Falha de comunicacao com a LLM: {e}")
            erro = f"Não foi possível conectar à LLM interna no momento. Detalhes: {e}"

    return render_template_string(HTML_TEMPLATE, resultado=resultado, erro=erro)

if __name__ == "__main__":
    # O servidor deve escutar em 0.0.0.0 e na porta 8080 conforme exigência do Devel Lab
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)