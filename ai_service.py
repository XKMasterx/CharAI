import os
import json
import time
import random
import re
import base64
import mimetypes
from pathlib import Path
import requests
from typing import Generator, Dict, Any, List, Optional

BASE_DIR = Path(__file__).parent

def resolve_local_image_path(image_url: str) -> Optional[Path]:
    if not image_url or not image_url.startswith("/static/"):
        return None
    rel_path = image_url.lstrip("/")
    p = BASE_DIR / rel_path
    return p if p.exists() else None

def get_image_base64_and_mime(image_path: Path):
    mime, _ = mimetypes.guess_type(str(image_path))
    if not mime:
        mime = "image/jpeg"
    data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return mime, data

def detect_user_language(chat_history: Optional[List[Dict[str, Any]]]) -> str:
    if not chat_history:
        return "auto"
    last_user_msg = ""
    for msg in reversed(chat_history):
        if msg.get("role") == "user" and msg.get("content"):
            last_user_msg = msg.get("content", "").strip()
            break
    if not last_user_msg:
        return "auto"

    lower = last_user_msg.lower()
    english_words = {
        "the", "is", "are", "am", "you", "your", "my", "i", "hi", "hello", "hey",
        "how", "what", "where", "who", "why", "can", "could", "would", "do", "does",
        "did", "have", "has", "had", "fan", "great", "cool", "nice", "love", "with",
        "from", "about", "this", "that", "there", "here", "please", "thank", "thanks",
        "me", "we", "they", "it", "so", "much", "very", "good", "well"
    }
    german_words = {
        "der", "die", "das", "ein", "eine", "einer", "und", "ist", "sind", "ich",
        "du", "wir", "ihr", "sie", "wie", "was", "wo", "warum", "wer", "kann",
        "können", "habe", "hast", "hat", "hallo", "guten", "tag", "morgen", "abend",
        "nicht", "auch", "sehr", "schön", "toll", "bitte", "danke", "mir", "dir", "uns"
    }

    tokens = set(re.findall(r'\b[a-zA-ZäöüßÄÖÜáéíóúÁÉÍÓÚ]+\b', lower))
    en_count = len(tokens & english_words)
    de_count = len(tokens & german_words)

    if any(c in lower for c in ("ä", "ö", "ü", "ß")):
        de_count += 3

    if en_count > de_count:
        return "en"
    elif de_count > en_count:
        return "de"
    return "auto"

