import json
import logging
import re

from app.services.llama_service import generate_text, GroqServiceError


logger = logging.getLogger(__name__)

# Limita o texto enviado para não estourar o limite de tokens da Groq.
MAX_CHARS = 12000

# Mesmos valores aceitos pelo Módulo 4 (campo "arquitetura").
ALLOWED_STYLES = {"multicamadas", "clean", "mvc", "hexagonal", "onion"}

STYLE_ALIASES = {
    "camadas": "multicamadas",
    "em camadas": "multicamadas",
    "layered": "multicamadas",
    "n-tier": "multicamadas",
    "clean architecture": "clean",
    "arquitetura limpa": "clean",
    "model-view-controller": "mvc",
    "ports and adapters": "hexagonal",
    "portas e adaptadores": "hexagonal",
}

SYSTEM_PROMPT = (
    "Você é um assistente especializado em Engenharia de Software. "
    "Responda SOMENTE com um objeto JSON válido, sem texto antes ou "
    "depois e sem blocos de código markdown."
)

USER_PROMPT = (
    "Analise o documento abaixo e devolva um JSON com exatamente estas chaves:\n"
    "{\n"
    '  "summary": "resumo de 2 a 4 frases, em português",\n'
    '  "architecture": {\n'
    '    "style": "multicamadas | clean | mvc | hexagonal | onion | null",\n'
    '    "layers": ["camadas ou componentes citados"],\n'
    '    "technologies": ["tecnologias citadas"]\n'
    "  },\n"
    '  "extracted_metadata": {\n'
    '    "title": "título do documento ou null",\n'
    '    "authors": ["autores citados"],\n'
    '    "dates": ["datas citadas"],\n'
    '    "keywords": ["até 6 palavras-chave"]\n'
    "  }\n"
    "}\n\n"
    "Regras:\n"
    "- Se o documento não descreve a arquitetura de um sistema de software, "
    'use "architecture": null.\n'
    '- "style" só pode ser um dos valores listados; se nenhum se aplicar, use null.\n'
    "- Use apenas informações presentes no documento. Não invente.\n\n"
    "DOCUMENTO:\n"
)


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(
        r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE
    ).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end <= start:
        raise ValueError("Resposta sem JSON.")

    return json.loads(cleaned[start : end + 1])


def _normalize_architecture(value):
    if not isinstance(value, dict):
        return None

    style = value.get("style")
    if isinstance(style, str):
        style = style.strip().lower()
        style = STYLE_ALIASES.get(style, style)
        if style not in ALLOWED_STYLES:
            style = None
    else:
        style = None

    layers = value.get("layers")
    technologies = value.get("technologies")

    return {
        "style": style,
        "layers": layers if isinstance(layers, list) else [],
        "technologies": technologies if isinstance(technologies, list) else [],
    }


def enrich_document(document_text: str) -> dict:
    """
    Gera resumo, arquitetura e metadados. Nunca levanta exceção:
    se algo falhar, devolve os três campos como None, e a
    classificação já feita continua válida.
    """

    empty = {
        "summary": None,
        "architecture": None,
        "extracted_metadata": None,
    }

    try:
        raw = generate_text(
            prompt=USER_PROMPT + document_text[:MAX_CHARS],
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,
            max_completion_tokens=1024,
        )

        data = _parse_json(raw)

        summary = data.get("summary")
        metadata = data.get("extracted_metadata")

        return {
            "summary": summary.strip()
            if isinstance(summary, str) and summary.strip()
            else None,
            "architecture": _normalize_architecture(data.get("architecture")),
            "extracted_metadata": metadata
            if isinstance(metadata, dict)
            else None,
        }

    except (GroqServiceError, ValueError, json.JSONDecodeError) as error:
        logger.warning("Enriquecimento da análise falhou: %s", error)
        return empty

    except Exception:
        logger.exception("Erro inesperado no enriquecimento da análise.")
        return empty
