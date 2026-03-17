import os
import time
import random
import json
import re
import zipfile
import tempfile
import webbrowser
import subprocess
from typing import TypedDict, Optional, List, Union

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askstring

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from langgraph.graph import StateGraph, END

from relatorio_html import gerar_relatorio_html

# --- Funções utilitárias ---
def selecionar_pasta_ou_zip(pasta, prefixo_temp):
    """Se houver ZIP na pasta, extrai e retorna a subpasta extraída. Senão, retorna a própria pasta."""
    arquivos_zip = [f for f in os.listdir(pasta) if f.lower().endswith('.zip')]
    if arquivos_zip:
        # Se houver mais de um zip, pede para escolher qual
        if len(arquivos_zip) > 1:
            zip_nome = askstring("ZIP encontrado", f"Foram encontrados vários ZIPs na pasta. Digite o nome do ZIP a ser extraído:\n{arquivos_zip}")
            if not zip_nome or zip_nome not in arquivos_zip:
                messagebox.showwarning("Aviso", "ZIP não selecionado corretamente.")
                return None
        else:
            zip_nome = arquivos_zip[0]
        zip_path = os.path.join(pasta, zip_nome)
        temp_dir = tempfile.mkdtemp(prefix=prefixo_temp)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        subdirs = [os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        if subdirs:
            return subdirs[0]
        else:
            return temp_dir
    return pasta

def buscar_arquivos_java(pasta):
    """Busca recursivamente arquivos .java em uma pasta."""
    java_files = []
    for root, _, files in os.walk(pasta):
        for f in files:
            if f.endswith('.java'):
                java_files.append(os.path.join(root, f))
    return java_files

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


# --- COMPONENTES DA INTERFACE ---
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
        altura = 720
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
        self.card_enunc = CardSelecao(self.main_container, "1. Enunciado", "Instruções (Markdown ou Texto)", self.sel_enunciado)
        self.card_enunc.pack(fill="x", pady=8)
        self.card_gaba = CardSelecao(self.main_container, "2. Gabarito", "Pasta com ficheiros .java (Opcional)", self.sel_gabarito)
        self.card_gaba.pack(fill="x", pady=8)
        self.card_aluno = CardSelecao(self.main_container, "3. Código do Aluno", "Pasta com o projeto .java do aluno", self.sel_aluno)
        self.card_aluno.pack(fill="x", pady=8)
        self.card_concepts = CardSelecao(self.main_container, "4. Conceitos a Avaliar", "Escolher quais conceitos incluir na avaliação (Opcional)", self.sel_conceitos)
        self.card_concepts.pack(fill="x", pady=8)
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
        p = filedialog.askopenfilename(title="Selecionar Enunciado", filetypes=[("Markdown/Text", ("*.md", "*.txt"))])
        if p:
            self.caminho_enunciado = p
            self.card_enunc.atualizar_status(os.path.basename(p))

    def sel_gabarito(self):
        initialdir = None
        if self.caminho_enunciado:
            initialdir = os.path.dirname(os.path.dirname(self.caminho_enunciado))
        pasta = filedialog.askdirectory(title="Selecionar Pasta do Gabarito", initialdir=initialdir)
        if not pasta:
            return
        pasta_final = selecionar_pasta_ou_zip(pasta, "gabarito_zip_")
        if not pasta_final:
            return
        self.caminhos_gabarito = buscar_arquivos_java(pasta_final)
        self.card_gaba.atualizar_status(f"{os.path.basename(pasta_final)} ({len(self.caminhos_gabarito)} arq.)")

    def sel_aluno(self):
        # Permite selecionar uma pasta única de aluno ou um diretório pai contendo múltiplos projetos de alunos.
        initialdir = None
        if self.caminhos_gabarito:
            first_gabarito = self.caminhos_gabarito[0]
            initialdir = os.path.dirname(os.path.dirname(first_gabarito))

        pasta = filedialog.askdirectory(title="Selecionar Pasta do Aluno (ou pasta com vários alunos)", initialdir=initialdir)
        if not pasta:
            return
        pasta_final = selecionar_pasta_ou_zip(pasta, "aluno_zip_")
        if not pasta_final:
            return

        # Se a pasta selecionada contém subpastas, é oferecido seleção múltipla para o usuário
        subdirs = [os.path.join(pasta_final, d) for d in os.listdir(pasta_final) if os.path.isdir(os.path.join(pasta_final, d))]
        if subdirs:
            # Constrói blocos no formato esperado por _open_concepts_selector
            blocks = []
            for i, d in enumerate(subdirs, start=1):
                blocks.append({'num': i, 'title': os.path.basename(d), 'text': os.path.basename(d) + '\n'})
            sel = self._open_concepts_selector(blocks)
            if sel is None:
                return
            selected_dirs = [subdirs[i] for i in sel]
            # Armazena a lista de pastas de alunos selecionadas
            self.alunos_dirs = selected_dirs
            total_files = sum(len(buscar_arquivos_java(sd)) for sd in selected_dirs)
            self.card_aluno.atualizar_status(f"{len(selected_dirs)} alunos selecionados ({total_files} arquivos .java)")
        else:
            # Sem subpastas: trata como um único aluno
            java_files = buscar_arquivos_java(pasta_final)
            self.caminhos_aluno = java_files
            self.alunos_dirs = [pasta_final]
            self.card_aluno.atualizar_status(f"{os.path.basename(pasta_final)} ({len(java_files)} arq.)")

    def sel_conceitos(self):
        # Carrega concepts.md diretamente
        base = os.path.dirname(__file__)
        prompts_dir = os.path.abspath(os.path.join(base, '..', '05-prompts'))
        concepts_path = os.path.join(prompts_dir, 'concepts.md')
        try:
            with open(concepts_path, 'r', encoding='utf-8') as f:
                concepts_text = f.read()
        except Exception:
            messagebox.showerror('Erro', f'Não foi possível ler {concepts_path}')
            return
        # Parse simples dos blocos numerados
        blocks = []
        cur = None
        for line in concepts_text.splitlines():
            m = re.match(r'^(\d+)\.\s*(.*)', line)
            if m:
                if cur:
                    blocks.append(cur)
                cur = {'num': int(m.group(1)), 'title': m.group(2).strip(), 'text': line + '\n'}
            else:
                if cur:
                    cur['text'] += line + '\n'
        if cur:
            blocks.append(cur)
        sel = self._open_concepts_selector(blocks)
        if sel is None:
            return
        selected_nums = [str(blocks[i]['num']) for i in sel]
        self.conceitos_limite = selected_nums
        titles = [blocks[i]['title'] for i in sel]
        status = f"{len(selected_nums)} selecionado(s): " + (", ".join(titles[:3]) + ("..." if len(titles) > 3 else ""))
        self.card_concepts.atualizar_status(status)
    def executar(self):
        # Aceita tanto seleção única de arquivos (`caminhos_aluno`) quanto seleção múltipla de pastas (`alunos_dirs`).
        has_enunciado = bool(self.caminho_enunciado)
        has_single = bool(getattr(self, 'caminhos_aluno', None))
        has_multiple = bool(getattr(self, 'alunos_dirs', None))
        if not has_enunciado or (not has_single and not has_multiple):
            messagebox.showwarning("Aviso", "Por favor, selecione o Enunciado e a Pasta do Aluno (ou a pasta pai com múltiplos alunos).")
            return
        self.confirmado = True
        self.root.destroy()

    def _open_concepts_selector(self, blocks: List[dict]) -> Optional[List[int]]:
        win = tk.Toplevel(self.root)
        win.title('Selecionar conceitos (multi)')
        win.geometry('480x520')
        tk.Label(win, text='Marque os conceitos que devem ser avaliados:').pack(anchor='w', padx=10, pady=(10,0))
        # Área rolável
        container = tk.Frame(win)
        container.pack(fill='both', expand=True, padx=10, pady=8)
        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        vars = []
        for b in blocks:
            var = tk.IntVar(value=0)
            chk = tk.Checkbutton(scroll_frame, text=f"{b['num']}. {b['title']}", variable=var, anchor='w', justify='left')
            chk.pack(anchor='w', fill='x')
            desc = re.sub(r'^\s*\d+\.\s*.*\n', '', b['text'], count=1)
            lbl = tk.Label(scroll_frame, text=desc.strip(), font=('Segoe UI', 9), fg='#374151', wraplength=440, justify='left')
            lbl.pack(anchor='w', padx=20, pady=(0,8))
            vars.append(var)

        result = {'sel': None}
        def on_ok():
            sel = [i for i, v in enumerate(vars) if v.get()]
            result['sel'] = sel
            win.destroy()
        def on_cancel():
            result['sel'] = None
            win.destroy()
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text='OK', command=on_ok).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Cancelar', command=on_cancel).pack(side='left', padx=6)
        self.root.wait_window(win)
        return result['sel']
    def get_data(self):
        self.root.mainloop()
        if not self.confirmado:
            return (None, None, None, None)
        # Retorna: enunciado, gabarito paths, lista de pastas de aluno selecionadas, conceitos
        return (
            self.caminho_enunciado,
            self.caminhos_gabarito,
            getattr(self, 'alunos_dirs', self.caminhos_aluno),
            getattr(self, 'conceitos_limite', None)
        )


