import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Carrega a chave do arquivo .env sem as aspas
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Inicializa o cliente com a nova biblioteca
client = genai.Client(api_key=api_key)

# Instrução de sistema para forçar o JSON
system_instruction = """
Você é um assistente financeiro de um motorista de aplicativo. 
Sua tarefa é extrair os gastos relatados no texto e retornar APENAS um objeto JSON válido, sem markdown adicional.
O JSON deve conter as chaves: "categoria" ("Combustivel", "Alimentacao" ou "Manutencao"), "valor" (numero decimal), e "descricao".
"""

# Interface
print("--- Extrator de Despesas para Motoristas ---")
entrada_usuario = input("Digite o seu gasto (ex: 'Abasteci 100 conto de etanol'): ")

print("\nProcessando...")

# Nova forma de chamar a API
response = client.models.generate_content(
    model='gemini-3.8-flash',
    contents=entrada_usuario,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.1,
    ),
)

print("\nResultado Extraído:")
print(response.text)