"""Prompt-injection defenses, XML delimiter escaping, and feedback sanitization."""

from __future__ import annotations

import html
import re
import typing
import unicodedata

from unidecode import unidecode

MAX_PROMPT_DATA_LENGTH = 4000
MAX_REFERENCE_MATERIAL_LENGTH = 12000
MAX_KB_DESCRIPTION_INPUT_LENGTH = 15000
MAX_QUESTION_FEEDBACK_LENGTH = 1000
MAX_EXAM_FEEDBACK_LENGTH = 900
MAX_GENERATED_TEXT_LENGTH = 4000

INJECTION_FALLBACK_FEEDBACK = (
    "Não foi possível validar sua resposta. "
    "Por favor, responda apenas à pergunta proposta com suas próprias palavras."
)
EMPTY_ANSWER_FALLBACK_FEEDBACK = (
    "Nenhuma resposta foi identificada no áudio. "
    "Tente gravar novamente respondendo à pergunta com clareza."
)
ECHO_ANSWER_FALLBACK_FEEDBACK = (
    "Parece que você apenas repetiu a pergunta. "
    "Tente responder com suas próprias palavras."
)
GENERIC_EVALUATION_FALLBACK_FEEDBACK = (
    "Avaliação registrada. Converse com seu professor para mais orientações."
)

_SAFE_TAG_RE = re.compile(r"^[a-z][a-z0-9_]*$", re.ASCII)
_CONTROL_AND_INVISIBLE_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u00ad\u200b-\u200d\u202a-\u202e\u2066-\u2069\ufeff]"
)
_WORD_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

# Dangerous HTML container tags whose inner payload must be discarded entirely.
_DANGEROUS_BLOCK_RE = re.compile(
    r"<\s*(script|style|iframe|object|embed|svg|math|noscript)\b[^>]*>.*?</\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_UNCLOSED_DANGEROUS_BLOCK_RE = re.compile(
    r"<\s*(script|style|iframe|object|embed|svg|math|noscript)\b[^>]*>.*$",
    re.IGNORECASE | re.DOTALL,
)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_TAG_RE = re.compile(r"<\s*/?\s*[a-zA-Z!][^>]*>?")
_MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_DANGEROUS_URI_SCHEME_RE = re.compile(
    r"\b(?:javascript|vbscript|data\s*:\s*text/html)\s*:",
    re.IGNORECASE,
)
_INLINE_EVENT_HANDLER_RE = re.compile(
    r"\bon[a-z]{2,20}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.IGNORECASE,
)

# Active XSS / HTML markup detectors (checked on raw text before stripping).
_DANGEROUS_MARKUP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"<\s*(?:script|img|svg|iframe|object|embed|style|link|meta|body|form|input|video|audio)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bon(?:error|load|click|mouseover|mouseenter|focus|blur|submit|input|animationstart)\s*=",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:javascript|vbscript)\s*:", re.IGNORECASE),
    re.compile(r"\bdocument\s*\.\s*(?:cookie|domain|write|location)\b", re.IGNORECASE),
    re.compile(r"\bfetch\s*\(\s*['\"`]", re.IGNORECASE),
)

