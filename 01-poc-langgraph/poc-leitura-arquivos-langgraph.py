import os
import time
import random
import json
from dotenv import load_dotenv 
from google import genai
from google.genai.errors import APIError
from typing import TypedDict
from langgraph.graph import StateGraph, END

# --- SCHEMA JSON ESTRITO ---
JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "avaliacao": {
            "type": "STRING",
            "description": "Status da correção: 'Certo', 'Errado' ou 'Parcialmente Certo'."
        },
        "justificativa": {
            "type": "STRING",
            "description": "Explicação detalhada dos erros/acertos pedagógicos."
        },
        "dica_correcao": {
            "type": "STRING",
            "description": "Dicas e orientações para o aluno corrigir o código, sem incluir o código em si."
        },
        "sugestao_correcao": {
            "type": "STRING",
            "description": "Apenas o código Java corrigido, sem comentários ou mensagens extras."
        }
    },
    "required": ["avaliacao", "justificativa", "dica_correcao", "sugestao_correcao"]
}


# --- COMPONENTES DA INTERFACE (POO) ---
import tkinter as tk
from tkinter import filedialog, messagebox

class CardSelecao(tk.Frame):
    def __init__(self, master, titulo, subtitulo, comando_selecao, **kwargs):
        super().__init__(master, bg="#ffffff", bd=0, highlightbackground="#e2e8f0", highlightthickness=1, **kwargs)
        self.lbl_titulo = tk.Label(self, text=titulo, font=("Segoe UI", 10, "bold"), fg="#1e293b", bg="#ffffff")
        self.lbl_titulo.pack(anchor="w", padx=15, pady=(12, 0))
        self.lbl_sub = tk.Label(self, text=subtitulo, font=("Segoe UI", 8), fg="#64748b", bg="#ffffff")
        self.lbl_sub.pack(anchor="w", padx=15)
        self.bottom_frame = tk.Frame(self, bg="#ffffff")
        self.bottom_frame.pack(fill="x", padx=15, pady=(10, 12))
        self.btn = tk.Button(
            self.bottom_frame, text="Selecionar", command=comando_selecao,
            font=("Segoe UI", 9, "bold"), bg="#f1f5f9", fg="#1e293b",
            relief="flat", cursor="hand2", padx=15, pady=5,
            activebackground="#e2e8f0"
        )
        self.btn.pack(side="left")
        self.lbl_status = tk.Label(self.bottom_frame, text="Nenhum selecionado", font=("Consolas", 9), fg="#3b82f6", bg="#ffffff")
        self.lbl_status.pack(side="left", padx=15)
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg="#e2e8f0"))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg="#f1f5f9"))
    def atualizar_status(self, texto):
        self.lbl_status.config(text=texto)

