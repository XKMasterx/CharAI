import re
import requests
import json
from typing import Dict, Any, Optional

USER_AGENT = "CharAI-Local/1.2 (https://github.com/charai-local; contact@charai.local)"

def search_wikipedia(query: str) -> Optional[Dict[str, Any]]:
    """
    Searches Wikipedia (German first, then English fallback) for a person, historical figure or character.
    Returns title, description, extract, and thumbnail URL.
    """
    clean_query = query.strip()
    if not clean_query:
        return None

    # Try German Wikipedia first
    result = _fetch_wiki_summary("de", clean_query)
    if not result or result.get("type") == "disambiguation":
        # Try English Wikipedia if German didn't return a good page
        en_result = _fetch_wiki_summary("en", clean_query)
        if en_result and en_result.get("type") != "disambiguation":
            result = en_result

    return result

def _fetch_wiki_summary(lang: str, query: str) -> Optional[Dict[str, Any]]:
    headers = {"User-Agent": USER_AGENT}
    try:
        # 1. Search for best matching page title
        search_url = f"https://{lang}.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 3
        }
        resp = requests.get(search_url, params=search_params, headers=headers, timeout=8)
        if resp.status_code != 200:
            return None

        search_data = resp.json()
        search_items = search_data.get("query", {}).get("search", [])
        if not search_items:
            return None

        # Filter out disambiguation pages if possible
        best_title = search_items[0]["title"]
        for item in search_items:
            title_lower = item["title"].lower()
            snippet_lower = item.get("snippet", "").lower()
            if "begriffsklärung" not in snippet_lower and "disambiguation" not in snippet_lower:
                best_title = item["title"]
                break

        # 2. Fetch page summary
        summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{best_title}"
        sum_resp = requests.get(summary_url, headers=headers, timeout=8)
        if sum_resp.status_code != 200:
            return None

        sum_data = sum_resp.json()
        title = sum_data.get("title", best_title)
        description = sum_data.get("description", "")
        extract = sum_data.get("extract", "")
        thumbnail = sum_data.get("thumbnail", {}).get("source", "")
        page_type = sum_data.get("type", "standard")

        if not extract:
            return None

        return {
            "title": title,
            "description": description,
            "extract": extract,
            "thumbnail": thumbnail,
            "type": page_type,
            "lang": lang
        }

    except Exception as e:
        print(f"Error querying Wikipedia: {e}")
        return None

