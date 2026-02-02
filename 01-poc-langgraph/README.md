# 01-poc-langgraph

Esta pasta contém diferentes versões e experimentos do sistema de correção automática. Veja a ordem de evolução e o objetivo de cada script:

- **poc-gemini-basico.py**
  - Script inicial, faz apenas chamada simples à API Gemini. Não usa LangGraph.
  - Serve para testar integração básica com o Gemini.

- **poc-correcao-simples.py**
  - Primeira versão funcional de correção automática, com exemplos de código e feedback do Gemini, mas sem LangGraph.

- **poc-correcao-simples-langgraph.py**
  - Adiciona o uso do LangGraph para orquestrar a correção, mas ainda de forma simples, sem interface gráfica.

- **poc-leitura-arquivos-langgraph.py**
  - Versão mais avançada: usa LangGraph, interface gráfica (Tkinter), leitura de múltiplos arquivos, integração com gabarito e geração de relatório HTML.

> Recomenda-se usar o `poc-leitura-arquivos-langgraph.py` para testes completos e interface, e os demais scripts como referência para funcionalidades específicas ou exemplos de uso.
