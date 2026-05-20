import os
import re
from typing import List, Optional


import tkinter as tk
from tkinter import filedialog, messagebox

from utils.io import select_dir_or_zip, find_java_files, count_java_in_dir_or_zip


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
        header = tk.Frame(self.root, bg="#f8fafc", pady=12)
        header.pack(fill="x")
        tk.Label(header, text="Corretor de Projetos POO", font=("Segoe UI", 16, "bold"), fg="#0f172a", bg="#f8fafc").pack()
        self.main_container = tk.Frame(self.root, bg="#f8fafc", padx=30)
        self.main_container.pack(fill="both", expand=True)
        self.card_enunc = CardSelecao(self.main_container, "1. Enunciado", "Instruções (Markdown ou Texto)", self.sel_enunciado)
        self.card_enunc.pack(fill="x", pady=6)
        self.card_gaba = CardSelecao(self.main_container, "2. Gabarito", "Pasta com ficheiros .java (Opcional)", self.sel_gabarito)
        self.card_gaba.pack(fill="x", pady=6)
        self.card_aluno = CardSelecao(self.main_container, "3. Código do Aluno", "Pasta com o projeto .java do aluno", self.sel_aluno)
        self.card_aluno.pack(fill="x", pady=6)
        self.card_concepts = CardSelecao(self.main_container, "4. Conceitos a Avaliar", "Escolher quais conceitos incluir na avaliação (Opcional)", self.sel_conceitos)
        self.card_concepts.pack(fill="x", pady=6)
        controls_frame = tk.Frame(self.main_container, bg="#f8fafc")
        controls_frame.pack(fill='x', pady=(4, 8))

        self.save_report_var = tk.IntVar(value=1)
        self.chk_save_report = tk.Checkbutton(
            controls_frame, text="Salvar relatório na pasta do aluno", variable=self.save_report_var,
            bg="#f8fafc", anchor="w", justify='left'
        )
        self.chk_save_report.pack(anchor='w', padx=6, pady=(0,4))

        self.mode_var = tk.IntVar(value=1)
        frame_mode = tk.Frame(controls_frame, bg="#f8fafc")
        frame_mode.pack(anchor='w', padx=6, pady=(0,4))
        tk.Label(frame_mode, text="Modo de retorno:", bg="#f8fafc").pack(side='left')
        tk.Radiobutton(frame_mode, text="Dar resposta", variable=self.mode_var, value=1, bg="#f8fafc").pack(side='left', padx=6)
        tk.Radiobutton(frame_mode, text="Apenas dicas", variable=self.mode_var, value=0, bg="#f8fafc").pack(side='left', padx=6)

        footer = tk.Frame(self.main_container, bg="#f8fafc", pady=6)
        footer.pack(fill="x", pady=(4, 8))
        self.btn_exec = tk.Button(
            footer, text="EXECUTAR ANÁLISE", command=self.executar,
            font=("Segoe UI", 12, "bold"), bg="#10b981", fg="#ffffff",
            relief="flat", cursor="hand2", width=30, padx=6, pady=8,
            activebackground="#059669"
        )
        self.btn_exec.pack(padx=20, pady=(4,8))

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
        pasta_final = select_dir_or_zip(pasta, "gabarito_zip_")
        if not pasta_final:
            return
        self.caminhos_gabarito = find_java_files(pasta_final)
        self.card_gaba.atualizar_status(f"{os.path.basename(pasta_final)} ({len(self.caminhos_gabarito)} arq.)")

    def sel_aluno(self):
        initialdir = None
        if self.caminhos_gabarito:
            first_gabarito = self.caminhos_gabarito[0]
            initialdir = os.path.dirname(os.path.dirname(first_gabarito))

        pasta = filedialog.askdirectory(title="Selecionar Pasta do Aluno (ou pasta com vários alunos)", initialdir=initialdir)
        if not pasta:
            return
        pasta_final = select_dir_or_zip(pasta, "aluno_zip_")
        if not pasta_final:
            return

        subdirs = [os.path.join(pasta_final, d) for d in os.listdir(pasta_final) if os.path.isdir(os.path.join(pasta_final, d))]
        if subdirs:
            blocks = []
            for i, d in enumerate(subdirs, start=1):
                blocks.append({'num': i, 'title': os.path.basename(d), 'text': os.path.basename(d) + '\n'})
            sel = self._open_concepts_selector(blocks, title='Selecionar alunos', prompt_text='Marque os alunos que deseja processar:')
            if sel is None:
                return
            selected_dirs = [subdirs[i] for i in sel]
            self.alunos_dirs = selected_dirs
            total_files = sum(count_java_in_dir_or_zip(sd) for sd in selected_dirs)
            self.card_aluno.atualizar_status(f"{len(selected_dirs)} alunos selecionados ({total_files} arquivos .java)")
        else:
            java_files = find_java_files(pasta_final)
            self.caminhos_aluno = java_files
            self.alunos_dirs = [pasta_final]
            self.card_aluno.atualizar_status(f"{os.path.basename(pasta_final)} ({len(java_files)} arq.)")

    def sel_conceitos(self):
        # Projeto raiz: dois níveis acima de 01-corretor
        base = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(base, '..', '..'))
        prompts_dir = os.path.abspath(os.path.join(project_root, '05-prompts'))
        concepts_path = os.path.join(prompts_dir, 'concepts.md')
        try:
            with open(concepts_path, 'r', encoding='utf-8') as f:
                concepts_text = f.read()
        except Exception:
            messagebox.showerror('Erro', f'Não foi possível ler {concepts_path}')
            return
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
        has_enunciado = bool(self.caminho_enunciado)
        has_single = bool(getattr(self, 'caminhos_aluno', None))
        has_multiple = bool(getattr(self, 'alunos_dirs', None))
        if not has_enunciado or (not has_single and not has_multiple):
            messagebox.showwarning("Aviso", "Por favor, selecione o Enunciado e a Pasta do Aluno (ou a pasta pai com múltiplos alunos).")
            return
        self.confirmado = True
        self.root.destroy()

    def _open_concepts_selector(self, blocks: List[dict], title: str = 'Selecionar conceitos', prompt_text: str = 'Marque os conceitos que devem ser avaliados:') -> Optional[List[int]]:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry('480x520')
        tk.Label(win, text=prompt_text).pack(anchor='w', padx=10, pady=(10,0))
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
        return (
            self.caminho_enunciado,
            self.caminhos_gabarito,
            getattr(self, 'alunos_dirs', self.caminhos_aluno),
            getattr(self, 'conceitos_limite', None)
        )
