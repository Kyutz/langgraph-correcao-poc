import os
import time
import random
import json
from typing import Optional

# Importação do google.genai para evitar falhas de importação em ambientes com dependências mínimas
_genai_client = None

MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gemini-2.5-flash')
MAX_RETRIES = 5

JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "avaliacao": {"type": "STRING"},
        "justificativa": {"type": "STRING"},
        "dica_correcao": {"type": "STRING"},
        "sugestao_correcao": {"type": "STRING"}
    },
    "required": ["avaliacao", "justificativa", "dica_correcao", "sugestao_correcao"]
}


def _get_client():
    global _genai_client
    if _genai_client is not None:
        return _genai_client
    try:
        from google import genai
    except Exception as e:
        raise RuntimeError("google.genai não está disponível no ambiente: " + str(e))
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY não encontrado no ambiente')
    _genai_client = genai.Client(api_key=api_key)
    return _genai_client


def generate_content_with_retry(prompt: str, system_instruction: Optional[str] = None):
    """Chama o LLM (Gemini) com retries, schema e backoff.
    Retorna o JSON decodificado como dict.
    Levanta RuntimeError se cliente não puder ser inicializado.
    """
    client = _get_client()
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
            try:
                data = json.loads(response.text)
                for key in ["avaliacao", "justificativa", "sugestao_correcao"]:
                    if key not in data:
                        raise ValueError(f"Chave obrigatória ausente: {key}")
                return data
            except Exception as e:
                # Log útil para depuração local
                print(f"Erro ao decodificar JSON da LLM: {e}\nResposta recebida:\n{getattr(response, 'text', str(response))}")
                raise
        except Exception as e:
            # Tenta detectar rate limits simples
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "rate" in msg.lower():
                delay = 2 ** attempt + random.uniform(0, 1)
                print(f"Aviso: taxa limite ou erro transitório. Retry em {delay:.2f}s...")
                time.sleep(delay)
                continue
            raise
    raise RuntimeError("Falha ao gerar conteúdo após múltiplas tentativas.")
