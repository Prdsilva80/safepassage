"""
LibreTranslate integration for automatic translation.
Translates civilian messages to English for NGO/admin review.
Translates AI responses back to civilian's language.
"""
import httpx
import structlog

log = structlog.get_logger()

LIBRETRANSLATE_URL = "http://libretranslate:5000"

SUPPORTED_LANGUAGES = {"en", "ar", "uk", "fr", "es", "pt"}

async def translate(text: str, source: str = "auto", target: str = "en") -> str:
    """Translate text. Returns original text if translation fails."""
    if not text or not text.strip():
        return text
    if source == target:
        return text
    # Normalise pt-BR to pt
    source = source.split("-")[0] if source != "auto" else source
    target = target.split("-")[0]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(f"{LIBRETRANSLATE_URL}/translate", json={
                "q": text,
                "source": source,
                "target": target,
                "format": "text",
            })
            res.raise_for_status()
            return res.json().get("translatedText", text)
    except Exception as e:
        log.warning("translation_failed", error=str(e), source=source, target=target)
        return text  # fallback: return original

async def to_english(text: str, source_lang: str = "auto") -> str:
    """Translate any text to English."""
    return await translate(text, source=source_lang, target="en")

async def from_english(text: str, target_lang: str) -> str:
    """Translate English text to target language."""
    return await translate(text, source="en", target=target_lang)

async def is_available() -> bool:
    """Check if LibreTranslate is up."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(f"{LIBRETRANSLATE_URL}/languages")
            return res.status_code == 200
    except:
        return False