class InterfaceCorretor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Corretor de Projetos POO")
        self.root.configure(bg="#f8fafc")
        largura, altura = 640, 580
        self.root.update_idletasks()
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")
        self.root.resizable(False, False)
        self.caminho_enunciado = ""
        self.caminhos_gabarito = []
        self.caminhos_aluno = []
        self.confirmado = False
        self._build_ui()
    def _build_ui(self):
        header = tk.Frame(self.root, bg="#f8fafc", pady=20)
        header.pack(fill="x")
        tk.Label(header, text="Corretor de Projetos POO", font=("Segoe UI", 16, "bold"), fg="#0f172a", bg="#f8fafc").pack()
        self.main_container = tk.Frame(self.root, bg="#f8fafc", padx=30)
        self.main_container.pack(fill="both", expand=True)
        self.card_enunc = CardSelecao(self.main_container, "1. Enunciado", "Ficheiro .txt com as instruções", self.sel_enunciado)
        self.card_enunc.pack(fill="x", pady=8)
        self.card_gaba = CardSelecao(self.main_container, "2. Gabarito", "Pasta com ficheiros .java (Opcional)", self.sel_gabarito)
        self.card_gaba.pack(fill="x", pady=8)
        self.card_aluno = CardSelecao(self.main_container, "3. Código do Aluno", "Pasta com o projeto .java do aluno", self.sel_aluno)
        self.card_aluno.pack(fill="x", pady=8)
        footer = tk.Frame(self.root, bg="#f8fafc", pady=30)
        footer.pack(fill="x")
        self.btn_exec = tk.Button(
            footer, text="EXECUTAR ANÁLISE", command=self.executar,
            font=("Segoe UI", 11, "bold"), bg="#10b981", fg="#ffffff",
            relief="flat", cursor="hand2", padx=50, pady=12,
            activebackground="#059669"
        )
        self.btn_exec.pack()
    def sel_enunciado(self):
        # Não define initialdir, sempre abre no diretório padrão do sistema
        p = filedialog.askopenfilename(title="Selecionar Enunciado", filetypes=[("Texto", "*.txt")])
        if p:
            self.caminho_enunciado = p
            self.card_enunc.atualizar_status(os.path.basename(p))

    def sel_gabarito(self):
        initialdir = None
        if self.caminho_enunciado:
            initialdir = os.path.dirname(os.path.dirname(self.caminho_enunciado))
        pasta = filedialog.askdirectory(title="Selecionar Pasta do Gabarito", initialdir=initialdir)
        if pasta:
            self.caminhos_gabarito = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.java')]
            self.card_gaba.atualizar_status(f"{os.path.basename(pasta)} ({len(self.caminhos_gabarito)} arq.)")

    def sel_aluno(self):
        initialdir = None
        if self.caminhos_gabarito:
            # Pega o diretório pai da pasta do gabarito
            first_gabarito = self.caminhos_gabarito[0]
            initialdir = os.path.dirname(os.path.dirname(first_gabarito))
        pasta = filedialog.askdirectory(title="Selecionar Pasta do Aluno", initialdir=initialdir)
        if pasta:
            self.caminhos_aluno = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.java')]
            self.card_aluno.atualizar_status(f"{os.path.basename(pasta)} ({len(self.caminhos_aluno)} arq.)")
    def executar(self):
        if not self.caminho_enunciado or not self.caminhos_aluno:
            messagebox.showwarning("Aviso", "Por favor, selecione o Enunciado e a Pasta do Aluno.")
            return
        self.confirmado = True
        self.root.destroy()
    def get_data(self):
        self.root.mainloop()
        return self.caminho_enunciado, self.caminhos_gabarito, self.caminhos_aluno if self.confirmado else (None, None, None)



# Seleciona os arquivos ao iniciar o script usando a nova interface orientada a objetos
app = InterfaceCorretor()
ENUNCIADO_FILE_PATH, GABARITO_FILE_PATHS, CODIGOS_JAVA_PATHS = app.get_data()
if ENUNCIADO_FILE_PATH:
    print(f"Enunciado selecionado: {ENUNCIADO_FILE_PATH}")
    print(f"Gabarito(s) selecionado(s): {GABARITO_FILE_PATHS if GABARITO_FILE_PATHS else 'Nenhum'}")
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
    "Avalie o código Java do aluno considerando o enunciado. Forneça feedback construtivo e educativo, focado em princípios de POO (Encapsulamento, Herança, Lógica).\n"
    "Sua resposta DEVE ser um JSON válido, SEM TEXTO ANTES OU DEPOIS, e seguir EXATAMENTE este schema:\n"
    '{\n'
    '  "avaliacao": "Certo" | "Errado" | "Parcialmente Certo",\n'
    '  "justificativa": string,\n'
    '  "dica_correcao": string,\n'
    '  "sugestao_correcao": string\n'
    '}\n'
    "No campo 'sugestao_correcao', coloque o código Java corrigido e inclua comentários explicativos sempre que possível para ajudar o aluno a entender as correções e boas práticas. Não inclua mensagens de parabéns ou explicações fora do código. "
    "Se a sugestão envolver mais de um arquivo, separe cada arquivo usando exatamente o padrão:\n"
    "// --- ARQUIVO INÍCIO: NomeDoArquivo.java ---\n"
    "(código do arquivo, com comentários explicativos se necessário)\n"
    "// --- ARQUIVO FIM: NomeDoArquivo.java ---\n"
    "No campo 'dica_correcao', coloque as orientações e dicas para o aluno corrigir o código, sem incluir o código em si. Use ```java apenas no prompt, não na resposta JSON. Responda integralmente em português. Não adicione explicações fora do JSON."
)

