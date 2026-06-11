import os
import time
import json
import webbrowser
from typing import TypedDict, Optional, List

import tkinter as tk
from tkinter import messagebox

from views.ui import InterfaceCorretor

from dotenv import load_dotenv
from google import genai
from langgraph.graph import StateGraph, END

from controllers.prompts import PromptManager, _save_prompt_for_analysis
from controllers.llm import generate_content_with_retry, MODEL_NAME, MAX_RETRIES
from utils.io import (
    select_dir_or_zip,
    find_java_files,
    read_file_content,
    save_feedback_json,
    resolve_target_dir,
    copy_report_to_student,
)
from utils.formatters import read_and_concat_java_files
from views.relatorio_html import gerar_relatorio_html

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


# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()


def _show_fatal_error(title: str, message: str) -> None:
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message, parent=root)
        root.destroy()
    except Exception:
        print(f"{title}: {message}")

# --- 1. CONFIGURAÇÃO E AUTENTICAÇÃO DO GEMINI ---
API_KEY = os.getenv("GEMINI_API_KEY")

try:
    if not API_KEY:
        raise ValueError("Chave API não encontrada.")
    client = genai.Client(api_key=API_KEY)
except ValueError:
    _show_fatal_error(
        "Chave da API ausente",
        "A variável GEMINI_API_KEY não foi encontrada. Configure a chave no arquivo .env e tente novamente.",
    )
    raise SystemExit(1)
except Exception as e:
    _show_fatal_error(
        "Erro ao inicializar o Gemini",
        f"Não foi possível iniciar o cliente Gemini: {e}",
    )
    raise SystemExit(1)

MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 5


# --- COMPONENTES DA INTERFACE ---

# Seleciona os arquivos ao iniciar o script usando a nova interface orientada a objetos
ui = InterfaceCorretor()
ENUNCIADO_FILE_PATH, GABARITO_FILE_PATHS, CODIGOS_JAVA_PATHS, CONCEITOS_A_AVALIAR = ui.get_data()
# Lê a preferência do usuário sobre salvar relatórios (valor lido uma vez antes de sobrescrever variáveis)
try:
    save_var = getattr(ui, 'save_report_var', None)
    if save_var is None:
        SAVE_REPORT_ENABLED = True
    else:
        SAVE_REPORT_ENABLED = bool(save_var.get())
except Exception:
    SAVE_REPORT_ENABLED = True
# Lê a preferência do usuário sobre o modo de correção (resolutivo = dar resposta; scaffolding = apenas dicas)
try:
    mode_var = getattr(ui, 'mode_var', None)
    if mode_var is None:
        MODO_CORRECAO = 'resolutive'
    else:
        MODO_CORRECAO = 'resolutive' if mode_var.get() else 'scaffolding'
except Exception:
    MODO_CORRECAO = 'resolutive'
if ENUNCIADO_FILE_PATH:
    print(f"Enunciado selecionado: {ENUNCIADO_FILE_PATH}")
    print(f"Gabarito(s) selecionado(s): {GABARITO_FILE_PATHS if GABARITO_FILE_PATHS else 'Nenhum'}")
    print(f"Arquivos de código selecionados: {CODIGOS_JAVA_PATHS}")
    print(f"Conceito limite informado: {CONCEITOS_A_AVALIAR if CONCEITOS_A_AVALIAR else 'Nenhum'}")


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
# As funções de leitura e manipulação de arquivos são fornecidas pelo módulo `io.py` importado acima.

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
    # Carrega a instrução do sistema (já inclui `persona` quando presente)
    system_instruction = pm.system_instruction(state.get('modo_correcao'))
    conceitos_limite = state.get('conceitos_limite')

    # O conteúdo já chega pré-processado por read_and_concat_java_files.
    codigo_aluno_fmt = codigo_aluno or ""
    gabarito_fmt = gabarito or ""

    user_prompt = pm.fill_user_template(enunciado, gabarito_fmt, codigo_aluno_fmt, conceitos_limite)

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

