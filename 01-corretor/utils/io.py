import os
import zipfile
import tempfile
import shutil
import time
import json
from typing import Optional, List

# Mapeamento temporário -> caminho original (quando extraímos ZIPs)
EXTRACTED_SUBMISSIONS: dict = {}


def _map_extracted_to_original(path: str) -> str:
    """Se `path` está dentro de um diretório temporário extraído, retorna
    o caminho da pasta original selecionada pelo usuário. Caso contrário,
    retorna `path` inalterado.
    """
    try:
        for temp_root, original in EXTRACTED_SUBMISSIONS.items():
            try:
                if os.path.commonpath([os.path.abspath(path), os.path.abspath(temp_root)]) == os.path.abspath(temp_root):
                    return original
            except Exception:
                continue
    except Exception:
        pass
    return path


def select_dir_or_zip(pasta: str, prefixo_temp: str) -> Optional[str]:
    """Se houver um arquivo .zip na `pasta`, extrai para um temp dir e retorna
    a subpasta extraída ou o temp dir; senão retorna a própria `pasta`.
    Retorna None se a seleção for cancelada.
    """
    try:
        arquivos_zip = [f for f in os.listdir(pasta) if f.lower().endswith('.zip')]
    except Exception:
        return None

    if arquivos_zip:
        zip_nome = arquivos_zip[0]
        zip_path = os.path.join(pasta, zip_nome)
        temp_dir = tempfile.mkdtemp(prefix=prefixo_temp)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        try:
            EXTRACTED_SUBMISSIONS[temp_dir] = pasta
        except Exception:
            pass
        # Lista subpastas, ignorando nomes indesejados como '_'
        subdirs = [os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d)) and d != '_']
        if subdirs:
            return subdirs[0]
        # Se só existe a subpasta '_', ignora e retorna o temp_dir para busca na raiz
        return temp_dir
    return pasta


def find_java_files(pasta: str) -> List[str]:
    java_files: List[str] = []
    for root, _, files in os.walk(pasta):
        for f in files:
            if f.endswith('.java'):
                java_files.append(os.path.join(root, f))
    return java_files


def count_java_in_dir_or_zip(pasta: str) -> int:
    """Conta arquivos .java numa pasta. Conta também .java dentro de zips na raiz."""
    total = 0
    try:
        if os.path.isdir(pasta):
            total += len(find_java_files(pasta))
            for fname in os.listdir(pasta):
                if fname.lower().endswith('.zip'):
                    zpath = os.path.join(pasta, fname)
                    try:
                        with zipfile.ZipFile(zpath, 'r') as zf:
                            for info in zf.infolist():
                                if info.filename.endswith('.java'):
                                    total += 1
                    except Exception:
                        pass
    except Exception:
        return 0
    return total


def read_file_content(file_path: str) -> str:
    """Lê arquivo de texto e retorna conteúdo; lança FileNotFoundError se ausente."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def save_feedback_json(student_name: str, feedback_obj: dict, out_dir: Optional[str] = None) -> Optional[str]:
    """Salva o feedback JSON em `out_dir` (por omissão ../05-prompts/received_responses).
    Retorna o caminho do ficheiro salvo ou None em caso de falha.
    """
    base = os.path.dirname(__file__)
    if not out_dir:
        # Projeto raiz: dois níveis acima de 01-corretor
        project_root = os.path.abspath(os.path.join(base, '..', '..'))
        out_dir = os.path.abspath(os.path.join(project_root, '05-prompts', 'received_responses'))
    try:
        os.makedirs(out_dir, exist_ok=True)
        ts = int(time.time())
        fname = os.path.join(out_dir, f"{student_name}_feedback_{ts}.json")
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(feedback_obj, f, ensure_ascii=False, indent=2)
        return fname
    except Exception:
        return None


def resolve_target_dir(pasta_final: Optional[str], sd: Optional[str], codigos_java_paths: Optional[List[str]] = None, enunciado_file_path: Optional[str] = None) -> Optional[str]:
    """Resolve o diretório de destino para salvar relatórios.
    Prioriza `pasta_final` (mapeada se extraída), depois primeira entrada de `codigos_java_paths`,
    depois `sd`, depois diretório do enunciado.
    """
    try:
        if pasta_final:
            mapped = _map_extracted_to_original(pasta_final)
            if mapped and os.path.isdir(mapped):
                return mapped
            if os.path.isdir(pasta_final):
                return pasta_final
        if codigos_java_paths and len(codigos_java_paths) > 0:
            candidate = os.path.dirname(codigos_java_paths[0])
            if os.path.isdir(candidate):
                return candidate
        if sd and os.path.isdir(sd):
            return sd
        if enunciado_file_path:
            d = os.path.dirname(enunciado_file_path)
            if os.path.isdir(d):
                return d
    except Exception:
        pass
    return None


def copy_report_to_student(relatorio_saida: str, target_dir: Optional[str]) -> bool:
    """Copia `relatorio_saida` para `target_dir` (retorna True se copiado).
    """
    if not target_dir:
        return False
    try:
        dst = os.path.join(target_dir, os.path.basename(relatorio_saida))
        shutil.copy(relatorio_saida, dst)
        return True
    except Exception:
        return False