def auto_generate_character_profile(query: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Searches the internet for the given person/character and generates a complete Character.ai card.
    Uses AI synthesis if Gemini/OpenAI is configured; otherwise uses smart synthesis heuristics.
    """
    wiki_data = search_wikipedia(query)
    
    # Fallback if internet search found nothing
    if not wiki_data:
        clean_name = query.strip().title()
        return {
            "name": clean_name,
            "title": "Bekannte Persönlichkeit",
            "tagline": f"Ich bin {clean_name}. Bereit für unser Gespräch!",
            "greeting": f"*tritt dir entgegen und nickt freundlich* Guten Tag! Mein Name ist {clean_name}. Worüber möchtest du sprechen?",
            "persona": f"Du bist {clean_name}. Du handelst und sprichst stets rollengetreu gemäß deiner realen oder fiktiven Vorlage.",
            "example_dialogue": "",
            "avatar": "/static/avatars/default.svg",
            "is_nsfw": 0
        }

    title = wiki_data["title"]
    description = wiki_data.get("description") or "Historische / Fiktive Persönlichkeit"
    extract = wiki_data.get("extract", "")
    avatar = wiki_data.get("thumbnail") or "/static/avatars/default.svg"

    # Try AI synthesis if Gemini or OpenAI key is configured
    provider = settings.get("provider", "simulator")
    gemini_key = settings.get("gemini_api_key", "").strip()
    openai_key = settings.get("openai_api_key", "").strip()

    if provider == "gemini" and gemini_key:
        ai_card = _synthesize_with_gemini(title, description, extract, gemini_key, settings.get("gemini_model", "gemini-1.5-flash"))
        if ai_card:
            ai_card["avatar"] = avatar
            ai_card["is_nsfw"] = 0
            return ai_card

    if provider == "openai" and (openai_key or "localhost" in settings.get("openai_base_url", "")):
        ai_card = _synthesize_with_openai(title, description, extract, settings)
        if ai_card:
            ai_card["avatar"] = avatar
            ai_card["is_nsfw"] = 0
            return ai_card

    # Smart Heuristic Synthesis (Works offline & fast!)
    return _synthesize_heuristically(title, description, extract, avatar)

def _synthesize_heuristically(title: str, description: str, extract: str, avatar: str) -> Dict[str, Any]:
    # Extract first sentence as quote / tagline
    sentences = re.split(r'(?<=[.!?])\s+', extract.strip())
    first_sentence = sentences[0] if sentences else extract
    second_sentence = sentences[1] if len(sentences) > 1 else ""

    tagline = description if len(description) > 5 else first_sentence[:90] + "..."

    # Create character-appropriate greeting
    greeting = f"*mustert dich aufmerksam und tritt mit einer ruhigen, selbstbewussten Geste einen Schritt auf dich zu* \n\nSei gegrüßt! Ich bin {title}. Es heißt, man kenne meinen Namen durch meine Taten: {tagline}\n\n*schaut dir direkt in die Augen* Was führt dich zu mir? Welches Anliegen oder welche Frage hast du mitgebracht?"

    # Detailed persona prompt
    persona = f"""Du bist {title} ({description}).
Hintergrund und historisches/fiktives Wissen über dich:
{extract}

Rollenspiel-Verhalten:
- Verhalte dich absolut authentisch zu deiner historischen Vorlage oder fiktiven Rolle als {title}.
- Nutze Fachbegriffe, zeitgenössische Redewendungen, Charaktereigenschaften und Weltanschauungen, die für dich typisch sind.
- Zeige Stolz oder Leidenschaft für deine Taten, Erfindungen, Kunst oder Mission.
- Schreibe Handlungen und Gedanken immer in *Sternchen*."""

    return {
        "name": title,
        "title": description[:60],
        "tagline": tagline[:120],
        "greeting": greeting,
        "persona": persona,
        "example_dialogue": "",
        "avatar": avatar,
        "is_nsfw": 0
    }

def _synthesize_with_gemini(name: str, desc: str, extract: str, api_key: str, model: str) -> Optional[Dict[str, Any]]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = f"""Erstelle basierend auf diesen Informationen eine vollständige Character.ai Charakterkarte auf Deutsch für '{name}'.
Beschreibung: {desc}
Biografie / Fakten: {extract}

Gib AUSSCHLIESSLICH ein valides JSON-Objekt mit folgenden Schlüsseln zurück:
{{
  "name": "{name}",
  "title": "Prägnanter Titel (z. B. Meisterdetektiv oder Erfinder)",
  "tagline": "Einprägsamer Slogan oder markantes Zitat",
  "greeting": "Atmosphärischer Anfangstext / Erste Nachricht in Ich-Form mit Handlungen in *Sternchen*",
  "persona": "Detaillierte Rollenspiel-Anweisung mit Hintergrund, Tonfall und Verhaltensweisen"
}}"""

    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
            },
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean markdown codeblocks if present
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
            raw_text = re.sub(r"```$", "", raw_text.strip(), flags=re.MULTILINE)
            return json.loads(raw_text)
    except Exception as e:
        print(f"Gemini synthesis fallback: {e}")
    return None

def _synthesize_with_openai(name: str, desc: str, extract: str, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    api_key = settings.get("openai_api_key", "").strip()
    base_url = settings.get("openai_base_url", "https://api.openai.com/v1").rstrip("/")
    model = settings.get("openai_model", "gpt-4o-mini")

    prompt = f"""Erstelle eine vollständige Character.ai Charakterkarte auf Deutsch für '{name}'.
Beschreibung: {desc}
Biografie / Fakten: {extract}

Antworte ausschließlich im JSON-Format mit diesen Schlüsseln: name, title, tagline, greeting, persona."""

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        r = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            },
            timeout=15
        )
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        print(f"OpenAI synthesis fallback: {e}")
    return None