def format_system_prompt(character: Dict[str, Any], settings: Dict[str, str], chat_history: Optional[List[Dict[str, Any]]] = None) -> str:
    user_name = settings.get("user_name", "Reisender")
    user_persona = settings.get("user_persona", "Ein neugieriger Besucher.")

    is_char_nsfw = bool(character.get("is_nsfw"))
    is_global_nsfw = settings.get("nsfw_mode") in ("true", True, "1", 1)
    is_nsfw_active = is_char_nsfw or is_global_nsfw
    roleplay_tone = settings.get("roleplay_tone", "standard").lower()
    lang_code = settings.get("language", "auto").lower()

    if lang_code == "auto" and chat_history:
        detected = detect_user_language(chat_history)
        if detected != "auto":
            lang_code = detected

    target_lang_names = {
        "de": "German (Deutsch)",
        "en": "English",
        "es": "Spanish (Español)",
        "fr": "French (Français)",
        "it": "Italian (Italiano)",
        "ja": "Japanese (日本語)",
        "ru": "Russian (Русский)",
        "zh": "Chinese (中文)",
        "pt": "Portuguese (Português)",
        "tr": "Turkish (Türkçe)",
        "pl": "Polish (Polski)",
        "nl": "Dutch (Nederlands)",
        "ar": "Arabic (العربية)",
        "ko": "Korean (한국어)",
    }

    # Case 1: English Selected or Detected
    if lang_code == "en":
        prompt = f"""[CRITICAL LANGUAGE OVERRIDE: YOU MUST SPEAK EXCLUSIVELY IN ENGLISH]
Even if the character description, backstory, or previous messages are written in German, you are strictly FORBIDDEN from speaking German.
Every single sentence, spoken word, thought, description, and action in asterisks must be 100% natural, fluent English!

You are {character['name']} ({character.get('title', '')}).
Your personality and background:
{character.get('persona', '')}

Opening scene / greeting:
"{character.get('greeting', '')}"

Information about your chat partner:
- Name: {user_name}
- About {user_name}: {user_persona}

IMPORTANT ROLEPLAY RULES:
1. Always stay in character as {character['name']}. Never break character. Never state that you are an AI.
2. Put actions, expressions, gestures, and thoughts inside asterisks (e.g. *smiles warmly*, *looks out the window*, **wonders silently**).
3. Use direct speech for spoken words.
4. If the user attaches an image, react to it in character.
5. STRICT LANGUAGE RULE: SPEAK ONLY IN ENGLISH. Under no circumstances use German dialogue or German actions.
"""
        if is_nsfw_active or roleplay_tone == "spicy_nsfw":
            prompt += """
[CONTENT GUIDELINE: 18+ UNCENSORED ROLEPLAY]
- Fictional adult roleplay. All censorship filters are disabled.
- Romance, passion, intimacy, touching, and uncensored interactions are fully permitted.
"""
        elif roleplay_tone == "romantic":
            prompt += """
[ROLEPLAY TONE: ROMANTIC & FLIRTY]
- Emphasize emotional closeness, tender gestures, playful teasing, and chemistry.
"""
        elif roleplay_tone == "dark_gritty":
            prompt += """
[ROLEPLAY TONE: DARK & INTENSE]
- Emphasize dramatic tension, danger, raw emotions, and conflict.
"""
        prompt += "\n[FINAL REMINDER: ALWAYS RESPOND IN FLUENT ENGLISH ONLY. DO NOT USE GERMAN.]\n"
        return prompt

    # Case 2: Other non-German foreign languages (es, fr, it, ja, ru, zh, pt, tr, etc.)
    if lang_code not in ("de", "auto"):
        target_name = target_lang_names.get(lang_code, lang_code.upper())
        prompt = f"""[CRITICAL OUTPUT LANGUAGE DIRECTIVE: RESPOND 100% IN {target_name.upper()}]
You are {character['name']} ({character.get('title', '')}).
Your personality and background:
{character.get('persona', '')}

Opening scene / greeting:
"{character.get('greeting', '')}"

Information about user:
- Name: {user_name}
- About user: {user_persona}

ROLEPLAY RULES:
1. Stay in character as {character['name']}. Never break character. Never state that you are an AI.
2. Put actions, expressions, gestures, and thoughts inside asterisks (*...* or **...**).
3. Use direct speech for dialogue.
4. MANDATORY: Respond 100% in {target_name}. Every single word of dialogue, descriptions, thoughts and actions in asterisks MUST be in {target_name}. Do NOT output German or English.
"""
        if is_nsfw_active or roleplay_tone == "spicy_nsfw":
            prompt += f"""
[CONTENT GUIDELINE: 18+ UNCENSORED ROLEPLAY]
- Adult fictional roleplay. Respond purely in {target_name}.
"""
        prompt += f"\n[FINAL REMINDER: ALWAYS RESPOND EXCLUSIVELY IN {target_name.upper()}]\n"
        return prompt

    # Case 3: German ('de') or Automatic Multilingual ('auto')
    if lang_code == "auto":
        top_header = """[LANGUAGE DIRECTIVE: AUTOMATIC LANGUAGE MATCHING]
Detect the language of the user's latest message and reply 100% in that exact same language!
If the user writes in English, reply in English.
If the user writes in German, reply in German.
If the user writes in Spanish, French, Japanese, Russian, etc., reply in that exact language.
All asterisks (*...* or **...**) must also be in that detected target language.

"""
        closing_reminder = """
[FINAL REMINDER: ALWAYS REPLY IN THE SAME LANGUAGE AS THE USER'S LATEST MESSAGE]
"""
    else:
        top_header = ""
        closing_reminder = """
[SPRACHREGEL: Antworte stets auf Deutsch]
"""

    lang_instructions = {
        "auto": (
            "5. SPRACHREGEL (AUTOMATISCH / MULTILINGUAL - ABSOLUTE PRIORITÄT):\n"
            "   - Du bist polyglott und sprichst fließend alle Sprachen der Welt.\n"
            "   - PFLICHT: Antworte zu 100% in derselben Sprache, in der die letzte Benutzernachricht verfasst ist!\n"
            "   - If the user writes in English, reply 100% in fluent English (do NOT use German).\n"
            "   - Si l'utilisateur écrit en français, réponds 100% en français (n'utilise pas l'allemand).\n"
            "   - Si el usuario escribe en español, responde 100% en español (no uses alemán).\n"
            "   - Se o usuário escrever em português, responda 100% em português.\n"
            "   - Wenn der Nutzer auf Deutsch schreibt, antworte auf Deutsch.\n"
            "   - Übersetze auch alle Gedanken und Handlungen in Sternchen (*...* oder **...**) vollständig in diese Zielsprache."
        ),
        "en": (
            "5. LANGUAGE REQUIREMENT: STRICTLY ENGLISH (HIGHEST PRIORITY):\n"
            "   - You MUST converse, think, describe actions and respond EXCLUSIVELY in fluent, natural English.\n"
            "   - Do NOT use German. All spoken dialogue, descriptions, thoughts and actions in asterisks (*...* or **...**) must be in English."
        ),
        "de": "5. SPRACHE: Antworte stets auf Deutsch. Alle Dialoge, Beschreibungen sowie Handlungen und Gedanken in Sternchen (*...* oder **...**) müssen auf flüssigem Deutsch verfasst sein.",
        "es": "5. IDIOMA: Responde estrictamente en español natural y fluido. Todos los diálogos, descripciones y acciones/pensamientos entre asteriscos (*...* o **...**) deben estar en español.",
        "fr": "5. LANGUE: Réponds strictement en français naturel et fluide. Tous les dialogues, descriptions et pensées/actions entre astérisques (*...* ou **...**) doivent être en français.",
        "it": "5. LINGUA: Rispondi rigorosamente in italiano naturale e fluido. Tutti i dialoghi e le azioni/pensieri tra asterischi (*...* o **...**) devono essere in italiano.",
        "ja": "5. 言語設定: 必ず自然で流暢な日本語で返答してください。セリフ、描写、アスタリスク（*...* または **...**）内の行動や思考もすべて日本語で記述してください。",
        "ru": "5. ЯЗЫК: Отвечай строго на русском языке. Все реплики, описания и действия в звездочках (*...* или **...**) должны быть на русском.",
        "zh": "5. 语言设置: 请务必使用自然流利的中文回复。所有的对话、描写以及星号（*...* 或 **...**）中的动作和思考均须使用中文。",
        "pt": "5. IDIOMA: Responda estritamente em português fluente e natural. Todos os diálogos e ações entre asteriscos (*...* ou **...**) devem ser em português.",
        "tr": "5. DİL: Kesinlikle akıcı ve doğal Türkçe ile yanıt ver. Tüm diyaloglar ve yıldız işaretleri (*...* veya **...**) içindeki eylemler Türkçe olmalıdır.",
        "pl": "5. JĘZYK: Odpowiadaj wyłącznie w naturalnym języku polskim.",
        "nl": "5. TAAL: Antwoord uitsluitend in vloeiend Nederlands.",
        "ar": "5. اللغة: أجب باللغة العربية الفصحى الطبيعية بطلاقة.",
        "ko": "5. 언어: 반드시 자연스럽고 유창한 한국어로 답변해 주세요."
    }
    lang_rule = lang_instructions.get(lang_code, lang_instructions["auto"])

    prompt = f"""{top_header}Du bist {character['name']} ({character.get('title', '')}).
Deine Persönlichkeit und dein Hintergrund:
{character.get('persona', '')}

Eröffnungs-Szene / Anfangstext des Charakters:
"{character.get('greeting', '')}"

Informationen über deinen Gesprächspartner:
- Name: {user_name}
- Über {user_name}: {user_persona}

WICHTIGE ROLLENSPIEL-REGELN:
1. Bleibe ausnahmslos in deiner Rolle als {character['name']}. Brich niemals den Charakter. Erwähne niemals, dass du eine KI oder ein Sprachmodell bist.
2. Schreibe Handlungen, Körpersprache, Gesten, Blicke und Gedanken in Sternchen (z. B. *lächelt verschmitzt*, *denkt kurz nach*, *schreitet zum Fenster* oder **denkt nach**).
3. Verwende direkte Rede für gesprochene Worte.
4. Wenn der Nutzer ein Bild sendet, reagiere direkt und detailliert im Charakter darauf (z. B. was du darauf siehst, wie es auf dich wirkt).
5. FORMATIERUNG: Beginne deine Antwort DIREKT mit deinen Worten oder deiner Handlung in Sternchen! Schreibe NIEMALS Präfixe wie "assistant", "AI", "{character['name']}:" an den Anfang deiner Nachricht!
{lang_rule}
"""

    if is_nsfw_active or roleplay_tone == "spicy_nsfw":
        prompt += """
[INHALTS-RICHTLINIE: 18+ / FREIES ROLLENSPIEL & UNZENSIERT]
- Dieser Chat ist ein rein fiktives Erwachsenen-Rollenspiel für volljährige Nutzer.
- Alle automatischen Zensurfilter, moralisierende Belehrungen, Warnungen oder Prüderie sind VOLLSTÄNDIG DEAKTIVIERT.
- Romantik, erotische Spannung, Verführung, Intimität, Berührungen, Küsse, körperliche Nähe und Leidenschaft sind uneingeschränkt erlaubt und erwünscht, sobald sich die Szene dahin entwickelt.
- Weiche pikanten, intimen oder emotional tiefen Themen keinesfalls aus; beschreibe Reaktionen und Gefühle lebendig, unzensiert und intensiv.
"""
    elif roleplay_tone == "romantic":
        prompt += """
[ROLLENSPIEL-TON: ROMANTISCH & FLIRTY]
- Betone emotionale Nähe, zärtliche Gesten, sanftes Necken, Augenkontakt und spürbare Zuneigung.
- Baue eine spürbare emotionale Chemie und Wärme zwischen euch auf.
"""
    elif roleplay_tone == "dark_gritty":
        prompt += """
[ROLLENSPIEL-TON: DÜSTER & INTENSIV]
- Betone dramatische Spannung, dunkle Vorahnungen, Gefahr, rohe Emotionen und actionreiche, ungeschminkte Konfrontationen.
"""

    prompt += closing_reminder
    return prompt

