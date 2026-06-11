import os
import time
import re
from typing import List, Optional, Union



class PromptManager:
    def __init__(self, prompts_dir=None):
        base = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(base, '..', '..'))
        default = os.path.abspath(os.path.join(project_root, '05-prompts'))
        self.prompts_dir = prompts_dir or default

    def _load(self, filename: str) -> str:
        path = os.path.join(self.prompts_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    def system_instruction(self, mode: Optional[str] = None) -> str:
        text = self._load('system_prompt.md')
        if not text:
            text = (
                "Você é um Professor de Programação Orientada a Objetos (POO). "
                "Avalie o código Java do aluno considerando o enunciado."
            )
        persona_text = self.persona()
        if persona_text:
            return persona_text + "\n\n" + text
        return text

    def persona(self) -> str:
        return self._load('persona.md')

    def user_template(self) -> str:
        text = self._load('user_template.md')
        if not text:
            return (
                "--- ENUNCIADO DO EXERCÍCIO ---\n{{ENUNCIADO}}\n"
                "--- GABARITO DO PROFESSOR ---```java\n{{GABARITO}}\n```\n"
                "--- CÓDIGO DO ALUNO ---\n```java\n{{CODIGO_ALUNO}}\n```\n"
            )
        return text

    def _parse_concepts(self, concepts_text: str) -> List[dict]:
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
                            selected_text = concepts_text
                            note = f'Avaliar até: {v} (não foi possível mapear; incluindo lista completa).'

                concepts_block = "\n-- CONCEITOS (referência) --\n" + selected_text.strip() + "\n\n-- NOTA: " + note + " --\n"
                result = result.replace("{{CONCEITOS_A_AVALIAR}}", concepts_block)
            else:
                result = result.replace("{{CONCEITOS_A_AVALIAR}}", "")
        return result


def _save_prompt_for_analysis(system_instruction: str, user_prompt: str) -> str:
    base = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(base, '..', '..'))
    prompts_dir = os.path.abspath(os.path.join(project_root, '05-prompts'))
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