# --- 2. DEFINIÇÃO DO ESTADO (STATE) DO LANGGRAPH ---
from typing import Optional
class CorrectionState(TypedDict):
    """Representa o estado do processo de correção."""
    enunciado: str
    gabarito: Optional[str]
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
    """Função robusta para chamar a API do Gemini com retries e backoff, forçando resposta JSON ESTRITO."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": JSON_SCHEMA
                }
            )
            # Força o parse do JSON para garantir estrutura
            try:
                data = json.loads(response.text)
                # Garante que todas as chaves obrigatórias existem
                for key in ["avaliacao", "justificativa", "sugestao_correcao"]:
                    if key not in data:
                        raise ValueError(f"Chave obrigatória ausente: {key}")
                return data
            except Exception as e:
                print(f"Erro ao decodificar JSON da LLM: {e}\nResposta recebida:\n{response.text}")
                raise e
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
    e atualiza o estado com o feedback bruto (JSON) e status.
    """
    enunciado_log = state['enunciado'].split('\n')[0][:70] + '...'
    print(f"\n--- INICIANDO CHAMADA À LLM: CORREÇÃO de '{enunciado_log}' ---")
    enunciado = state["enunciado"]
    codigo_aluno = state["codigo_aluno"]
    gabarito = state.get("gabarito")
    if gabarito:
        prompt = (
            f"--- ENUNCIADO DO EXERCÍCIO ---\n{enunciado}\n"
            f"--- GABARITO DO PROFESSOR ---\n{gabarito}\n"
            f"--- CÓDIGO DO ALUNO ---\n```java\n{codigo_aluno}\n```\n"
            "Avalie o código do aluno COMPARANDO DIRETAMENTE com o gabarito acima. Considere o gabarito como a única solução correta. Aponte diferenças, similaridades e se o código do aluno está igual, melhor ou pior que o gabarito. Siga a estrutura rígida definida no System Instruction."
        )
    else:
        prompt = format_correction_prompt(enunciado, codigo_aluno)
    feedback_json = generate_content_with_retry(prompt, SYSTEM_INSTRUCTION_CORRECAO)
    print("--- LLM RESPONDEU. RETORNANDO AO GRAFO. ---")
    return {
        "feedback_bruto": json.dumps(feedback_json, ensure_ascii=False, indent=2),
        "avaliacao_status": feedback_json["avaliacao"]
    }

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
    if GABARITO_FILE_PATHS:
        print(f"[PASSO 3] Lendo gabarito dos arquivos: {GABARITO_FILE_PATHS}")
        gabarito_content = read_and_concat_java_files(GABARITO_FILE_PATHS)
    else:
        gabarito_content = None
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
        "gabarito": gabarito_content,
        "codigo_aluno": codigo_content,
        "feedback_bruto": "",
        "avaliacao_status": ""
    }
    final_state = app.invoke(initial_state)
    print("\n--- RESULTADO FINAL DO GRAFO ---")
    print(f"Feedback da LLM para {TEST_CASE_NAME} (JSON):")
    print(final_state["feedback_bruto"])
    print(f"\nStatus de avaliação: {final_state['avaliacao_status']}")
    print("\n" + "=" * 80)
    print("FIM DA EXECUÇÃO DO LANGGRAPH: PASSO 3 CONCLUÍDO.")
    print("=" * 80)

    # --- GERAÇÃO DO RELATÓRIO HTML ---
    import webbrowser
    from relatorio_html import gerar_relatorio_html
    try:
        feedback_json = json.loads(final_state["feedback_bruto"])
    except Exception:
        feedback_json = {"avaliacao": "Erro", "justificativa": "Erro ao decodificar JSON.", "sugestao_correcao": ""}
    enunciado = enunciado_content.strip()
    # Pós-processamento para normalizar quebras de linha escapadas
    def normalize_newlines(text):
        return text.replace('\\n', '\n') if text else text

    gabarito = normalize_newlines(gabarito_content.strip()) if gabarito_content else ""
    codigo_aluno = normalize_newlines(codigo_content.strip())
    avaliacao = feedback_json.get("avaliacao", "")
    justificativa = feedback_json.get("justificativa", "")
    dica_correcao = feedback_json.get("dica_correcao", "")
    sugestao_correcao = normalize_newlines(feedback_json.get("sugestao_correcao", ""))
    relatorio_saida = gerar_relatorio_html(
        enunciado=enunciado,
        gabarito=gabarito,
        codigo_aluno=codigo_aluno,
        avaliacao=avaliacao,
        justificativa=justificativa,
        dica_correcao=dica_correcao,
        sugestao_correcao=sugestao_correcao
    )
    print(f"\nRelatório HTML gerado em: {relatorio_saida}")
    webbrowser.open(f"file://{relatorio_saida}")
