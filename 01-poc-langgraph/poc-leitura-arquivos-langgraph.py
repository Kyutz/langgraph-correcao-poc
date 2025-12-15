
import os
import time
import random
from dotenv import load_dotenv 
from google import genai
from google.genai.errors import APIError
from typing import TypedDict
from langgraph.graph import StateGraph, END

# Interface gráfica para seleção dos arquivos (janela principal com campos e botões)
import tkinter as tk
from tkinter import filedialog, messagebox



def escolher_arquivos_via_gui():
    root = tk.Tk()
    root.title("Selecionar arquivos para correção")
    # Centralizar janela
    largura = 700
    altura = 300
    root.update_idletasks()
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")

    caminho_enunciado = tk.StringVar(master=root)
    caminhos_codigos = []  # lista de arquivos java
    selecionado = {'ok': False}

    def selecionar_enunciado():
        caminho = filedialog.askopenfilename(title="Selecione o arquivo de ENUNCIADO", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if caminho:
            caminho_enunciado.set(caminho)

    def adicionar_codigo():
        arquivos = filedialog.askopenfilenames(title="Adicionar arquivos de CÓDIGO DO ALUNO", filetypes=[("Java Files", "*.java"), ("All Files", "*.*")])
        for arquivo in arquivos:
            if arquivo not in caminhos_codigos:
                caminhos_codigos.append(arquivo)
        atualizar_codigos_entry()

    def remover_codigo():
        selecionados = listbox_codigos.curselection()
        for idx in reversed(selecionados):
            del caminhos_codigos[idx]
        atualizar_codigos_entry()

    def executar():
        if not caminho_enunciado.get() or not caminhos_codigos:
            messagebox.showerror("Erro", "Selecione o enunciado e pelo menos um arquivo de código.")
            return
        selecionado['ok'] = True
        root.destroy()

    tk.Label(root, text="Enunciado do Exercício (.txt):").grid(row=0, column=0, padx=10, pady=10, sticky='e')
    enunciado_var = tk.StringVar(master=root)
    entry_enunciado = tk.Entry(root, textvariable=enunciado_var, width=50, state='readonly')
    entry_enunciado.grid(row=0, column=1, padx=5)
    def atualizar_enunciado_entry():
        if caminho_enunciado.get():
            enunciado_var.set(os.path.basename(caminho_enunciado.get()))
        else:   
            enunciado_var.set("")
    btn_enunciado = tk.Button(root, text="Procurar...", command=lambda: [selecionar_enunciado(), atualizar_enunciado_entry()])
    btn_enunciado.grid(row=0, column=2, padx=5)
    atualizar_enunciado_entry()

    tk.Label(root, text="Códigos do Aluno (.java):").grid(row=1, column=0, padx=10, pady=10, sticky='e')
    listbox_codigos = tk.Listbox(root, selectmode=tk.MULTIPLE, width=50, height=6)
    listbox_codigos.grid(row=1, column=1, padx=5, rowspan=2, sticky='n')
    def atualizar_codigos_entry():
        listbox_codigos.delete(0, tk.END)
        for f in caminhos_codigos:
            listbox_codigos.insert(tk.END, os.path.basename(f))
    btn_add_codigos = tk.Button(root, text="Adicionar...", command=adicionar_codigo, width=18)
    btn_add_codigos.grid(row=1, column=2, padx=5, pady=2, sticky='n')
    btn_remover_codigos = tk.Button(root, text="Remover Selecionado(s)", command=remover_codigo, width=18)
    btn_remover_codigos.grid(row=2, column=2, padx=5, pady=2, sticky='n')
    atualizar_codigos_entry()

    btn_executar = tk.Button(root, text="Executar", command=executar, width=20, bg='#4CAF50', fg='white')
    btn_executar.grid(row=4, column=0, columnspan=3, pady=20)

    root.mainloop()

    if not selecionado['ok']:
        print("Execução cancelada pelo usuário.")
        exit()
    return caminho_enunciado.get(), list(caminhos_codigos)

# Seleciona os arquivos ao iniciar o script
ENUNCIADO_FILE_PATH, CODIGOS_JAVA_PATHS = escolher_arquivos_via_gui()
print(f"Enunciado selecionado: {ENUNCIADO_FILE_PATH}")
print(f"Arquivos de código selecionados: {CODIGOS_JAVA_PATHS}")

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO DO GEMINI ---
API_KEY = os.getenv("GEMINI_API_KEY")

try:
    if not API_KEY:
        raise ValueError("Chave API não encontrada.")
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
class CorrectionState(TypedDict):
    """Representa o estado do processo de correção."""
    enunciado: str
    codigo_aluno: str
    feedback_bruto: str  # Resultado da LLM (Passo 1/Nó Básico)
    avaliacao_status: str # Status extraído para tomada de decisão futura

# --- 3. FUNÇÕES UTILITÁRIAS ---
def read_file_content(file_path: str) -> str:
    """Função para ler o conteúdo de um arquivo de forma segura."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado no caminho: {file_path}")
        exit()
    except Exception as e:
        print(f"Erro ao ler o arquivo {file_path}: {e}")
        exit()

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
                raise e
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
    enunciado_log = state['enunciado'].split('\n')[0][:70] + '...'
    print(f"\n--- INICIANDO CHAMADA À LLM: CORREÇÃO de '{enunciado_log}' ---")
    enunciado = state["enunciado"]
    codigo_aluno = state["codigo_aluno"]
    prompt = format_correction_prompt(enunciado, codigo_aluno)
    feedback = generate_content_with_retry(prompt, SYSTEM_INSTRUCTION_CORRECAO)
    print("--- LLM RESPONDEU. RETORNANDO AO GRAFO. ---")
    return {"feedback_bruto": feedback}
def read_and_concat_java_files(file_paths):
    """Lê múltiplos arquivos Java e concatena com delimitadores para o LLM."""
    combined = ""
    for path in file_paths:
        nome = os.path.basename(path)
        conteudo = read_file_content(path)
        combined += f"// --- ARQUIVO INÍCIO: {nome} ---\n"
        combined += conteudo.strip() + "\n"
        combined += f"// --- ARQUIVO FIM: {nome} ---\n\n"
    return combined

# --- 5. EXECUÇÃO DO GRAFO ---
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("INÍCIO DA EXECUÇÃO DO LANGGRAPH: PASSO 3 - LEITURA DE ARQUIVOS")
    print("=" * 80)
    # 5.1. Leitura dos Arquivos
    print(f"\n[PASSO 3] Lendo enunciado do arquivo: {ENUNCIADO_FILE_PATH}")
    enunciado_content = read_file_content(ENUNCIADO_FILE_PATH)
    print(f"[PASSO 3] Lendo arquivos de código do aluno: {CODIGOS_JAVA_PATHS}")
    codigo_content = read_and_concat_java_files(CODIGOS_JAVA_PATHS)
    print("\n--- Conteúdo do Código Lido (Amostra) ---")
    print(codigo_content.strip()[:300] + '...')
    print("-" * 40)
    # 5.2. Inicialização e Compilação do Grafo
    workflow = StateGraph(CorrectionState)
    workflow.add_node("correcao", correction_node)
    workflow.set_entry_point("correcao")
    workflow.add_edge("correcao", END)
    app = workflow.compile()
    # 5.3. Execução do LangGraph com o Conteúdo Lido
    TEST_CASE_NAME = "TESTE DE LEITURA DE ARQUIVOS"
    print(f"\nINÍCIO DA EXECUÇÃO DO GRAFO - {TEST_CASE_NAME}")
    print("-" * 80)
    initial_state = {
        "enunciado": enunciado_content,
        "codigo_aluno": codigo_content,
        "feedback_bruto": "",
        "avaliacao_status": ""
    }
    final_state = app.invoke(initial_state)
    print("\n--- RESULTADO FINAL DO GRAFO ---")
    print(f"Feedback da LLM para {TEST_CASE_NAME}:")
    print(final_state["feedback_bruto"])
    print("\n" + "=" * 80)
    print("FIM DA EXECUÇÃO DO LANGGRAPH: PASSO 3 CONCLUÍDO.")
    print("=" * 80)
