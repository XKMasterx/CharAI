https://charai-mus8.onrender.com/
---
title: CharAI
emoji: 🎭
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🎭 CharAI Local – Dein eigener Character.ai Klon

Ein moderner, voll ausgestatteter **Character.ai-Klon**, der komplett lokal auf deinem Windows-PC läuft.

Er bietet das originale **Character.ai-Erlebnis**: Individuelle Persönlichkeiten, lebendiges Rollenspiel mit typischer `*Handlungs-*`Formatierung, alternative Antworten (**Swipes**), eigene Charaktererstellung mit **automatischer Internet-Recherche**, **Bild-Uploads (Avatar & Chat)**, **NSFW / 18+ Unzensiert-Einstellungen**, Sprachausgabe und flexible KI-Backends.

---

## ✨ Features im Überblick

- 📸 **NEU: Bild-Uploads (Avatar & Chat):**
  - **Eigener Avatar vom PC:** Lade beim Erstellen oder Bearbeiten eines Charakters beliebige Bilder (`.png`, `.jpg`, `.webp`, `.gif`) direkt von deiner Festplatte hoch oder ziehe sie per Drag & Drop auf den Avatar-Kreis.
  - **Bilder im Chat mitsenden:** Hänge Fotos, Zeichnungen oder Memes per Knopfdruck (📷) an deine Nachricht an.
  - **Zwischenablage / Screenshot einfügen (Strg + V):** Mache einfach einen Screenshot und drücke `Strg + V` im Chat – das Bild wird sofort angehängt!
  - **Multimodale KI-Erkennung (Vision):** Wenn du Google Gemini (`gemini-1.5-flash` / `gemini-2.0-flash`) oder OpenAI nutzt, **sieht der Charakter dein Bild tatsächlich** und reagiert detailgenau darauf! Auch der Offline-Simulator reagiert stimmig.
  - **Lightbox:** Klicke auf ein Bild im Chat, um es in voller Größe anzusehen.

- 🌐 **Internet-Recherche & Auto-Profil:**
  - Gib beim Erstellen eines Charakters einfach den Namen einer bekannten Person oder fiktiven Figur ein (z. B. *Nikola Tesla*, *Napoleon*, *Geralt von Riva*, *Cleopatra*, *Marilyn Monroe*, *Elon Musk*).
  - Ein Klick auf **Recherchieren** durchsucht Wikipedia und füllt **Name, Titel, Biografie, Zitat, echtes Foto als Avatar und den Anfangstext (Start-Szene)** automatisch aus! Keine umständlichen Beispieldialoge nötig!

- 🔞 **18+ / NSFW & Unzensiert-Modus:**
  - **Charakter-NSFW-Schalter:** Markiere einzelne Charaktere als `🔞 18+`, wodurch sie ein sichtbares Badge erhalten und Inhaltsfilter deaktiviert werden.
  - **Globaler NSFW-Modus (in den Einstellungen):** Schaltet Zensurfilter für alle Unterhaltungen ab.
  - **Einstellbarer Rollenspiel-Ton:**
    - *Standard / Ausgewogen:* Authentische, originalgetreue Persönlichkeit.
    - *Romantisch & Flirty:* Sanfte Nähe, Zärtlichkeit, tiefe Blicke & Necken.
    - *18+ Leidenschaftlich & Unzensiert:* Volle Freiheit für intime, erotische und ungefilterte Szenen ohne Moralbelehrungen.
    - *Düster & Intensiv:* Dramatische Spannung, Gefahr und rohe Konfrontationen.

- 🎭 **Vorinstallierte Charaktere:**
  - Albert Einstein, Sherlock Holmes, Luna Sterling (Cyberpunk-Netrunnerin), Aria Mondschleier (Magierin), Marcus Aurelius (Stoiker) und Echo (Kreativ-Begleiterin).

- 🔄 **Original Character.ai Swipes (`< 1/3 >`):**
  - Generiere alternative Antworten per Klick auf **Neu generieren** und blättere durch verschiedene Variationen.

- 💬 **Neuer Chat (Mit oder ohne Anfangstext):**
  - Wähle beim Klick auf **+** (Neuer Chat) flexibel zwischen **„Mit Anfangstext“** (der Charakter beginnt) oder **„Ohne Anfangstext“** (ein komplett leerer Chat, bei dem du das Gespräch eröffnest).

- 🎨 **Authentisches Roleplay-Design:**
  - Handlungen, Gesten und Gedanken in `*Sternchen*` werden automatisch in stilvollem Lavendel-Italic hervorgehoben.

- ⚡ **Multi-KI-Backend:**
  - **Smarte Simulation (Standard):** Funktioniert **sofort offline** ohne API-Schlüssel oder Setup. Reagiert auch auf Bilder und im NSFW-Modus!
  - **Google Gemini:** Kostenlos, extrem schnell & **multimodal mit Bild-Erkennung** via Google AI Studio.
  - **Ollama:** 100% lokal & privat auf deiner GPU/CPU (`llama3.2`, `mistral`, `llava`).
  - **OpenAI / Groq / LM Studio / OpenRouter:** Kompatibel mit jedem OpenAI-kompatiblen Endpunkt.

- 📁 **Import & Export (TavernAI / Character.ai Standard):**
  - Exportiere deine Charaktere als `.json` oder importiere fertige Charakterkarten aus der Community.

- 🔊 **Integrierte Sprachausgabe:**
  - Antworten können per Knopfdruck vorgelesen werden.

---

## 🚀 Schnellstart

### 1. Per 1-Klick Startdatei (Windows):
Im Ordner `C:\Users\EpicS\.gemini\antigravity\scratch\character-ai-clone` einfach doppelt klicken auf:
👉 **`run.bat`**

### 2. Oder manuell im Terminal:
```powershell
cd C:\Users\EpicS\.gemini\antigravity\scratch\character-ai-clone
python app.py
```

Der Server startet sofort und öffnet automatisch deinen Webbrowser unter:
🌐 **`http://127.0.0.1:8000`**
