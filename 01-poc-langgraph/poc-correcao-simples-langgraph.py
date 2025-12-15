import os
import time
import random
from dotenv import load_dotenv 
from google import genai
from google.genai.errors import APIError
from typing import TypedDict
from langgraph.graph import StateGraph, END

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO DO GEMINI ---
API_KEY = os.getenv("GEMINI_API_KEY")

try:
    if not API_KEY:
        raise ValueError("Chave API não encontrada.")
    # A variável 'client' é necessária para a função generate_content_with_retry
    client = genai.Client(api_key=API_KEY)
except ValueError:
    print("Erro: A chave API não foi carregada. Verifique o arquivo .env.")
    exit()
except Exception as e:
    print(f"Erro ao inicializar o cliente Gemini: {e}")
    exit()

MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 5
SYSTEM_INSTRUCTION_CORRECAO = (
    "Você é um Professor de Programação Orientada a Objetos (POO) da UFLA. "
    "Sua função é avaliar o código Java de um aluno, considerando o enunciado. "
    "Forneça um feedback construtivo e educativo, focado em princípios de POO (Encapsulamento, Herança, Lógica). "
    "Sua resposta DEVE seguir EXATAMENTE esta estrutura, usando títulos em negrito:\n"
    "1. **Avaliação:** Certo, Errado ou Parcialmente Certo.\n"
    "2. **Justificativa:** Explique detalhadamente a lógica e a aplicação dos princípios de POO.\n"
    "3. **Sugestão de Correção:** Apresente sugestões para aprimoramento ou correção do código, mesmo que ele esteja 'Certo'.\n"
    "Responda integralmente em português."
)

# --- 2. DEFINIÇÃO DO ESTADO (STATE) DO LANGGRAPH ---
# O estado é o dicionário compartilhado entre todos os nós do grafo.
class CorrectionState(TypedDict):
    """Representa o estado do processo de correção."""
    enunciado: str
    codigo_aluno: str
    feedback_bruto: str  # Resultado da LLM (Passo 1/Nó Básico)
    avaliacao_status: str # Status extraído para tomada de decisão futura

# --- 3. FUNÇÕES UTILITÁRIAS (REUTILIZANDO DA CORREÇÃO SIMPLES) ---

def generate_content_with_retry(prompt, system_instruction):
    """Função robusta para chamar a API do Gemini com retries e backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"system_instruction": system_instruction}
            )
            return response.text

        except APIError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                delay = 2**attempt + random.uniform(0, 1)
                print(f"Aviso: Taxa limite atingida. Tentando novamente em {delay:.2f} segundos...")
                time.sleep(delay)
            else:
                raise e # Lança outros erros
        except Exception as e:
            raise e
    raise Exception("Falha ao gerar conteúdo após múltiplas tentativas.")

def format_correction_prompt(enunciado, codigo_aluno):
    """Formata a entrada de dados para o modelo (usa o SYSTEM_INSTRUCTION global)."""
    return (
        f"--- ENUNCIADO DO EXERCÍCIO ---\n"
        f"{enunciado}\n"
        "--- CÓDIGO DO ALUNO ---\n"
        f"```java\n{codigo_aluno}\n```\n\n"
        "Siga a estrutura rígida definida no System Instruction."
    )

# --- 4. DEFINIÇÃO DOS NÓS DO LANGGRAPH ---

def correction_node(state: CorrectionState) -> dict:
    """
    Nó de correção: Recebe o estado, executa a chamada à LLM
    e atualiza o estado com o feedback bruto.
    """
    # Exibe o início do enunciado para rastreabilidade
    enunciado_log = state['enunciado'].split('\n')[0][:70] + '...'
    print(f"\n--- INICIANDO CHAMADA À LLM: CORREÇÃO de '{enunciado_log}' ---") # Log mais claro
    
    enunciado = state["enunciado"]
    codigo_aluno = state["codigo_aluno"]
    
    prompt = format_correction_prompt(enunciado, codigo_aluno)
    
    # Chama a função robusta do POC
    feedback = generate_content_with_retry(prompt, SYSTEM_INSTRUCTION_CORRECAO)
    
    print("--- LLM RESPONDEU. RETORNANDO AO GRAFO. ---")
    # Simplesmente atualiza o estado com o resultado
    return {"feedback_bruto": feedback}

# --- 5. EXECUÇÃO DO GRAFO ---
if __name__ == "__main__":
    
    # Mensagem de início geral (mais clara)
    print("\n" + "=" * 80)
    print("INÍCIO DA EXECUÇÃO DO LANGGRAPH: CORREÇÃO DE MÚLTIPLOS CASOS DE TESTE")
    print("=" * 80)
    
    # 5.1. Inicialização do Grafo
    workflow = StateGraph(CorrectionState)
    
    # Adiciona o único nó (Node) que faz a correção
    workflow.add_node("correcao", correction_node)
    
    # Define o ponto de entrada e a transição: correcao -> FIM
    workflow.set_entry_point("correcao")
    workflow.add_edge("correcao", END)
    
    # Compila o grafo
    app = workflow.compile()
    
    # 5.2. Casos de Teste (Reutilizando a ContaBancaria)
    
    ENUNCIADO = (
        "Implemente uma classe Java chamada 'ContaBancaria' com os seguintes requisitos: "
        "1. Um atributo privado 'saldo' do tipo double. "
        "2. Um método 'depositar(double valor)' que adiciona valor ao saldo. "
        "3. Um método 'sacar(double valor)' que subtrai valor do saldo se houver saldo suficiente. "
        "4. Um método 'getSaldo()' que retorna o saldo atual."
    )
    
    # Caso 1: Código Correto
    CODIGO_CORRETO = """
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
"""

    # Caso 2: Código com Erro (Encapsulamento e Lógica de Depósito/Saque)
    CODIGO_ERRO = """
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
"""
    
    # Caso 3: Código Parcialmente Certo (Falta Validação de Negativos no Depósito, mas Saque está OK)
    CODIGO_PARCIAL = """
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
"""
    
    def run_test_case(test_name, codigo_aluno):
        print("\n" + "=" * 80)
        print(f"INÍCIO DA EXECUÇÃO - {test_name}")
        print("-" * 80)
        initial_state = {
            "enunciado": ENUNCIADO,
            "codigo_aluno": codigo_aluno,
            "feedback_bruto": "",
            "avaliacao_status": ""
        }
        final_state = app.invoke(initial_state)
        print("\n--- RESULTADO FINAL DO GRAFO ---")
        print(f"Feedback da LLM para {test_name}:")
        print(final_state["feedback_bruto"])

    run_test_case("TESTE 1: CÓDIGO CORRETO", CODIGO_CORRETO)
    run_test_case("TESTE 2: CÓDIGO COM ERRO", CODIGO_ERRO)
    run_test_case("TESTE 3: CÓDIGO PARCIALMENTE CERTO", CODIGO_PARCIAL)

    print("\n" + "=" * 80)
    print("FIM DA EXECUÇÃO DO LANGGRAPH: OS TRÊS TESTES FORAM INVOCADOS SEQUENCIALMENTE.")
    print("=" * 80)