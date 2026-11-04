import os
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

def configurar_api():
    """Carrega as variáveis de ambiente e inicializa o cliente do Gemini."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("Chave da API não encontrada. Verifique seu arquivo .env.")
        
    return genai.Client(api_key=api_key)

def extrair_despesas(client, texto_usuario):
    """Envia o texto do usuário para o LLM e extrai as entidades em formato JSON."""
    system_instruction = """
    Você é um assistente financeiro de um motorista de aplicativo. 
    Sua tarefa é extrair os gastos relatados no texto e retornar APENAS um objeto JSON válido, sem markdown adicional.
    O JSON deve conter as chaves: "categoria" ("Combustivel", "Alimentacao" ou "Manutencao"), "valor" (numero decimal), e "descricao".
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=texto_usuario,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
            ),
        )
        return response.text
        
    except APIError as e:
        return f"[Erro na API do Gemini] O serviço pode estar indisponível ou sobrecarregado.\nDetalhes técnicos: {e}"
    except Exception as e:
        return f"[Erro Inesperado] Falha ao processar o conteúdo.\nDetalhes: {e}"

def main():
    """Função principal que gerencia o fluxo de execução via terminal."""
    print("--- Extrator de Despesas para Motoristas ---")
    
    # 1. Configura a API lidando com possível erro de falta de chave
    try:
        client = configurar_api()
    except ValueError as erro_config:
        print(f"\nErro de Configuração: {erro_config}")
        return

    # 2. Captura a entrada
    entrada_usuario = input("Digite o seu gasto (ex: 'Abasteci 100 conto de etanol'): ")
    
    # 3. Processa e exibe
    print("\nProcessando...")
    resultado = extrair_despesas(client, entrada_usuario)
    
    print("\nResultado Extraído:")
    print(resultado)

if __name__ == "__main__":
    main()