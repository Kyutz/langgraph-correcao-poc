# POC Correção Simples
# Este script utiliza o Gemini para atuar como corretor de exercícios de POO em Java.

import os
import time
from dotenv import load_dotenv
from google import genai

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Função para chamada à API Gemini
# Retorna a resposta do modelo ou None em caso de falha

def generate_content_with_retry(prompt, model_name="gemini-2.5-flash", max_retries=5, base_delay=2):
    """
    Chama a API Gemini com exponential backoff para erros temporários.
    Retorna a resposta do modelo ou None em caso de falha.
    """
    for attempt in range(max_retries):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Erro ao chamar Gemini (tentativa {attempt+1}):", e)
            # Exponential backoff: espera dobra a cada tentativa
            wait = base_delay * (2 ** attempt)
            time.sleep(wait)
    return None

# Enunciado do exercício (exemplo simples de Java)
exercise_statement = (
    "Implemente uma classe Java chamada ContaBancaria com os seguintes requisitos: "
    "1. Um atributo privado saldo do tipo double. "
    "2. Um método depositar(double valor) que adiciona valor ao saldo. "
    "3. Um método sacar(double valor) que subtrai valor do saldo se houver saldo suficiente. "
    "4. Um método getSaldo() que retorna o saldo atual."
)

# Exemplos de código do aluno
student_code_correct = '''
public class ContaBancaria {
    private double saldo;
    public void depositar(double valor) {
        saldo += valor;
    }
    public void sacar(double valor) {
        if (saldo >= valor) {
            saldo -= valor;
        }
    }
    public double getSaldo() {
        return saldo;
    }
}
'''

student_code_error = '''
public class ContaBancaria {
    public double saldo; // ERRO: Atributo público
    public void depositar(double valor) {
        saldo = valor; // ERRO: Sobrescreve
    }
    public void sacar(double valor) {
        saldo -= valor; // ERRO: Não verifica saldo
    }
    public double getSaldo() {
        return saldo;
    }
}
'''

student_code_partial = '''
public class ContaBancaria {
    private double saldo; // Certo: Privado
    public void depositar(double valor) {
        // Parcial: Não valida se valor > 0, mas adiciona corretamente
        saldo += valor;
    }
    public void sacar(double valor) {
        if (saldo >= valor) {
            saldo -= valor;
        }
    }
    public double getSaldo() {
        return saldo;
    }
}
'''

system_prompt = (
    "Você é um Professor de Programação Orientada a Objetos (POO) da UFLA. "
    "Sua função é avaliar o código Java de um aluno, considerando o enunciado. "
    "Forneça um feedback construtivo e educativo, focado em princípios de POO (Encapsulamento, Herança, Lógica). "
    "Sua resposta DEVE seguir EXATAMENTE esta estrutura, usando os títulos em negrito:\n"
    "1. **Avaliação:** Certo, Errado ou Parcialmente Certo.\n"
    "2. **Justificativa:** Explique detalhadamente a lógica e a aplicação dos princípios de POO.\n"
    "3. **Sugestão de Correção:** Apresente sugestões para aprimoramento ou correção do código, mesmo que ele esteja 'Certo'.\n"
    "Responda integralmente em português."
)

# Função para montar o prompt completo

def build_prompt(system_prompt, exercise_statement, student_code):
    return (
        f"{system_prompt}\n\n"
        f"Enunciado do exercício:\n{exercise_statement}\n\n"
        f"Código do aluno:\n{student_code}\n"
    )

# Testa o caso correto
print("\n--- Teste: Código Correto ---")
prompt_correct = build_prompt(system_prompt, exercise_statement, student_code_correct)
feedback_correct = generate_content_with_retry(prompt_correct)
print(feedback_correct or "Erro ao obter resposta do Gemini.")

# Testa o caso com erro
print("\n--- Teste: Código com Erro ---")
prompt_error = build_prompt(system_prompt, exercise_statement, student_code_error)
feedback_error = generate_content_with_retry(prompt_error)
print(feedback_error or "Erro ao obter resposta do Gemini.")

# Testa o caso parcial
print("\n--- Teste: Código Parcial ---")
prompt_partial = build_prompt(system_prompt, exercise_statement, student_code_partial)
feedback_partial = generate_content_with_retry(prompt_partial)
print(feedback_partial or "Erro ao obter resposta do Gemini.")