# `read_and_concat_java_files`, `remove_java_comments` and `format_with_google_java_format`
# são importados de `formatters.py` acima.

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
        gabarito_content = read_and_concat_java_files(GABARITO_FILE_PATHS, source_group="gabarito")
    else:
        gabarito_content = None
    print(f"[PASSO 3] Lendo arquivos de código do aluno: {CODIGOS_JAVA_PATHS}")
    # Se a lista contém pastas (modo lote), não tente abrir diretórios como arquivos.
    if CODIGOS_JAVA_PATHS and isinstance(CODIGOS_JAVA_PATHS, list) and all(os.path.isdir(p) for p in CODIGOS_JAVA_PATHS):
        print("Modo lote detectado: cada item é uma pasta de aluno. O processamento por aluno será feito em sequência.")
        codigo_content = ""
    else:
        codigo_content = read_and_concat_java_files(CODIGOS_JAVA_PATHS, source_group="aluno")
    print("\n--- Conteúdo do Código Lido (Amostra) ---")
    print(codigo_content.strip()[:300] + '...')
    print("-" * 40)
    # 5.2. Inicialização e Compilação do Grafo
    workflow = StateGraph(CorrectionState)
    workflow.add_node("correcao", correction_node)
    workflow.set_entry_point("correcao")
    workflow.add_edge("correcao", END)
    graph = workflow.compile()
    # 5.3. Execução do LangGraph com o Conteúdo Lido
    # Suporta dois modos:
    # - modo único (comportamento original): CODIGOS_JAVA_PATHS é lista de arquivos .java
    # - modo lote: CODIGOS_JAVA_PATHS é lista de pastas de aluno (seleção na UI)
    def normalize_newlines(text):
        return text.replace('\\n', '\n') if text else text

    # `save_feedback_json` é provido por `io.py` (importado no topo). Use-o diretamente.

    # Verifica se a opção de salvar relatórios na pasta do aluno está habilitada (lida da UI)
    def should_save_reports() -> bool:
        try:
            return bool(SAVE_REPORT_ENABLED)
        except Exception:
            return True

    # Função para resolver o diretório alvo para salvar o relatório.
    # `resolve_target_dir` é provido por `io.py` (importado no topo). Use-o diretamente.

    # `copy_report_to_student` é provido por `io.py` (importado no topo). Use-o diretamente.

    # Detecta se estamos no modo lote (cada item é uma pasta)
    batch_mode = False
    # Modo lote: ativado sempre que `CODIGOS_JAVA_PATHS` for uma lista de diretórios
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
            "conceitos_limite": CONCEITOS_A_AVALIAR,
            "modo_correcao": MODO_CORRECAO
        }
        final_state = graph.invoke(initial_state)
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

        # Salva o feedback bruto retornado pela LLM para auditoria em 05-prompts/received_responses
        try:
            # Gera um nome identificador baseado no enunciado ou timestamp
            try:
                enunciado_id = os.path.splitext(os.path.basename(ENUNCIADO_FILE_PATH))[0]
            except Exception:
                enunciado_id = f"single_{int(time.time())}"
            saved_path = save_feedback_json(enunciado_id, feedback_json)
            if saved_path:
                print(f"Feedback salvo em: {saved_path}")
            else:
                print("Falha ao salvar feedback em received_responses.")
        except Exception:
            print('Erro ao tentar salvar feedback (single run).')

        # Se o usuário escolheu modo 'scaffolding' (apenas dicas), força sugestao_correcao vazia no relatório
        try:
            if MODO_CORRECAO == 'scaffolding' and isinstance(feedback_json, dict):
                feedback_json['sugestao_correcao'] = ""
        except Exception:
            pass
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
        # Também salva uma cópia do relatório na mesma pasta onde os arquivos do aluno foram lidos
        try:
            if not should_save_reports():
                print('Opção de salvar relatório na pasta do código desativada; não copiando relatório.')
            else:
                target = resolve_target_dir(None, None, CODIGOS_JAVA_PATHS, ENUNCIADO_FILE_PATH)
                copy_report_to_student(relatorio_saida, target)
        except Exception as e:
            print('Falha ao copiar relatório para a pasta do aluno:', e)
    else:
        # Modo lote: iterar por cada pasta de aluno
        print(f"Entrando em modo lote: processando {len(CODIGOS_JAVA_PATHS)} alunos...")
        for sd in CODIGOS_JAVA_PATHS:
            pasta_resolvida = resolve_target_dir(sd, sd)
            aluno_nome = os.path.basename(os.path.abspath(pasta_resolvida)) if pasta_resolvida else os.path.basename(sd.rstrip(os.sep))
            print(f"\n--- Aluno: {aluno_nome} ---")
            # Extrai ZIPs se necessário
            try:
                pasta_final = select_dir_or_zip(sd, f"aluno_zip_{aluno_nome}_")
                if not pasta_final:
                    pasta_final = sd
            except Exception:
                pasta_final = sd

            target_dir = resolve_target_dir(pasta_final, sd)
            if target_dir:
                aluno_nome = os.path.basename(os.path.abspath(target_dir))

            java_files = find_java_files(pasta_final)
            if not java_files:
                print(f"Nenhum arquivo .java encontrado para {aluno_nome} em {pasta_final}. Pulando.")
                continue

            codigo_content_student = read_and_concat_java_files(java_files, source_group=aluno_nome)

            initial_state = {
                "enunciado": enunciado_content,
                "gabarito": gabarito_content,
                "codigo_aluno": codigo_content_student,
                "feedback_bruto": "",
                "avaliacao_status": "",
                "conceitos_limite": CONCEITOS_A_AVALIAR,
                "modo_correcao": MODO_CORRECAO
            }
            final_state = graph.invoke(initial_state)

            try:
                feedback_json = json.loads(final_state["feedback_bruto"])
            except Exception:
                feedback_json = {"avaliacao": "Erro", "justificativa": "Erro ao decodificar JSON.", "sugestao_correcao": ""}

            # Honra o modo de correção: se scaffolding, removemos a sugestao de correção antes do relatório
            try:
                if MODO_CORRECAO == 'scaffolding' and isinstance(feedback_json, dict):
                    feedback_json['sugestao_correcao'] = ""
            except Exception:
                pass

            # Salva feedback JSON
            saved = save_feedback_json(aluno_nome, feedback_json)
            if saved:
                print(f"Feedback salvo em: {saved}")
            else:
                print(f"Falha ao salvar feedback para {aluno_nome} em received_responses.")

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
                    sugestao_correcao=sugestao_correcao,
                    titulo=aluno_nome,
                )
                print(f"Relatório HTML gerado para {aluno_nome}: {relatorio_saida}")
                # Copia o relatório gerado para a pasta do aluno processado (se habilitado)
                try:
                    if not should_save_reports():
                        print('Opção de salvar relatório na pasta do código desativada; não copiando relatório para este aluno.')
                    else:
                        copy_report_to_student(relatorio_saida, target_dir)
                except Exception as e:
                    print('Falha ao copiar relatório para a pasta do aluno:', e)
            except Exception as e:
                print('Falha ao gerar relatório HTML para', aluno_nome, e)
