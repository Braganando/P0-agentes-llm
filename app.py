import os
import logging
import argparse
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

# Configuração do Log (Item 16)
logging.basicConfig(
    filename='execucao.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def configurar_api():
    """Carrega as variáveis de ambiente e inicializa o cliente do Gemini."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logging.error("Chave da API não encontrada no arquivo .env.")
        raise ValueError("Chave da API não encontrada. Verifique seu arquivo .env.")
        
    return genai.Client(api_key=api_key)

def extrair_despesas(client, texto_usuario, temperatura):
    """Envia o texto para o LLM e extrai as entidades em formato JSON."""
    system_instruction = """
    Você é um assistente financeiro de um motorista de aplicativo. 
    Sua tarefa é extrair os gastos relatados no texto e retornar APENAS um objeto JSON válido, sem markdown adicional.
    O JSON deve conter as chaves: "categoria" ("Combustivel", "Alimentacao" ou "Manutencao"), "valor" (numero decimal), e "descricao".
    """
    
    logging.info(f"Enviando prompt. Temperatura configurada: {temperatura}")
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=texto_usuario,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperatura,
            ),
        )
        logging.info("Requisição processada com sucesso pelo LLM.")
        return response.text
        
    except APIError as e:
        logging.error(f"Erro na API do Gemini: {e}")
        return f"[Erro na API] Serviço indisponível ou limite excedido. Consulte o arquivo execucao.log para detalhes."
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return f"[Erro Inesperado] Falha ao processar. Consulte o arquivo execucao.log."

def main():
    """Gerencia o fluxo de execução e a captura de argumentos de linha de comando."""
    
    # Adiciona suporte a parâmetros de linha de comando (Item 15)
    parser = argparse.ArgumentParser(description="Extrator de Despesas com LLM")
    parser.add_argument("--temp", type=float, default=0.1, help="Temperatura do modelo LLM (0.0 a 1.0)")
    args = parser.parse_args()

    print("--- Extrator de Despesas para Motoristas ---")
    logging.info("--- Nova execução da aplicação iniciada ---")

    try:
        client = configurar_api()
    except ValueError as erro_config:
        print(f"\nErro de Configuração: {erro_config}")
        return

    entrada_usuario = input("Digite o seu gasto (ex: 'Abasteci 100 conto de etanol'): ")
    
    print(f"\nProcessando com LLM (Temperatura: {args.temp})...")
    resultado = extrair_despesas(client, entrada_usuario, args.temp)
    
    print("\nResultado Extraído:")
    print(resultado)
    logging.info("Aplicação finalizada normalmente.\n")

if __name__ == "__main__":
    main()