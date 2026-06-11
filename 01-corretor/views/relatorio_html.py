import os
from datetime import datetime
from typing import Optional


def gerar_relatorio_html(
  enunciado,
  gabarito,
  codigo_aluno,
  avaliacao,
  justificativa,
  dica_correcao,
  sugestao_correcao,
  pasta_relatorios=None,
  titulo: Optional[str] = None,
):
    """
    Gera um relatório HTML e salva na pasta relatorios/ com data e hora no nome.
    Retorna o caminho do arquivo gerado.
    """
    # Define a cor do badge de status
    cor = "bg-gray-400"
    if avaliacao == "Certo":
        cor = "bg-green-600"
    elif avaliacao == "Errado":
        cor = "bg-red-600"
    elif avaliacao == "Parcialmente Certo":
        cor = "bg-yellow-500"

    title_text = f"Relatório de Correção - {titulo}" if titulo else "Relatório de Correção - LangGraph"

    # Prepara a justificativa para exibição em HTML (substituindo quebras de linha)
    def render_markdown_preserve_code(text: str) -> str:
      if not text:
        return ""
      import re
      code_blocks = []
      def _code_repl(m):
        code_blocks.append(m.group(0))
        return f"@@CODE_BLOCK_{len(code_blocks)-1}@@"

      text_wo_code = re.sub(r'```[\s\S]*?```', _code_repl, text)

      # Tenta usar biblioteca de markdown se disponível
      try:
        import markdown as _md
        rendered = _md.markdown(text_wo_code)
      except Exception:
        rendered = text_wo_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
        rendered = re.sub(r"\*(.+?)\*", r"<em>\1</em>", rendered)
        rendered = rendered.replace('\n', '<br>')

      for i, cb in enumerate(code_blocks):
        inner = re.sub(r'^```\w*\n|\n```$', '', cb)
        inner_esc = inner.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        code_html = f"<pre class=\"!bg-transparent\"><code>{inner_esc}</code></pre>"
        rendered = rendered.replace(f"@@CODE_BLOCK_{i}@@", code_html)
      return rendered

    justificativa_html = render_markdown_preserve_code(justificativa)

    # Mostra o enunciado como texto bruto do .md, sem reescrever listas ou markdown
    enunciado_html_content = (
      enunciado.replace('&', '&amp;')
      .replace('<', '&lt;')
      .replace('>', '&gt;')
      .replace('\r', '')
    )
    enunciado_html = f'''<div style="max-height:220px;overflow:auto;white-space:pre-wrap;word-break:break-word;font-style:normal;">{enunciado_html_content}</div>'''

    # Função auxiliar para dividir blocos por arquivo
    def split_java_blocks(conteudo):
      import re
      # Remove tags markdown ```java e ```
      conteudo = re.sub(r'^```java\s*|```$', '', conteudo.strip(), flags=re.MULTILINE)
      padrao = re.compile(r"// --- ARQUIVO INÍCIO: (.*?) ---\n(.*?)// --- ARQUIVO FIM: \\1 ---", re.DOTALL)
      padrao2 = re.compile(r"// --- ARQUIVO INÍCIO: (.*?) ---\n(.*?)// --- ARQUIVO FIM: \1 ---", re.DOTALL)
      blocos = padrao2.findall(conteudo)
      if not blocos:
        blocos = padrao.findall(conteudo)
      if blocos:
        return [(nome.strip(), codigo.strip()) for nome, codigo in blocos]
      else:
        return [(None, conteudo.strip())] if conteudo.strip() else []

    # Bloco do gabarito
    gabarito_html = ""
    if gabarito:
        blocos = split_java_blocks(gabarito)
        blocos_html = ""
        for idx, (nome, codigo) in enumerate(blocos):
            code_id = f"gabarito-code-{idx}"
            nome_html = f'<div class="font-mono text-xs text-slate-500 mb-1">{nome}</div>' if nome else ''
            codigo_escapado = (codigo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\r', ''))
            blocos_html += f'''<div class="mb-4"><div class="flex items-center justify-between mb-1">{nome_html}<button class="px-2 py-1 text-xs rounded bg-slate-200 hover:bg-slate-300 font-mono copy-btn" data-target="{code_id}">Copiar código</button></div><div class="scroll-block rounded-xl"><pre class="!bg-transparent"><code class="language-java" id="{code_id}" style="white-space: pre !important;">{codigo_escapado}</code></pre></div></div>'''
        gabarito_html = f'''
          <details id="gabarito" class="rounded-xl border border-slate-200 bg-slate-50 mb-6">
          <summary class="cursor-pointer px-4 py-3 text-base font-bold text-slate-700 select-none flex items-center">Gabarito do Professor</summary>
          <div class="m-4">{blocos_html}</div>
        </details>'''

    # Bloco da sugestão de correção (pode ter múltiplos arquivos)
    sugestao_html = ""
    if sugestao_correcao and sugestao_correcao.strip() and (avaliacao != "Certo"):
        blocos = split_java_blocks(sugestao_correcao)
        blocos_html = ""
        for idx, (nome, codigo) in enumerate(blocos):
            code_id = f"sugestao-code-{idx}"
            nome_html = f'<div class="font-mono text-xs text-green-700 mb-1">{nome}</div>' if nome else ''
            codigo_escapado = (codigo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\r', ''))
            blocos_html += f'''<div class="mb-4"><div class="flex items-center justify-between mb-1">{nome_html}<button class="px-2 py-1 text-xs rounded bg-green-200 hover:bg-green-300 font-mono copy-btn" data-target="{code_id}">Copiar código</button></div><div class="scroll-block-sugestao rounded-xl"><pre class="!bg-transparent"><code class="language-java" id="{code_id}" style="white-space: pre !important;">{codigo_escapado}</code></pre></div></div>'''
        sugestao_html = f'''
          <details id="sugestao" class="rounded-xl border border-green-100 bg-green-50">
          <summary class="cursor-pointer px-4 py-3 text-base font-bold text-green-800 select-none flex items-center">Sugestão de Correção</summary>
          <div class="m-4">{blocos_html}</div>
        </details>'''
    # Se não houver sugestão ou código já está certo, não mostra bloco

    # Bloco do aluno (pode ter múltiplos arquivos)
    aluno_html = ""
    blocos = split_java_blocks(codigo_aluno)
    blocos_html = ""
    for idx, (nome, codigo) in enumerate(blocos):
        code_id = f"aluno-code-{idx}"
        nome_html = f'<div class="font-mono text-xs text-slate-700 mb-1">{nome}</div>' if nome else ''
        codigo_escapado = (codigo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\r', ''))
        blocos_html += f'''<div class="mb-4"><div class="flex items-center justify-between mb-1">{nome_html}<button class="px-2 py-1 text-xs rounded bg-slate-200 hover:bg-slate-300 font-mono copy-btn" data-target="{code_id}">Copiar código</button></div><div class="scroll-block rounded-xl"><pre class="!bg-transparent"><code class="language-java" id="{code_id}" style="white-space: pre !important;">{codigo_escapado}</code></pre></div></div>'''
    aluno_html = f'''
      <details id="aluno" class="rounded-xl border border-slate-200 bg-slate-50">
      <summary class="cursor-pointer px-4 py-3 text-base font-bold text-slate-700 select-none flex items-center">Código do Aluno</summary>
      <div class="m-4">{blocos_html}</div>
    </details>'''

    # Bloco da dica de correção (texto pedagógico, sem código)
    dica_correcao_html = ""
    if dica_correcao and dica_correcao.strip():
        dica_esc = render_markdown_preserve_code(dica_correcao)
        dica_correcao_html = f'''
    <details id="dica_correcao" open class="rounded-xl border border-amber-100 bg-amber-50">
      <summary class="cursor-pointer px-4 py-3 text-base font-bold text-amber-800 select-none flex items-center">Dica de Correção
        <button class="ml-4 px-2 py-1 text-xs rounded bg-amber-200 hover:bg-amber-300 font-mono copy-btn" data-target="dica-correcao-text">Copiar dica</button>
      </summary>
      <div class="text-amber-900 leading-relaxed px-4 pb-4" id="dica-correcao-text">{dica_esc}</div>
    </details>'''

    html_final = f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_text}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
  <style>
    pre code {{ border-radius: 0.75rem !important; white-space: pre !important; }}
    body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}
    .sidebar-link.active {{ background: #e0e7ef; font-weight: bold; }}
    .sidebar-link:hover {{ background: #e0e7ef; }}
    .sidebar {{ position: fixed; top: 0; left: 0; height: 100vh; width: 220px; background: #f1f5f9; border-right: 1px solid #e2e8f0; z-index: 40; padding-top: 80px; }}
    @media (max-width: 900px) {{ .sidebar {{ display: none; }} }}
    .main-content {{ margin-left: 240px; }}
    @media (max-width: 900px) {{ .main-content {{ margin-left: 0; }} }}
    .sticky-header {{ position: sticky; top: 0; z-index: 30; background: #fff; border-bottom: 1px solid #e2e8f0; }}
    .scroll-block {{ max-height: 400px; overflow: auto; background: #0f172a10; }}
    .scroll-block-sugestao {{ max-height: 600px; overflow: auto; background: #0f172a10; }}
    .float-top-btn {{ position: fixed; bottom: 32px; right: 32px; z-index: 50; background: #2563eb; color: #fff; border-radius: 9999px; padding: 0.75rem 1.25rem; font-weight: bold; box-shadow: 0 2px 8px #0002; border: none; cursor: pointer; transition: background 0.2s; }}
    .float-top-btn:hover {{ background: #1d4ed8; }}
  </style>
</head>
<body class="bg-slate-50 min-h-screen pb-12">
  <nav class="sidebar hidden md:block">
    <ul class="space-y-2 px-4">
      <li><a href="#enunciado" class="sidebar-link block rounded-lg px-4 py-2 text-slate-700">Enunciado</a></li>
      <li><a href="#gabarito" class="sidebar-link block rounded-lg px-4 py-2 text-slate-700">Gabarito</a></li>
      <li><a href="#aluno" class="sidebar-link block rounded-lg px-4 py-2 text-slate-700">Código do Aluno</a></li>
      <li><a href="#justificativa" class="sidebar-link block rounded-lg px-4 py-2 text-slate-700">Feedback</a></li>
      <li><a href="#dica_correcao" class="sidebar-link block rounded-lg px-4 py-2 text-slate-700">Dica de Correção</a></li>
      <li><a href="#sugestao" class="sidebar-link block rounded-lg px-4 py-2 text-slate-700">Sugestão</a></li>
    </ul>
  </nav>
  <div class="main-content max-w-4xl mx-auto p-6 mt-8 bg-white rounded-3xl shadow-xl border border-gray-100">
    <div class="sticky-header flex justify-between items-center mb-8 pb-4 pt-2 px-2">
        <h1 class="text-3xl font-extrabold text-slate-800 tracking-tight">{title_text}</h1>
        <span class="px-4 py-1.5 rounded-full text-white text-sm font-bold shadow-sm {cor}">
            {avaliacao.upper()}
        </span>
    </div>
    <div class="space-y-8">
        <div id="enunciado">
          <h2 class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-2">Enunciado</h2>
          <div class="bg-slate-50 p-4 rounded-lg text-slate-700 text-sm border-l-4 border-slate-300 italic">{enunciado_html}</div>
        </div>

        <details id="justificativa" open class="rounded-xl border border-blue-100 bg-blue-50">
          <summary class="cursor-pointer px-4 py-3 text-base font-bold text-blue-800 select-none flex items-center">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"></path></svg>
            Justificativa Pedagógica
            <button class="ml-4 px-2 py-1 text-xs rounded bg-blue-200 hover:bg-blue-300 font-mono copy-btn" data-target="justificativa-text">Copiar feedback</button>
          </summary>
          <div class="text-blue-900 leading-relaxed px-4 pb-4" id="justificativa-text">{justificativa_html}</div>
        </details>

        {dica_correcao_html}

        {aluno_html}

        {gabarito_html}

        {sugestao_html}
    </div>
    <footer class="text-center text-xs text-gray-400 mt-12 pt-6 border-t">
        Gerado automaticamente por LangGraph Corretor • {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </footer>
  </div>
  <button onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});" class="float-top-btn" title="Ir para o topo">↑ Topo</button>
  <script>hljs.highlightAll();</script>
  <script>
    // Sidebar highlight
    const links = document.querySelectorAll('.sidebar-link');
    const sections = ['enunciado','justificativa','dica_correcao','aluno','gabarito','sugestao'].map(id => document.getElementById(id));
    function highlightSidebar(idx) {{
      links.forEach(function(l, i) {{ l.classList.toggle('active', i === idx); }});
    }}
    window.addEventListener('scroll', () => {{
      var idx = 0;
      for (var i = 0; i < sections.length; i++) {{
        if (sections[i] && sections[i].getBoundingClientRect().top - 80 < 0) idx = i;
      }}
      highlightSidebar(idx);
    }});
    // Destaca ao clicar no menu lateral
    links.forEach(function(link, i) {{
      link.addEventListener('click', function() {{
        setTimeout(function() {{ highlightSidebar(i); }}, 10);
      }});
    }});

    // Copy button logic
    document.querySelectorAll('.copy-btn').forEach(btn => {{
      btn.addEventListener('click', function(e) {{
        e.preventDefault();
        const targetId = btn.getAttribute('data-target');
        const codeElem = document.getElementById(targetId);
        if (codeElem) {{
          let text = codeElem.innerText || codeElem.textContent;
          navigator.clipboard.writeText(text).then(() => {{
            btn.textContent = 'Copiado!';
            setTimeout(() => {{ btn.textContent = 'Copiar código'; }}, 1200);
          }});
        }}
      }});
    }});
  </script>
</body>
</html>'''

    # Define a pasta de saída (sempre na raiz do projeto, pasta '04-relatorios')
    if not pasta_relatorios:
      base = os.path.dirname(__file__)
      raiz_projeto = os.path.abspath(os.path.join(base, '..', '..'))
      pasta_relatorios = os.path.join(raiz_projeto, "04-relatorios")

    os.makedirs(pasta_relatorios, exist_ok=True)

    # Gera o nome do arquivo com timestamp
    datahora = datetime.now().strftime("%Y%m%d_%H%M%S")
    relatorio_saida = os.path.join(pasta_relatorios, f"relatorio_{datahora}.html")

    # Salva o arquivo
    with open(relatorio_saida, "w", encoding="utf-8") as f:
      f.write(html_final)

    return os.path.abspath(relatorio_saida)