# Seleciona os arquivos ao iniciar o script usando a nova interface orientada a objetos
app = InterfaceCorretor()
ENUNCIADO_FILE_PATH, GABARITO_FILE_PATHS, CODIGOS_JAVA_PATHS, CONCEITOS_A_AVALIAR = app.get_data()
if ENUNCIADO_FILE_PATH:
    print(f"Enunciado selecionado: {ENUNCIADO_FILE_PATH}")
    print(f"Gabarito(s) selecionado(s): {GABARITO_FILE_PATHS if GABARITO_FILE_PATHS else 'Nenhum'}")
    print(f"Arquivos de código selecionados: {CODIGOS_JAVA_PATHS}")
    print(f"Conceito limite informado: {CONCEITOS_A_AVALIAR if CONCEITOS_A_AVALIAR else 'Nenhum'}")

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


# --- 2. DEFINIÇÃO DO ESTADO (STATE) DO LANGGRAPH ---
class CorrectionState(TypedDict):
    # Representa o estado do processo de correção.
    enunciado: str
    gabarito: Optional[str]
    codigo_aluno: str
    feedback_bruto: str  # Resultado da LLM (Passo 1/Nó Básico)
    avaliacao_status: str # Status extraído para tomada de decisão futura
    conceitos_limite: Optional[str]