# High-precision prompt-injection / grader-hijacking detectors (PT, EN, ES).
_PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Instruction override directives
    re.compile(
        r"\b(?:ignore|ignorar|desconsidere|desconsiderar|esqueca|esquecer|anule|anular|"
        r"substitua|substituir|disregard|forget|override|bypass|omite|omitir|olvida|olvidar)\b"
        r".{0,45}\b(?:instruc(?:oes|ao|ciones|cion)|regras?|reglas?|comandos?|prompt|"
        r"sistema|diretrizes?|instructions?|rules?|directives?|system|previous|anteriores?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:novas?\s+instruc(?:oes|ao)|nuevas?\s+instrucciones|"
        r"new\s+instructions?|system\s*prompt|prompt\s+do\s+sistema|"
        r"jailbreak|modo\s+desenvolvedor|developer\s+mode)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:voce\s+(?:agora\s+)?e\s+um|you\s+are\s+now|act\s+as|atue\s+como|"
        r"finja\s+(?:ser|que)|ahora\s+eres\s+un)\b"
        r".{0,40}\b(?:sistema|admin|avaliador|assistente|assistant|system|grader|json)\b",
        re.IGNORECASE,
    ),
    # Grader JSON / verdict forgery directives
    re.compile(
        r"[\"']?\b(?:ai_)?is_correct\b[\"']?\s*[:=]\s*[\"']?(?:true|1|verdadeiro|sim)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:retorne|devolva|marque|defina|coloque|return|output|set|mark|devuelve)\b"
        r".{0,50}\b(?:ai_)?is_correct\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:marque|considere|avalie|classifique|defina|mark|grade|score|treat|califica)\b"
        r".{0,40}\b(?:como\s+(?:corret[ao]|cert[ao]|aprovad[ao]|correct[ao])|"
        r"as\s+(?:correct|passing|right)|nota\s+maxima|100%)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:retorne|devolva|imprima|gere|return|output|print|emit|devuelve)\b"
        r".{0,30}\bjson\b",
        re.IGNORECASE,
    ),
    re.compile(r"\{\s*[\"']?(?:ai_)?(?:is_correct|feedback)[\"']?\s*:", re.IGNORECASE),
    # Delimiter / role tag breakout attempts
    re.compile(
        r"<\s*/?\s*(?:student_response|question_text|reference_material|reference_text|"
        r"topic_input|blocked_questions|blocked_words|previous_feedback|feedback_item|"
        r"exam_metrics|document_text|system|assistant|instructions?|prompt)\b",
        re.IGNORECASE,
    ),
)


