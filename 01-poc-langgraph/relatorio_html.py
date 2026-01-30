import os
from datetime import datetime

def gerar_relatorio_html(enunciado, gabarito, codigo_aluno, avaliacao, justificativa, sugestao_correcao, pasta_relatorios=None):
    """
    Gera um relatório HTML moderno e salva na pasta relatorios/ com data e hora no nome.
    Retorna o caminho absoluto do arquivo gerado.
    """
    # Define a cor do badge de status
    cor = "bg-gray-400"
    if avaliacao == "Certo":
        cor = "bg-green-600"
    elif avaliacao == "Errado":
        cor = "bg-red-600"
    elif avaliacao == "Parcialmente Certo":
        cor = "bg-yellow-500"

    # Prepara a justificativa para exibição em HTML (substituindo quebras de linha)
    # Fazemos isso fora da f-string para evitar o SyntaxError com contrabarras
    justificativa_html = justificativa.replace('\n', '<br>').replace('\\n', '<br>')

    # Prepara o bloco de gabarito se ele existir
    gabarito_html = ""
    if gabarito:
        gabarito_html = f'''
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-700 mb-2">Gabarito do Professor</h2>
      <div class="rounded-lg overflow-hidden border border-gray-200">
        <pre><code class="language-java">{gabarito}</code></pre>
      </div>
    </div>'''

    # Monta o HTML final
    html_final = f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Relatório de Correção - LangGraph</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
  <style>
    pre code {{ border-radius: 0.5rem !important; }}
    body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}
  </style>
</head>
<body class="bg-gray-50 min-h-screen pb-12">
  <div class="max-w-4xl mx-auto p-6 mt-8 bg-white rounded-xl shadow-xl border border-gray-100">
    <div class="flex justify-between items-center mb-8 border-b pb-4">
        <h1 class="text-3xl font-extrabold text-slate-800 tracking-tight">Relatório de Correção</h1>
        <span class="px-4 py-1.5 rounded-full text-white text-sm font-bold shadow-sm {cor}">
            {avaliacao.upper()}
        </span>
    </div>

    <div class="space-y-8">
        <div>
          <h2 class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-2">Enunciado</h2>
          <div class="bg-slate-50 p-4 rounded-lg text-slate-700 text-sm border-l-4 border-slate-300 italic">
            {enunciado}
          </div>
        </div>

        {gabarito_html}

        <div>
          <h2 class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-2">Código do Aluno</h2>
          <pre><code class="language-java">{codigo_aluno}</code></pre>
        </div>

        <div class="bg-blue-50 p-6 rounded-xl border border-blue-100">
          <h2 class="text-blue-800 font-bold mb-3 flex items-center">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"></path></svg>
            Justificativa Pedagógica
          </h2>
          <div class="text-blue-900 leading-relaxed">{justificativa_html}</div>
        </div>

        <div>
          <h2 class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-2">Sugestão de Correção</h2>
          <pre><code class="language-java">{sugestao_correcao}</code></pre>
        </div>
    </div>

    <footer class="text-center text-xs text-gray-400 mt-12 pt-6 border-t">
        Gerado automaticamente por LangGraph Corretor • {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </footer>
  </div>
  <script>hljs.highlightAll();</script>
</body>
</html>'''

    # Define a pasta de saída (sempre na raiz do projeto, pasta 'relatorios')
    if not pasta_relatorios:
      # Caminho absoluto para a pasta '04-relatorios' na raiz do projeto
      # Procura a raiz do projeto subindo até encontrar requirements.txt
      raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      while not os.path.exists(os.path.join(raiz_projeto, 'requirements.txt')):
        nova_raiz = os.path.dirname(raiz_projeto)
        if nova_raiz == raiz_projeto:
          break
        raiz_projeto = nova_raiz
      pasta_relatorios = os.path.join(raiz_projeto, "04-relatorios")

    os.makedirs(pasta_relatorios, exist_ok=True)

    # Gera o nome do arquivo com timestamp
    datahora = datetime.now().strftime("%Y%m%d_%H%M%S")
    relatorio_saida = os.path.join(pasta_relatorios, f"relatorio_{datahora}.html")

    # Salva o arquivo
    with open(relatorio_saida, "w", encoding="utf-8") as f:
      f.write(html_final)

    return os.path.abspath(relatorio_saida)