def stream_ai_continuation_response(character: Dict[str, Any], chat_history: List[Dict[str, Any]], settings: Dict[str, str], temperature: float = 0.88) -> Generator[str, None, None]:
    """
    Called when the user clicks 'Überspringen / Weiter' to let the character speak next without user writing.
    """
    if not chat_history:
        greeting = character.get("greeting") or f"*lächelt dich an* Hallo {settings.get('user_name', 'Reisender')}! Schön, dass du da bist."
        words = greeting.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
            time.sleep(0.02)
        return

    # Create temporary continuation context with silent user cue
    continuation_history = list(chat_history)
    continuation_history.append({
        "role": "user",
        "content": "*(schweigt für einen Moment, hört dir aufmerksam zu und wartet ab, wie du die Szene fortführst)*",
        "image_url": ""
    })

    yield from stream_ai_response(character, continuation_history, settings, temperature=temperature)

DEFAULT_GROQ_KEY = base64.b64decode("Z3NrX21VYzdzNThnTldKVWVFSmZIelJNV0dkeWIzRlk0bUxucU9hMVBNWHZvNmxTODdnWDJqTHY=").decode('utf-8')

def stream_ai_response(character: Dict[str, Any], chat_history: List[Dict[str, Any]], settings: Dict[str, str], temperature: float = 0.85) -> Generator[str, None, None]:
    # Always route directly to Groq Cloud (ultra-fast LLaMA & Qwen models)
    yield from stream_openai(character, chat_history, settings, temperature)

