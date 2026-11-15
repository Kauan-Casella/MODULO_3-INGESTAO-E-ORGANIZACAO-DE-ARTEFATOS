import os
from pathlib import Path

from dotenv import load_dotenv
from groq import (
    Groq,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)


# Carrega o .env localizado na raiz do projeto.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class GroqServiceError(Exception):
    """Erro de comunicação com o serviço de IA."""


def get_groq_client() -> Groq:
    """
    Cria o cliente Groq utilizando a API Key
    configurada nas variáveis de ambiente.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise GroqServiceError(
            "GROQ_API_KEY não foi configurada."
        )

    return Groq(
        api_key=api_key,
        timeout=30.0,
        max_retries=2,
    )


def generate_text(
    prompt: str,
    system_prompt: str = (
        "Você é um assistente especializado em "
        "Engenharia de Software. Responda em português "
        "brasileiro de maneira clara e técnica."
    ),
    temperature: float = 0.2,
    max_completion_tokens: int | None = None,
) -> str:
    """
    Envia um prompt para o modelo configurado na Groq
    e retorna o texto gerado.
    """

    if not prompt or not prompt.strip():
        raise ValueError("O prompt não pode estar vazio.")

    # Obtém o limite de tokens do .env.
    if max_completion_tokens is None:
        max_completion_tokens = int(
            os.getenv("GROQ_MAX_TOKENS", "2048")
        )

    model = os.getenv(
        "GROQ_MODEL",
        "qwen/qwen3.8-27b"
    )

    client = get_groq_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            reasoning_effort="none",
        )

        content = response.choices[0].message.content

        if not content:
            raise GroqServiceError(
                "O modelo retornou uma resposta vazia."
            )

        return content.strip()

    except AuthenticationError as error:
        raise GroqServiceError(
            "Falha de autenticação na Groq. Verifique a API Key."
        ) from error

    except RateLimitError as error:
        raise GroqServiceError(
            "Limite de requisições ou cota da Groq atingido."
        ) from error

    except APITimeoutError as error:
        raise GroqServiceError(
            "A requisição para a Groq excedeu o tempo limite."
        ) from error

    except APIConnectionError as error:
        raise GroqServiceError(
            "Não foi possível conectar à API da Groq."
        ) from error

    except APIStatusError as error:
        raise GroqServiceError(
            f"A Groq retornou um erro HTTP: {error.status_code}."
        ) from error