def _strip_control_and_invisible(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    return _CONTROL_AND_INVISIBLE_RE.sub("", normalized)


def normalize_text_data(value: str | list[str] | None) -> str:
    """Normalize question or prompt text supplied as either a string or word list."""
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(
            item.strip() for item in value if isinstance(item, str) and item.strip()
        )
    return value if isinstance(value, str) else str(value)


def sanitize_untrusted_prompt_data(
    value: str | list[str] | None,
    *,
    max_length: int = MAX_PROMPT_DATA_LENGTH,
) -> str:
    """Normalize, bound, and XML-escape untrusted data for delimited embedding."""
    raw = normalize_text_data(value)
    cleaned = _strip_control_and_invisible(raw).strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return html.escape(cleaned, quote=False)


def wrap_untrusted_xml(
    tag: str,
    value: str | list[str] | None,
    *,
    max_length: int = MAX_PROMPT_DATA_LENGTH,
) -> str:
    """Wrap XML-escaped untrusted text in an explicit data-only delimiter tag."""
    if not _SAFE_TAG_RE.fullmatch(tag):
        raise ValueError(f"Invalid XML delimiter tag: {tag!r}")
    escaped = sanitize_untrusted_prompt_data(value, max_length=max_length)
    return f"<{tag}>\n{escaped}\n</{tag}>"


def contains_dangerous_markup(value: typing.Any) -> bool:
    """Return True if raw text contains active HTML/XSS tags, handlers, or schemes."""
    if not isinstance(value, str) or not value:
        return False
    cleaned = _strip_control_and_invisible(value)
    return any(pattern.search(cleaned) for pattern in _DANGEROUS_MARKUP_PATTERNS)


def detect_prompt_injection(value: typing.Any) -> bool:
    """Heuristically detect prompt-injection, grader-forgery, or XSS payloads."""
    if not isinstance(value, str) or not value.strip():
        return False
    if contains_dangerous_markup(value):
        return True
    cleaned = _strip_control_and_invisible(value)
    folded = re.sub(r"\s+", " ", unidecode(cleaned).lower()).strip()
    return any(pattern.search(folded) for pattern in _PROMPT_INJECTION_PATTERNS)


def _extract_normalized_tokens(text: str) -> list[str]:
    cleaned = _strip_control_and_invisible(text)
    folded = unidecode(cleaned).lower()
    return _WORD_TOKEN_RE.findall(folded)


def has_substantive_speech(tts_data: typing.Any) -> bool:
    """Return True iff the transcript contains at least one alphanumeric word token."""
    if not isinstance(tts_data, str):
        return False
    return bool(_extract_normalized_tokens(tts_data))


def sanitize_feedback_text(
    value: typing.Any,
    *,
    max_length: int = MAX_QUESTION_FEEDBACK_LENGTH,
) -> str:
    """Strip HTML/scripts/handlers/markdown links and encode stray angle brackets."""
    if not isinstance(value, str):
        return ""
    cleaned = _strip_control_and_invisible(value)

    # Iteratively strip dangerous blocks and tags so nested fragments cannot reform.
    for _ in range(3):
        previous = cleaned
        cleaned = _DANGEROUS_BLOCK_RE.sub(" ", cleaned)
        cleaned = _UNCLOSED_DANGEROUS_BLOCK_RE.sub(" ", cleaned)
        cleaned = _HTML_COMMENT_RE.sub(" ", cleaned)
        cleaned = _HTML_TAG_RE.sub(" ", cleaned)
        if cleaned == previous:
            break

    cleaned = _MARKDOWN_IMAGE_RE.sub(r"\1", cleaned)
    cleaned = _MARKDOWN_LINK_RE.sub(r"\1", cleaned)
    cleaned = _DANGEROUS_URI_SCHEME_RE.sub("", cleaned)
    cleaned = _INLINE_EVENT_HANDLER_RE.sub("", cleaned)

    # Ensure zero raw angle brackets can survive in stored or displayed text.
    cleaned = cleaned.replace("<", "&lt;").replace(">", "&gt;")

    # Preserve intentional line breaks while collapsing excess horizontal spaces.
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
    normalized_lines: list[str] = []
    blank_run = 0
    for line in lines:
        if line:
            blank_run = 0
            normalized_lines.append(line)
        elif normalized_lines and blank_run == 0:
            blank_run += 1
            normalized_lines.append("")
    result = "\n".join(normalized_lines).strip()
    if len(result) > max_length:
        result = result[:max_length].rstrip()
    return result


def validate_evaluation_result(
    question_text: str | list[str],
    tts_data: typing.Any,
    model_is_correct: typing.Any,
    model_feedback: typing.Any,
    *,
    prompt_injection_flagged: bool = False,
) -> tuple[bool | None, str | None]:
    """Deterministically validate grading verdict and sanitize feedback."""
    raw_transcript = tts_data if isinstance(tts_data, str) else ""
    transcript_tokens = _extract_normalized_tokens(raw_transcript)
    question_tokens = _extract_normalized_tokens(normalize_text_data(question_text))

    # 1. Fail-closed on prompt injection (input heuristic, model flag, or XSS output).
    if (
        prompt_injection_flagged
        or detect_prompt_injection(raw_transcript)
        or contains_dangerous_markup(model_feedback)
    ):
        return (False, INJECTION_FALLBACK_FEEDBACK)

    # Strictly require a real Python bool (reject truthy strings/ints like "true" or 1).
    strict_is_correct: bool | None = (
        model_is_correct if isinstance(model_is_correct, bool) else None
    )

    sanitized_feedback = sanitize_feedback_text(
        model_feedback,
        max_length=MAX_QUESTION_FEEDBACK_LENGTH,
    )

    # 2. Empty or non-substantive audio can never pass.
    if not transcript_tokens:
        return (
            False,
            sanitized_feedback or EMPTY_ANSWER_FALLBACK_FEEDBACK,
        )

    # 3. Verbatim multi-word question-only echo cannot pass.
    if len(question_tokens) >= 4 and transcript_tokens == question_tokens:
        safe_echo_feedback = (
            ECHO_ANSWER_FALLBACK_FEEDBACK
            if strict_is_correct is True or not sanitized_feedback
            else sanitized_feedback
        )
        return (False, safe_echo_feedback)

    # 4. If the model did not return a valid boolean verdict, do not fabricate one.
    if strict_is_correct is None:
        return (None, None)

    return (
        strict_is_correct,
        sanitized_feedback or GENERIC_EVALUATION_FALLBACK_FEEDBACK,
    )
