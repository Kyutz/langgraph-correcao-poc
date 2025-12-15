# Carrega variáveis de ambiente do arquivo .env
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Inicializa o client usando a chave da API do .env
try:
    if not api_key:
        raise ValueError("A chave GEMINI_API_KEY não foi encontrada no arquivo .env.")
    client = genai.Client(api_key=api_key)
except Exception as e:
    print("Erro ao inicializar o client Gemini:", e)
    exit(1)

# Solicita ao usuário um prompt para enviar ao modelo
user_prompt = input("\nDigite um texto para enviar ao modelo Gemini (ou pressione Enter para usar o exemplo): ")
if not user_prompt.strip():
    user_prompt = "Explique como a IA funciona em poucas palavras"

# Define o modelo a ser usado (padrão: gemini-2.5-flash)
model_name = "gemini-2.5-flash"

# Envia o prompt ao modelo e exibe a resposta
try:
    response = client.models.generate_content(
        model=model_name, contents=user_prompt
    )
    print(f"\nResposta do modelo '{model_name}':\n{response.text}")
except Exception as e:
    print("Erro ao gerar conteúdo com o modelo Gemini:", e)