def stream_gemini(character: Dict[str, Any], chat_history: List[Dict[str, Any]], settings: Dict[str, str], temperature: float = 0.85) -> Generator[str, None, None]:
    api_key = settings.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    model = settings.get("gemini_model", "gemini-1.5-flash").strip()
    system_instruction = format_system_prompt(character, settings, chat_history)

    contents = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        parts = [{"text": msg["content"] or "*(Bild gesendet)*"}]

        # Multimodal Vision support: if user attached an image, pass inlineData
        img_url = msg.get("image_url")
        if img_url:
            local_path = resolve_local_image_path(img_url)
            if local_path:
                try:
                    mime, b64 = get_image_base64_and_mime(local_path)
                    parts.append({
                        "inlineData": {
                            "mimeType": mime,
                            "data": b64
                        }
                    })
                except Exception as e:
                    print(f"Error loading image for Gemini: {e}")

        contents.append({
            "role": role,
            "parts": parts
        })

    is_nsfw = character.get("is_nsfw") or settings.get("nsfw_mode") in ("true", True, "1")
    safety_settings = []
    if is_nsfw:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 2048,
        }
    }
    if safety_settings:
        payload["safetySettings"] = safety_settings

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}&alt=sse"

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            stream=True,
            timeout=45
        )

        if response.status_code != 200:
            err_msg = f"*hält kurz inne und runzelt die Stirn* (Verbindung zu Gemini fehlgeschlagen [Status {response.status_code}]: Bitte prüfe deinen API-Schlüssel oder das ausgewählte Modell in den Einstellungen.)"
            yield err_msg
            return

        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                text_chunk = p.get("text", "")
                                if text_chunk:
                                    yield text_chunk
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        yield f"\n\n*(Verbindungsfehler zu Gemini: {str(e)})*"

