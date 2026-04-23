
# LangGraph Correcao POC

## Instruções rápidas de execução (Windows e Linux/macOS)

## Requisitos
- Python 3.9+
- Crie e ative um ambiente virtual e instale dependências: `pip install -r requirements.txt`
- Configure um arquivo `.env` na raiz com `GEMINI_API_KEY=suachave`.

## Criar e ativar venv

Windows (PowerShell):
```powershell
python -m venv .venv
& ".venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

Linux / macOS (bash):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar o protótipo (interface)
```bash
python 01-poc-langgraph/poc-leitura-arquivos-langgraph.py
```

## Como usar o protótipo

Visão geral
- O protótipo fornece uma interface simples para avaliar programas Java enviados por alunos. Ele suporta dois modos:
	- **Modo Único**: processa um único projeto/arquivo.
	- **Modo Lote**: percorre uma pasta com subpastas de alunos (cada subpasta é um aluno) ou arquivos ZIP.

Elementos da interface
- **Selecionar Enunciado**: escolha o arquivo contendo o enunciado do exercício (Markdown ou TXT). Este é obrigatório.
- **Selecionar Gabarito (opcional)**: pasta com arquivos `.java` do gabarito do professor (opcional). Pode ser usada como referência no prompt.
- **Selecionar Código do Aluno / Pasta de Alunos**: selecione uma pasta única do aluno ou uma pasta pai contendo subpastas (cada subpasta é um aluno). Também é possível selecionar um arquivo ZIP — o sistema extrai para um diretório temporário.
- **Conceitos a Avaliar (opcional)**: abre um seletor de conceitos (carregado de `05-prompts/concepts.md`) para limitar quais tópicos devem ser considerados na avaliação.
- **Checkbox "Salvar relatório na pasta do aluno"**: quando marcado, o HTML gerado será copiado para a pasta do aluno.
- **Modo de retorno (na UI)**: escolha exatamente uma das opções mostradas na interface:
	- **Dar resposta**: comportamento resolutivo — inclui `sugestao_correcao` (código Java) no JSON retornado.
	- **Apenas dicas**: comportamento *scaffolding* — o modelo deve oferecer apenas dicas; o sistema força `sugestao_correcao` vazio antes de gerar o relatório.
- **Botão Executar Análise**: inicia o processo de extração, pré-processamento, chamada ao LLM e geração de relatórios.
- **Exportar/Salvar**: gera e salva relatórios HTML por aluno em `04-relatorios/` na raiz do projeto, e grava prompts/respostas em `05-prompts/sent_prompts` e `05-prompts/received_responses` para auditoria.

## Fluxo de execução (resumido)
1. O protótipo lê a entrada (pasta/ZIP) e extrai em diretórios temporários quando necessário.
2. Faz pré-processamento: remoção de comentários Java e tentativa de formatação com `google-java-format`.
3. Monta o prompt: carrega `05-prompts/persona.md` (se existir) e `05-prompts/system_prompt.md` (a persona é concatenada antes da instrução do sistema), preenche `05-prompts/user_template.md` com o enunciado/gabarito/código do aluno e — se a template contiver `{{CONCEITOS_A_AVALIAR}}` e o usuário tiver selecionado conceitos — insere trechos de `05-prompts/concepts.md`. Em seguida chama o LLM.
4. Recebe resposta JSON, valida o esquema e gera um relatório HTML com o feedback e a avaliação de cada item.