# --- 3. FUNÇÕES UTILITÁRIAS ---

def read_file_content(file_path: str) -> str:
    # Função para ler o conteúdo de um arquivo de forma segura.
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado no caminho: {file_path}")
        exit()
    except Exception as e:
        print(f"Erro ao ler o arquivo {file_path}: {e}")
        exit()

class PromptManager:
    def __init__(self, prompts_dir=None):
        base = os.path.dirname(__file__)
        default = os.path.abspath(os.path.join(base, '..', '05-prompts'))
        self.prompts_dir = prompts_dir or default

    def _load(self, filename: str) -> str:
        path = os.path.join(self.prompts_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    def system_instruction(self) -> str:
        text = self._load('system_prompt.md')
        if not text:
            # fallback curto
            return (
                "Você é um Professor de Programação Orientada a Objetos (POO). "
                "Avalie o código Java do aluno considerando o enunciado."
            )
        return text

    def persona(self) -> str:
        return self._load('persona.md')

    def user_template(self) -> str:
        # Template neutro onde o código e o enunciado serão injetados
        text = self._load('user_template.md')
        if not text:
            # Template por omissão — o código insere os blocos marcados
            return (
                "--- ENUNCIADO DO EXERCÍCIO ---\n{{ENUNCIADO}}\n"
                "--- GABARITO DO PROFESSOR ---```java\n{{GABARITO}}\n```\n"
                "--- CÓDIGO DO ALUNO ---\n```java\n{{CODIGO_ALUNO}}\n```\n"
            )
        return text

    def _parse_concepts(self, concepts_text: str) -> List[dict]:
        # Parseia concepts.md em blocos numerados: [{'num': int, 'title': str, 'text': str}, ...]
        lines = concepts_text.splitlines()
        blocks: List[dict] = []
        cur = None
        for line in lines:
            m = re.match(r'^(\d+)\.\s*(.*)', line)
            if m:
                if cur:
                    blocks.append(cur)
                cur = {'num': int(m.group(1)), 'title': m.group(2).strip(), 'text': line + '\n'}
            else:
                if cur:
                    cur['text'] += line + '\n'
        if cur:
            blocks.append(cur)
        return blocks

    def fill_user_template(self, enunciado: str, gabarito: Optional[str], codigo_aluno: str, conceitos_a_avaliar: Optional[Union[str, List[str]]] = None) -> str:
        template = self.user_template()
        g = gabarito or ""
        result = template.replace("{{ENUNCIADO}}", enunciado).replace("{{GABARITO}}", g).replace("{{CODIGO_ALUNO}}", codigo_aluno)
        # Substitui o placeholder de conceitos por um bloco apropriado.
        if "{{CONCEITOS_A_AVALIAR}}" in result:
            if conceitos_a_avaliar:
                concepts_text = self._load('concepts.md')
                blocks = self._parse_concepts(concepts_text)
                selected_text = ''
                note = ''
                if isinstance(conceitos_a_avaliar, list):
                    sel_nums = set()
                    for v in conceitos_a_avaliar:
                        try:
                            sel_nums.add(int(v))
                        except Exception:
                            for b in blocks:
                                if v.strip().lower() in b['title'].lower():
                                    sel_nums.add(b['num'])
                    for b in blocks:
                        if b['num'] in sel_nums:
                            selected_text += b['text'] + '\n'
                    note = 'Avaliar apenas os conceitos selecionados.'
                else:
                    v = conceitos_a_avaliar.strip()
                    if v.isdigit():
                        n = int(v)
                        for b in blocks:
                            if b['num'] <= n:
                                selected_text += b['text'] + '\n'
                        note = f'Avaliar até: {n} (incluir conceitos 1..{n}).'
                    else:
                        idx = None
                        for b in blocks:
                            if v.lower() in b['title'].lower():
                                idx = b['num']
                                break
                        if idx:
                            for b in blocks:
                                if b['num'] <= idx:
                                    selected_text += b['text'] + '\n'
                            note = f'Avaliar até: {v} (incluir conceitos 1..{idx}).'
                        else:
                            # Fallback: iincluir todos conceitos
                            selected_text = concepts_text
                            note = f'Avaliar até: {v} (não foi possível mapear; incluindo lista completa).'

                concepts_block = "\n-- CONCEITOS (referência) --\n" + selected_text.strip() + "\n\n-- NOTA: " + note + " --\n"
                result = result.replace("{{CONCEITOS_A_AVALIAR}}", concepts_block)
            else:
                result = result.replace("{{CONCEITOS_A_AVALIAR}}", "")
        return result


def _save_prompt_for_analysis(system_instruction: str, user_prompt: str) -> str:
    """Salva `system_instruction` e `user_prompt` em um arquivo .txt para análise.
    Retorna o caminho do ficheiro criado.
    """
    base = os.path.dirname(__file__)
    prompts_dir = os.path.abspath(os.path.join(base, '..', '05-prompts'))
    out_dir = os.path.join(prompts_dir, 'sent_prompts')
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        out_dir = os.path.abspath(os.path.join(base, '..'))

    fname = os.path.join(out_dir, f"prompt_sent_{int(time.time())}.txt")
    try:
        with open(fname, 'w', encoding='utf-8') as f:
            f.write("--- SYSTEM INSTRUCTION ---\n")
            f.write(system_instruction + "\n\n")
            f.write("--- USER PROMPT ---\n")
            f.write(user_prompt + "\n")
    except Exception:
        return ""
    return fname


# --- Função para remover comentários de código Java ---
def remove_java_comments(code: str) -> str:
    """Remove comentários de linha (//) e bloco (/* */) de código Java, e linhas vazias resultantes."""
    # Remove comentários de bloco
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    # Remove comentários de linha
    code = re.sub(r'//.*', '', code)
    # Remove linhas vazias
    code = '\n'.join([linha for linha in code.splitlines() if linha.strip()])
    return code

def format_with_google_java_format(code: str, jar_path: Optional[str] = None) -> str:
    """Formata o código usando google-java-format quando o JAR estiver disponível.

    Procura o JAR nas opções: `jar_path`, `GOOGLE_JAVA_FORMAT_JAR` (env)
    e `06-tools/google-java-format.jar` no repositório.
    """
    if code is None:
        return ""

    # Resolve o caminho do JAR
    candidates = []
    if jar_path:
        candidates.append(jar_path)
    env_jar = os.getenv('GOOGLE_JAVA_FORMAT_JAR')
    if env_jar:
        candidates.append(env_jar)
    repo_tools = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '06-tools', 'google-java-format.jar'))
    candidates.append(repo_tools)
    jar = None
    for c in candidates:
        if c and os.path.isfile(c):
            jar = os.path.abspath(c)
            break

    if not jar:
        return code

    # Grava em arquivo temporário e formata
    with tempfile.NamedTemporaryFile(suffix='.java', delete=False, mode='w', encoding='utf-8') as tf:
        tf.write(code)
        tmpname = tf.name
    try:
        subprocess.run(['java', '-jar', jar, '-i', tmpname], check=True)
        with open(tmpname, 'r', encoding='utf-8') as f:
            formatted = f.read()
        return formatted
    except Exception as e:
        print(f"Aviso: falha ao executar google-java-format ({jar}): {e}")
        return code
    finally:
        try:
            os.unlink(tmpname)
        except Exception:
            pass