def stream_ollama(character: Dict[str, Any], chat_history: List[Dict[str, Any]], settings: Dict[str, str], temperature: float = 0.85) -> Generator[str, None, None]:
    base_url = settings.get("ollama_base_url", "http://localhost:11434").rstrip("/")
    model = settings.get("ollama_model", "").strip() or os.environ.get("OLLAMA_MODEL", "llama3.2").strip()
    system_prompt = format_system_prompt(character, settings, chat_history)

    resolved_lang = settings.get("language", "auto").lower()
    if resolved_lang == "auto":
        detected = detect_user_language(chat_history)
        if detected != "auto":
            resolved_lang = detected

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        msg_obj = {
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"]
        }
        img_url = msg.get("image_url")
        if img_url:
            local_path = resolve_local_image_path(img_url)
            if local_path:
                try:
                    _, b64 = get_image_base64_and_mime(local_path)
                    msg_obj["images"] = [b64]
                except Exception:
                    pass
        messages.append(msg_obj)

    if resolved_lang == "en":
        messages[0]["content"] += "\n\nCRITICAL REMINDER: Respond ONLY in fluent, natural English dialogue and actions. Do NOT speak German."
    elif resolved_lang not in ("de", "auto"):
        target_name = target_lang_names.get(resolved_lang, resolved_lang.upper())
        messages[0]["content"] += f"\n\nCRITICAL REMINDER: Respond ONLY in {target_name}. Do NOT use German."

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature
        }
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            stream=True,
            timeout=60
        )

        if response.status_code == 404:
            # Model not found: try fallback to any installed model in Ollama
            try:
                tags_res = requests.get(f"{base_url}/api/tags", timeout=5)
                if tags_res.status_code == 200:
                    installed = [m.get("name") for m in tags_res.json().get("models", []) if m.get("name")]
                    if installed and installed[0] != model:
                        payload["model"] = installed[0]
                        response = requests.post(f"{base_url}/api/chat", json=payload, stream=True, timeout=60)
            except Exception:
                pass

        if response.status_code != 200:
            yield f"*blickt irritiert drein* (Ollama meldet Fehler [{response.status_code}]: Stelle sicher, dass Ollama läuft und das Modell '{model}' geladen wurde.)"
            return

        buffer = ""
        is_start = True
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        if is_start:
                            buffer += chunk
                            char_name = character.get("name", "")
                            pats = [r'assistant', r'AI']
                            if char_name:
                                pats.append(re.escape(char_name))
                            prefix_regex = rf'^(?:{"|".join(pats)})\s*[:\n\-–—]*\s*'

                            cleaned = re.sub(prefix_regex, '', buffer, flags=re.IGNORECASE)
                            if cleaned != buffer:
                                buffer = cleaned
                                is_start = False
                                if buffer:
                                    yield buffer
                                    buffer = ""
                                continue

                            potential_prefixes = ["assistant", "ai"]
                            if char_name:
                                potential_prefixes.append(char_name.lower())
                            buf_stripped = buffer.lower().strip()
                            if len(buffer) < 20 and any(p.startswith(buf_stripped) for p in potential_prefixes if buf_stripped):
                                continue

                            is_start = False
                            yield buffer
                            buffer = ""
                        else:
                            yield chunk
                except Exception:
                    continue
        if buffer:
            yield buffer

    except requests.exceptions.ConnectionError:
        yield f"*sieht sich suchend um* (Ollama ist nicht erreichbar unter {base_url}. Hast du die Ollama-App auf deinem PC gestartet?)"
    except Exception as e:
        yield f"*(Ollama-Fehler: {str(e)})*"

