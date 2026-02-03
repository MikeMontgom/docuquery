"""
Answer Generator - Step Q4

Generates answers using the configured model.
"""

from pathlib import Path

from openai import OpenAI
import google.generativeai as genai

import config

_openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
genai.configure(api_key=config.GEMINI_API_KEY)

_PROMPT_PATH = Path(__file__).parent.parent / "docs" / "prompts" / "answering.md"
_PROMPT_TEMPLATE = None


def _load_prompt() -> str:
    """Load and cache the answering prompt."""
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is None:
        content = _PROMPT_PATH.read_text()
        parts = content.split("```")
        if len(parts) >= 2:
            _PROMPT_TEMPLATE = parts[1].strip()
        else:
            _PROMPT_TEMPLATE = content
    return _PROMPT_TEMPLATE


def _format_history(history: list[dict]) -> str:
    """Format conversation history for prompt."""
    if not history:
        return "(No previous conversation)"

    lines = []
    for msg in history:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def generate_answer(
    question: str,
    history: list[dict],
    context: str,
    model: str = "gpt-4o",
) -> str:
    """
    Generate an answer using the specified model.

    Args:
        question: User's question
        history: Conversation history
        context: Assembled document context
        model: Model to use (gpt-4o, gpt-4o-mini, gemini-3)

    Returns:
        Generated answer text
    """
    prompt_template = _load_prompt()
    history_formatted = _format_history(history)

    prompt = prompt_template.replace("{conversation_history_formatted}", history_formatted)
    prompt = prompt.replace("{question}", question)
    prompt = prompt.replace("{assembled_context}", context)

    if model.startswith("gpt"):
        return _answer_with_openai(prompt, question, model)
    elif model.startswith("gemini"):
        return _answer_with_gemini(prompt, question)
    else:
        raise ValueError(f"Unsupported model: {model}")


def _answer_with_openai(prompt: str, question: str, model: str) -> str:
    """Generate answer using OpenAI model."""
    response = _openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def _answer_with_gemini(prompt: str, question: str) -> str:
    """Generate answer using Gemini model."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    full_prompt = f"{prompt}\n\nQuestion: {question}"

    response = model.generate_content(
        full_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=2000,
        ),
    )
    return response.text
