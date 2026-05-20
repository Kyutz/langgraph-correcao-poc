import os
import subprocess
import tempfile
from typing import List, Optional


def remove_java_comments(code: str) -> str:
    if not code:
        return ""

    out_chars = []
    i = 0
    n = len(code)

    def is_escaped(pos):
        cnt = 0
        j = pos - 1
        while j >= 0 and code[j] == '\\':
            cnt += 1
            j -= 1
        return (cnt % 2) == 1

    while i < n:
        ch = code[i]
        nxt = code[i+1] if i+1 < n else ''

        if ch == '"':
            out_chars.append(ch)
            i += 1
            while i < n:
                out_chars.append(code[i])
                if code[i] == '"' and not is_escaped(i):
                    i += 1
                    break
                i += 1
            continue

        if ch == "'":
            out_chars.append(ch)
            i += 1
            while i < n:
                out_chars.append(code[i])
                if code[i] == "'" and not is_escaped(i):
                    i += 1
                    break
                i += 1
            continue

        if ch == '/' and nxt == '/':
            i += 2
            while i < n and code[i] not in ('\n', '\r'):
                i += 1
            continue

        if ch == '/' and nxt == '*':
            i += 2
            depth = 1
            while i < n and depth > 0:
                if code[i] == '/' and i+1 < n and code[i+1] == '*':
                    depth += 1
                    i += 2
                elif code[i] == '*' and i+1 < n and code[i+1] == '/':
                    depth -= 1
                    i += 2
                else:
                    i += 1
            continue

        out_chars.append(ch)
        i += 1

    result = ''.join(out_chars)
    lines = [ln for ln in result.splitlines() if ln.strip()]
    return '\n'.join(lines)


def format_with_google_java_format(code: str, jar_path: Optional[str] = None) -> str:
    if code is None:
        return ""

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

    with tempfile.NamedTemporaryFile(suffix='.java', delete=False, mode='w', encoding='utf-8') as tf:
        tf.write(code)
        tmpname = tf.name
    try:
        subprocess.run(['java', '-jar', jar, '-i', tmpname], check=True)
        with open(tmpname, 'r', encoding='utf-8') as f:
            formatted = f.read()
        return formatted
    except Exception:
        return code
    finally:
        try:
            os.unlink(tmpname)
        except Exception:
            pass


def read_and_concat_java_files(file_paths: List[str]) -> str:
    combined = ""
    for path in file_paths:
        nome = os.path.basename(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except Exception:
            conteudo = ''
        try:
            formatted = format_with_google_java_format(conteudo)
        except Exception:
            formatted = conteudo
        conteudo_sem_comentarios = remove_java_comments(formatted)
        combined += f"// --- ARQUIVO INÍCIO: {nome} ---\n"
        combined += conteudo_sem_comentarios.strip() + "\n"
        combined += f"// --- ARQUIVO FIM: {nome} ---\n\n"
    return combined