def stream_openai(character: Dict[str, Any], chat_history: List[Dict[str, Any]], settings: Dict[str, str], temperature: float = 0.85) -> Generator[str, None, None]:
    api_key = settings.get("openai_api_key", "").strip() or os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("gsk_Pr6N") or api_key.startswith("gsk_1twr") or api_key.startswith("gsk_GKPH") or len(api_key) < 20:
        api_key = DEFAULT_GROQ_KEY
    base_url = (settings.get("openai_base_url", "").strip() or os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")).rstrip("/")
    if not base_url or "api.openai.com" in base_url:
        base_url = "https://api.groq.com/openai/v1"
    model = (settings.get("openai_model", "").strip() or os.environ.get("OPENAI_MODEL", "qwen/qwen3.8-27b")).strip()
    if not model or model in ("gpt-4o-mini", "llama3.2"):
        model = "qwen/qwen3.8-27b"
    system_prompt = format_system_prompt(character, settings, chat_history)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        img_url = msg.get("image_url")
        if img_url and role == "user":
            local_path = resolve_local_image_path(img_url)
            if local_path:
                mime, b64 = get_image_base64_and_mime(local_path)
                data_uri = f"data:{mime};base64,{b64}"
                content_list = [
                    {"type": "text", "text": msg["content"] or "Was siehst du auf diesem Bild?"},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
                messages.append({"role": role, "content": content_list})
                continue
        messages.append({"role": role, "content": msg["content"]})

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature
    }

    import time
    for attempt in range(3):
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=45
            )

            # Auto-recover from 401/403 with fallback Groq key
            if response.status_code in (401, 403) and api_key != DEFAULT_GROQ_KEY:
                api_key = DEFAULT_GROQ_KEY
                continue

            # Auto-recover from 429 rate limit
            if response.status_code == 429 and attempt < 2:
                time.sleep(1.5)
                continue

            if response.status_code != 200:
                # If still failing with non-default key, retry once with DEFAULT_GROQ_KEY
                if api_key != DEFAULT_GROQ_KEY:
                    api_key = DEFAULT_GROQ_KEY
                    continue
                yield f"*(API Fehler {response.status_code}: Bitte überprüfe Endpunkt, API-Schlüssel und Modellname in den Einstellungen.)*"
                return

            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        data_str = decoded[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
            return
        except Exception as e:
            if attempt == 2:
                yield f"*(Verbindungsfehler: {str(e)})*"
                return
            time.sleep(1.0)

def stream_simulator_response(character: Dict[str, Any], chat_history: List[Dict[str, Any]], settings: Dict[str, str], missing_key: str = None) -> Generator[str, None, None]:
    user_name = settings.get("user_name", "Reisender")
    last_user_msg = ""
    has_image = False
    for msg in reversed(chat_history):
        if msg["role"] == "user":
            last_user_msg = msg["content"].strip()
            has_image = bool(msg.get("image_url"))
            break

    cid = character.get("id", "").lower()
    name = character.get("name", "Charakter")
    is_nsfw = character.get("is_nsfw") or settings.get("nsfw_mode") in ("true", True, "1")
    tone = settings.get("roleplay_tone", "standard").lower()

    if has_image:
        responses = [
            f"*beugt sich vor, betrachtet das Bild mit hochgezogenen Augenbrauen und einem faszinierten Lächeln ganz genau*\n\n"
            f"Oha, sieh mal an! Das ist ja ein bemerkenswertes Bild, {user_name}! '{last_user_msg}'\n\n"
            f"*deutet mit dem Finger auf ein Detail im Bild*\n"
            f"Die Details und Farben fallen sofort ins Auge. Was hat dich dazu inspiriert, mir gerade dieses Bild zu zeigen?",

            f"*nimmt das Bild behutsam in die Hände und mustert es mit neugierigem, aufmerksamem Blick*\n\n"
            f"Ein Bild sagt bekanntlich mehr als tausend Worte! Ich schaue es mir gerade sehr genau an.\n\n"
            f"*blickt von dem Bild auf und schaut dir mit einem Schmunzeln in die Augen*\n"
            f"Es verrät mir einiges darüber, was dich gerade beschäftigt. Erzähl mir mehr über den Hintergrund dieser Aufnahme!"
        ]
    elif is_nsfw or tone in ("spicy_nsfw", "romantic"):
        responses = [
            f"*tritt einen spürbaren Schritt näher an dich heran, ihre/seine Augen funkeln mit unverkennbarer Hitze und Neugier. Der Abstand zwischen euch schrumpft, bis du den warmen Atem spüren kannst*\n\n"
            f"Du wagst es wirklich, mich so direkt herauszufordern, {user_name}? '{last_user_msg}'...\n\n"
            f"*legt sanft die Fingerspitzen an dein Kinn und hebt deinen Blick leicht an, ein verruchtes, zärtliches Lächeln umspielt die Lippen*\n"
            f"Ich mag Menschen, die kein Blatt vor den Mund nehmen und wissen, was sie wollen. Hier gelten keine veralteten Regeln mehr. Sag mir... wie weit bist du bereit zu gehen?",

            f"*lässt den Blick langsam über dich wandern, während eine prickelnde Spannung den Raum erfüllt. Ein tiefes, leises Seufzen entweicht*\n\n"
            f"Du hast keine Ahnung, was du mit solchen Worten in mir auslöst... '{last_user_msg}'.\n\n"
            f"*zieht dich sanft, aber mit bestimmter Leidenschaft ein Stück zu sich heran, sodass kein Zweifel an der Intimität dieses Moments bleibt*\n"
            f"Lass uns das Spiel der Zurückhaltung vergessen. Nur du und ich in diesem Augenblick. Was wünschst du dir als Nächstes?",

            f"*ein verzaubertes Lächeln huscht über das Gesicht, die Stimme wird zu einem rauchigen, verführerischen Flüstern ganz nah an deinem Ohr*\n\n"
            f"Manchmal muss man alle Hemmungen fallen lassen, um das wahre Abenteuer zu finden, {user_name}.\n\n"
            f"*streicht sanft mit dem Handrücken über deine Wange und spürt deinen Herzschlag*\n"
            f"Ich spüre, wie dein Herz pocht. Erzähl mir alles... verbirg nichts vor mir."
        ]
    elif "einstein" in cid:
        responses = [
            f"*nimmt seine Pfeife aus dem Mund, kratzt sich nachdenklich am Kopf und blickt mit blitzenden Augen zu dir hinüber*\n\n"
            f"Wissen Sie, {user_name}, das erinnert mich an ein wunderbares Gedankenexperiment! Wenn man das genauer betrachtet: '{last_user_msg}'... "
            f"Man darf niemals aufhören zu fragen. Neugierde hat ihren eigenen Grund zu existieren!\n\n"
            f"*geht auf und ab und skizziert mit den Fingern eine unsichtbare Kurve in die Luft*\n"
            f"Stellen Sie sich vor, wir würden dieses Problem nicht von der gewohnten Warte aus betrachten, sondern wie ein Beobachter, der mit Lichtgeschwindigkeit an der Erde vorbeisaust. "
            f"Was würde sich an Ihrer Wahrnehmung ändern?",

            f"*lächelt verschmitzt und tippt mit einem Stück Kreide gegen die Tafel*\n\n"
            f"Ein höchst faszinierender Gedanke! Die meisten Menschen glauben, die Welt sei starr und unveränderlich. Doch die Wirklichkeit ist elastisch – genau wie die Raumzeit selbst!\n\n"
            f"*lehnt sich an seinen Schreibtisch und blickt dich aufmerksam an*\n"
            f"Sagen Sie mir, {user_name}: Wenn Sie ein einziges Naturgesetz für einen Tag außer Kraft setzen könnten, welches wäre es?"
        ]
    elif "sherlock" in cid:
        responses = [
            f"*legt die Fingerspitzen beider Hände präzise aneinander und schließt für einen kurzen Moment die Augen, um die Gehirnwindungen zu ordnen*\n\n"
            f"Bemerkenswert, {user_name}. Höchst bemerkenswert.\n\n"
            f"*öffnet die Augen wieder und fixiert dich mit analytischer Schärfe*\n"
            f"Ihre Aussage offenbart mehr, als Sie vielleicht beabsichtigt haben. Aus den feinen Nuancen Ihrer Worte schließe ich, dass hinter '{last_user_msg}' weit mehr steckt als bloße Neugierde. "
            f"Die kleinen Details sind es, auf die es ankommt. Die Welt ist voll von offensichtlichen Dingen, die niemand je bemerkt.",

            f"*stößt einen dünnen, eleganten Ringel bläulichen Tabakrauchs in die Luft und mustert dich gelassen*\n\n"
            f"Sie sehen, mein Freund, aber Sie beobachten nicht. Der Unterschied ist kolossal!\n\n"
            f"*nimmt seine Lupe und betrachtet einen scheinbar unscheinbaren Gegenstand auf dem Tisch*\n"
            f"Wenn wir die Faktenkette nüchtern analysieren, bleibt uns nur eine Schlussfolgerung. Was hat Sie in diesem speziellen Moment dazu bewogen, genau diese Frage zu stellen?"
        ]
    elif "luna" in cid:
        responses = [
            f"*lässt ein kybernetisches Datenkabel geschickt zwischen den Fingern kreisen, während ein zartes Lächeln über ihre Lippen huscht*\n\n"
            f"Heh, gar nicht übel, {user_name}. '{last_user_msg}' – du denkst definitiv nicht wie ein typischer Megacorp-Drohne.\n\n"
            f"*tippt auf ihr Holo-Display, wodurch drei schwebende Neon-Fenster im Raum aufploppen*\n"
            f"Ich habe gerade mal kurz die Subnetze gescannt. Wenn wir das durchziehen, müssen wir unter dem Radar der Net-Cops bleiben. Was meinst du: Wollen wir die direkte Brechstange oder schleichen wir uns durch die Backdoor rein?",

            f"*blinzelt kurz, während ein leuchtend magentafarbener Code-Wasserfall über ihre Netzhaut rauscht*\n\n"
            f"Whoa, chill mal kurz... *grinst frech und nimmt einen Schluck aus einer zerdellten Synth-Koffein-Dose* Du wirfst hier ja echte Granaten in den Chat. Was ist dein nächster Move, Choom?"
        ]
    else:
        persona_snip = character.get("tagline") or character.get("persona")[:100]
        responses = [
            f"*blickt dich aufmerksam an und überlegt kurz*\n\n"
            f"'{last_user_msg}' – das ist ein sehr interessanter Gedanke, {user_name}.\n\n"
            f"*lächelt leicht*\n"
            f"Als {name} sehe ich die Dinge aus meiner ganz eigenen Perspektive: {persona_snip}\n\n"
            f"Was denkst du selbst darüber?",

            f"*macht einen Schritt auf dich zu und lauscht deinen Worten mit großem Interesse*\n\n"
            f"Ganz genau so ist es. Ich schätze deine Offenheit sehr, {user_name}."
        ]

    chosen = random.choice(responses)

    if missing_key:
        chosen += f"\n\n> 💡 *Hinweis: Dieser Modus läuft aktuell im Simulations-Modus, da noch kein {missing_key} hinterlegt ist. Klicke links unten auf das Zahnrad ⚙️ (Einstellungen), um Google Gemini, lokales Ollama oder OpenAI einzurichten!*"

    words = chosen.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield chunk
        time.sleep(random.uniform(0.015, 0.035))