def generate_content_with_retry(prompt, system_instruction):
    # Função para chamar a API do Gemini com retries e backoff
    for attempt in range(MAX_RETRIES):
        try:
            config = {
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": JSON_SCHEMA
            }
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config
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
    # Usa PromptManager para carregar system prompt, persona e template do utilizador.
    pm = PromptManager()
    # Carrega o system_instruction e concatena a persona (se existir) para garantir que o modelo recebe ambas.
    system_instruction = pm.system_instruction()
    persona_text = pm.persona()
    if persona_text:
        # Coloca a persona antes da instrução do sistema para dar identidade/contexto consistente ao modelo.
        system_instruction = persona_text + "\n\n" + system_instruction
    conceitos_limite = state.get('conceitos_limite')
    user_prompt = pm.fill_user_template(enunciado, gabarito, codigo_aluno, conceitos_limite)

    # Salva prompt (system + user) para análise local antes de enviar à LLM
    try:
        saved = _save_prompt_for_analysis(system_instruction, user_prompt)
        if saved:
            print(f"Prompt salvo para análise: {saved}")
    except Exception:
        pass
    # Prompt será enviado à LLM

    feedback_json = generate_content_with_retry(user_prompt, system_instruction)
    print("--- LLM RESPONDEU. RETORNANDO AO GRAFO. ---")
    return {
        "feedback_bruto": json.dumps(feedback_json, ensure_ascii=False, indent=2),
        "avaliacao_status": feedback_json["avaliacao"]
    }

