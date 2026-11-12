import logging
import os
import re
import json
import time
import httpx
from flask import Flask, request, render_template_string
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIConnectionError, APIStatusError
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://llm-internal.softex:9001").strip()
DEFAULT_TIMEOUT = "25" if GEMINI_API_KEY else "120"
REQUEST_TIMEOUT = int(os.getenv("LLM_TIMEOUT", DEFAULT_TIMEOUT))

MODELO_PADRAO = "gemini-3.5-flash" if GEMINI_API_KEY else "qwen3.5:9b-q4_K_M"
MODELO = os.getenv("LLM_MODEL", MODELO_PADRAO)

logging.info(f"=== EXTRATOR v2.1 INICIADO | Modelo: {MODELO} | Gemini Key ativa: {bool(GEMINI_API_KEY)} ===")


def obter_config_ssl():
    ca_env = os.getenv("LLM_CA_BUNDLE", "true").strip()
    if ca_env.lower() in ("false", "0", "no"):
        return False
    if ca_env.lower() in ("true", "1", "yes"):
        return True
    return ca_env


def limpar_json(texto: str) -> str:
    """Remove blocos <think>...</think>, textos introdutórios e crases markdown."""
    if not texto:
        return ""
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE).strip()
    # Se houver texto antes ou depois das chaves, isola apenas o objeto JSON {...}
    match = re.search(r"\{.*\}", texto, flags=re.DOTALL)
    if match:
        return match.group(0).strip()
    return texto


def consultar_llm(prompt: str) -> str:
    ssl_verify = obter_config_ssl()

    # 1. Prioriza o Gemini (com retentativa para erro 503 de alta demanda)
    if GEMINI_API_KEY:
        client_gemini = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT * 1000)
        )
        # Tenta o modelo principal duas vezes e, se o 503 persistir, usa o gemini-2.5-flash
        modelos_tentativa = [MODELO, MODELO, "gemini-2.5-flash"]
        for idx, mod in enumerate(modelos_tentativa, 1):
            try:
                logging.info(f"[v2.1] Consultando Gemini ({mod}) - Tentativa {idx}/{len(modelos_tentativa)}...")
                response = client_gemini.models.generate_content(
                    model=mod,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                if response.text:
                    return response.text
            except Exception as e_gemini:
                logging.warning(f"[v2.1] Falha no Gemini ({mod}): {e_gemini}")
                if idx < len(modelos_tentativa):
                    time.sleep(2)

        logging.warning("[v2.1] Gemini indisponivel apos retentativas. Acionando Ollama interno...")

    # 2. Fallback para Ollama interno via SDK OpenAI (Passo 5 do mentor)
    base_url = os.getenv("LLM_BASE_URL", f"{OLLAMA_HOST.rstrip('/')}/v1")
    modelo_interno = "qwen3.5:9b-q4_K_M" if GEMINI_API_KEY else MODELO
    http_client = httpx.Client(verify=ssl_verify, timeout=120.0)

    logging.info(f"[v2.1] Consultando endpoint OpenAI ({base_url} | modelo={modelo_interno} | verify={ssl_verify})...")
    client_openai = OpenAI(
        base_url=base_url,
        api_key=os.getenv("OPENAI_API_KEY", "ollama"),
        http_client=http_client,
        max_retries=1,
    )

    completion = client_openai.chat.completions.create(
        model=modelo_interno,
        messages=[
            {"role": "system", "content": "Responda APENAS com um objeto JSON válido, sem explicações."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    msg = completion.choices[0].message
    conteudo = msg.content or ""
    if not conteudo and hasattr(msg, "model_extra") and msg.model_extra:
        conteudo = msg.model_extra.get("reasoning", "") or msg.model_extra.get("reasoning_content", "")
    return conteudo


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
        pre { background: #eee; padding: 15px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }
        .error-box { background-color: #ffe6e6; color: #cc0000; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #ff9999; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Extrator de Despesas para Motoristas</h2>
        
        {% if erro %}
            <div class="error-box">
                <strong>Aviso:</strong> {{ erro }}
            </div>
        {% endif %}

        <form method="POST">
            <label for="gasto">Descreva o seu gasto (Ex: "abasteci 50 de etanol"):</label>
            <input type="text" id="gasto" name="gasto" required>
            <button type="submit">Processar Despesa</button>
        </form>

        {% if resultado %}
            <h3>Resultado Extraído:</h3>
            <pre>{{ resultado }}</pre>
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
        logging.info(f"[v2.1] Texto recebido: {texto_usuario}")
        
        prompt = f"""
        Extraia as despesas do texto abaixo e retorne APENAS um objeto JSON válido.
        Se houver uma única despesa, retorne um objeto com as chaves "categoria", "valor" e "descricao".
        Se houver mais de uma despesa, retorne uma chave "despesas" contendo a lista de objetos (cada um com "categoria" sendo "Combustivel", "Alimentacao" ou "Manutencao", "valor" numérico decimal e "descricao").
        
        Texto: {texto_usuario}
        """
        
        try:
            resposta_bruta = consultar_llm(prompt)
            logging.info(f"[v2.1] Resposta bruta recebida: {resposta_bruta!r}")
            texto_limpo = limpar_json(resposta_bruta)

            if not texto_limpo:
                erro = "A LLM retornou uma resposta vazia. Envie novamente."
            else:
                try:
                    parsed_json = json.loads(texto_limpo)
                    resultado = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                    logging.info("[v2.1] Extração realizada com sucesso.")
                except json.JSONDecodeError:
                    resultado = texto_limpo
                    logging.warning("[v2.1] A resposta não pôde ser formatada como JSON estrito, exibindo texto bruto.")

        except APITimeoutError:
            logging.error("[v2.1] Timeout atingido na chamada à LLM.")
            erro = "O servidor de IA demorou além do limite para responder. Tente novamente em instantes."
        except APIStatusError as e:
            logging.error(f"[v2.1] Erro HTTP da API ({e.status_code}): {e.message}")
            erro = f"O servidor de IA retornou um erro HTTP ({e.status_code}). Tente novamente."
        except APIConnectionError as e:
            logging.error(f"[v2.1] Falha de conexão/SSL: {e}")
            erro = "Falha de conexão ou verificação SSL/TLS com o servidor de IA. Se estiver em teste, defina LLM_CA_BUNDLE=false."
        except Exception as e:
            logging.error(f"[v2.1] Erro inesperado: {e}")
            erro = f"Erro ao processar a despesa: {e}"

    return render_template_string(HTML_TEMPLATE, resultado=resultado, erro=erro)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)