def read_and_concat_java_files(file_paths):
    """Lê múltiplos arquivos Java, remove comentários e concatena com delimitadores para o LLM."""
    combined = ""
    for path in file_paths:
        nome = os.path.basename(path)
        conteudo = read_file_content(path)
        conteudo_sem_comentarios = remove_java_comments(conteudo)
        # Tenta formatar com google-java-format se disponível, senão usa código original
        conteudo_sem_comentarios = format_with_google_java_format(conteudo_sem_comentarios)
        combined += f"// --- ARQUIVO INÍCIO: {nome} ---\n"
        combined += conteudo_sem_comentarios.strip() + "\n"
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
    # Se a lista contém pastas (modo lote), não tente abrir diretórios como arquivos.
    if CODIGOS_JAVA_PATHS and isinstance(CODIGOS_JAVA_PATHS, list) and all(os.path.isdir(p) for p in CODIGOS_JAVA_PATHS):
        print("Modo lote detectado: cada item é uma pasta de aluno. O processamento por aluno será feito em sequência.")
        codigo_content = ""
    else:
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
    # Suporta dois modos:
    # - modo único (comportamento original): CODIGOS_JAVA_PATHS é lista de arquivos .java
    # - modo lote: CODIGOS_JAVA_PATHS é lista de pastas de aluno (seleção na UI)
    def normalize_newlines(text):
        return text.replace('\\n', '\n') if text else text

    def save_feedback_json(student_name, feedback_obj):
        base = os.path.dirname(__file__)
        out_dir = os.path.abspath(os.path.join(base, '..', '05-prompts', 'received_responses'))
        os.makedirs(out_dir, exist_ok=True)
        ts = int(time.time())
        fname = os.path.join(out_dir, f"{student_name}_feedback_{ts}.json")
        try:
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(feedback_obj, f, ensure_ascii=False, indent=2)
            print('Resposta salva em:', fname)
        except Exception as e:
            print('Falha ao salvar feedback JSON:', e)

    # Detecta se estamos no modo lote (cada item é uma pasta)
    batch_mode = False
    if CODIGOS_JAVA_PATHS and isinstance(CODIGOS_JAVA_PATHS, list) and all(os.path.isdir(p) for p in CODIGOS_JAVA_PATHS):
        batch_mode = True

    if not batch_mode:
        # Comportamento original (um único conjunto de arquivos já lidos acima)
        TEST_CASE_NAME = "TESTE DE LEITURA DE ARQUIVOS"
        print(f"\nINÍCIO DA EXECUÇÃO DO GRAFO - {TEST_CASE_NAME}")
        print("-" * 80)
        initial_state = {
            "enunciado": enunciado_content,
            "gabarito": gabarito_content,
            "codigo_aluno": codigo_content,
            "feedback_bruto": "",
            "avaliacao_status": "",
            "conceitos_limite": CONCEITOS_A_AVALIAR
        }
        final_state = app.invoke(initial_state)
        print("\n--- RESULTADO FINAL DO GRAFO ---")
        print(f"Feedback da LLM para {TEST_CASE_NAME} (JSON):")
        print(final_state["feedback_bruto"])
        print(f"\nStatus de avaliação: {final_state['avaliacao_status']}")
        print("\n" + "=" * 80)
        print("FIM DA EXECUÇÃO DO GRAFO: PASSO 3 CONCLUÍDO.")
        print("=" * 80)

        # --- GERAÇÃO DO RELATÓRIO HTML ---
        try:
            feedback_json = json.loads(final_state["feedback_bruto"])
        except Exception:
            feedback_json = {"avaliacao": "Erro", "justificativa": "Erro ao decodificar JSON.", "sugestao_correcao": ""}
        enunciado = enunciado_content.strip()
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
    else:
        # Modo lote: iterar por cada pasta de aluno
        print(f"Entrando em modo lote: processando {len(CODIGOS_JAVA_PATHS)} alunos...")
        for sd in CODIGOS_JAVA_PATHS:
            aluno_nome = os.path.basename(sd.rstrip(os.sep))
            print(f"\n--- Aluno: {aluno_nome} ---")
            # Extrai ZIPs se necessário
            try:
                pasta_final = selecionar_pasta_ou_zip(sd, f"aluno_zip_{aluno_nome}_")
                if not pasta_final:
                    pasta_final = sd
            except Exception:
                pasta_final = sd

            java_files = buscar_arquivos_java(pasta_final)
            if not java_files:
                print(f"Nenhum arquivo .java encontrado para {aluno_nome} em {pasta_final}. Pulando.")
                continue

            codigo_content_student = read_and_concat_java_files(java_files)

            initial_state = {
                "enunciado": enunciado_content,
                "gabarito": gabarito_content,
                "codigo_aluno": codigo_content_student,
                "feedback_bruto": "",
                "avaliacao_status": "",
                "conceitos_limite": CONCEITOS_A_AVALIAR
            }
            final_state = app.invoke(initial_state)

            try:
                feedback_json = json.loads(final_state["feedback_bruto"])
            except Exception:
                feedback_json = {"avaliacao": "Erro", "justificativa": "Erro ao decodificar JSON.", "sugestao_correcao": ""}

            # Salva feedback JSON
            save_feedback_json(aluno_nome, feedback_json)

            # Gera relatório por aluno
            enunciado = enunciado_content.strip()
            gabarito = normalize_newlines(gabarito_content.strip()) if gabarito_content else ""
            codigo_aluno = normalize_newlines(codigo_content_student.strip())
            avaliacao = feedback_json.get("avaliacao", "")
            justificativa = feedback_json.get("justificativa", "")
            dica_correcao = feedback_json.get("dica_correcao", "")
            sugestao_correcao = normalize_newlines(feedback_json.get("sugestao_correcao", ""))
            try:
                relatorio_saida = gerar_relatorio_html(
                    enunciado=enunciado,
                    gabarito=gabarito,
                    codigo_aluno=codigo_aluno,
                    avaliacao=avaliacao,
                    justificativa=justificativa,
                    dica_correcao=dica_correcao,
                    sugestao_correcao=sugestao_correcao
                )
                print(f"Relatório HTML gerado para {aluno_nome}: {relatorio_saida}")
            except Exception as e:
                print('Falha ao gerar relatório HTML para', aluno_nome, e)
