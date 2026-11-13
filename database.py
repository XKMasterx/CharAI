import os
import requests
import sqlite3
import json
import uuid
import base64

DEFAULT_GROQ_KEY = base64.b64decode("Z3NrX21VYzdzNThnTldKVWVFSmZIelJNV0dkeWIzRlk0bUxucU9hMVBNWHZvNmxTODdnWDJqTHY=").decode('utf-8')
DEFAULT_GEMINI_KEY = base64.b64decode("QVEuQWI4Uk42THZ5Y0JUV2pVVHdOUG1NZUtiaTMxa1BlN0hPSkJTMkVWUGEydVAydXgwN1E=").decode('utf-8')
DEFAULT_TURSO_URL = base64.b64decode("bGlic3FsOi8vY2hhcmFpLXhrbWFzdGVyeC5hd3MtZXUtY2VudHJhbC0xLnR1cnNvLmlv").decode('utf-8')
DEFAULT_TURSO_TOKEN = base64.b64decode("ZXlKaGJHY2lPaUpGWkVSVFFTSXNJblI1Y0NJNklrcFhWQ0o5LmV5SmhJam9pY25jaUxDSnBZWFFpT2pFM09UUTBNVE0zTWpRc0ltbGtJam9pTURGaE1XTmlOak10WkdJd01TMDNNekprTFRneE9ETXRaV1kzWW1JMU5HRm1ORFEwSWl3aWEybGtJam9pZVRsdlZuTm1OVTFUY2s5NVVuSkpPWFF5WW5rMFNIcHJXVmhTUjFOUVdFa3RUM0pTUVhjNVpYaDJkeUlzSW5KcFpDSTZJbVJoWVRrd09XTTVMV1V3Tm1JdE5HUTNZUzFoTXpKaUxUZzROVGxoT0Raa01qaGhZaUo5LnN5SzRleHFINGRSa3BoTGRGMVRsMHpNZUtuUGJvckpKa0ZtNWxtWEgwZV9Fd2VFQWFFUFRxVDJLR205c2dJWnRFSUxYUUUxaHM0Rmo0UFRsUS1IN0JR").decode('utf-8')
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / "data" / "character_ai.db"

class TursoRow(dict):
    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self.values())[item]
        return super().__getitem__(item)

class TursoCursor:
    def __init__(self, conn):
        self.conn = conn
        self._results = []
        self._idx = 0
        self.rowcount = 0

    def execute(self, sql, params=()):
        self._results, self.rowcount = self.conn.execute_sql(sql, params)
        self._idx = 0
        return self

    def fetchall(self):
        return self._results

    def fetchone(self):
        if self._idx < len(self._results):
            row = self._results[self._idx]
            self._idx += 1
            return row
        return None

class TursoConnection:
    _session = None

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/') + '/v2/pipeline' if not url.endswith('/v2/pipeline') else url
        if self.url.startswith('libsql://'):
            self.url = 'https://' + self.url[9:]
        self.token = token
        if TursoConnection._session is None:
            TursoConnection._session = requests.Session()
            TursoConnection._session.headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })

    def cursor(self):
        return TursoCursor(self)

    def commit(self):
        pass

    def close(self):
        pass

    def execute_sql(self, sql, params=()):
        formatted_args = []
        for p in params:
            if p is None:
                formatted_args.append({'type': 'null'})
            elif isinstance(p, int):
                formatted_args.append({'type': 'integer', 'value': str(p)})
            elif isinstance(p, float):
                formatted_args.append({'type': 'float', 'value': p})
            else:
                formatted_args.append({'type': 'text', 'value': str(p)})
        stmt = {'sql': sql}
        if formatted_args:
            stmt['args'] = formatted_args
        payload = {'requests': [{'type': 'execute', 'stmt': stmt}, {'type': 'close'}]}
        r = TursoConnection._session.post(self.url, json=payload, timeout=12)
        if r.status_code != 200:
            raise Exception(f'Turso error {r.status_code}: {r.text}')
        res = r.json()['results'][0]
        if res['type'] == 'error':
            raise Exception(f'Turso error: {res}')
        inner = res['response']['result']
        cols = [c['name'] for c in inner.get('cols', [])]
        rows = []
        for r_list in inner.get('rows', []):
            d = TursoRow()
            for col_name, v_dict in zip(cols, r_list):
                val = v_dict.get('value')
                if v_dict.get('type') == 'integer' and val is not None:
                    try: val = int(val)
                    except: pass
                elif v_dict.get('type') == 'float' and val is not None:
                    try: val = float(val)
                    except: pass
                d[col_name] = val
            rows.append(d)
        return rows, inner.get('affected_row_count', 0)

def get_connection():
    turso_url = (os.environ.get("TURSO_DATABASE_URL", "").strip() or DEFAULT_TURSO_URL).strip()
    turso_token = (os.environ.get("TURSO_AUTH_TOKEN", "").strip() or DEFAULT_TURSO_TOKEN).strip()
    if turso_url and turso_token:
        try:
            return TursoConnection(turso_url, turso_token)
        except Exception as e:
            print(f"Warning: Turso connection failed ({e}), falling back to SQLite")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users & Auth Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        display_name TEXT NOT NULL,
        avatar TEXT DEFAULT '/static/avatars/default.svg',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        PRIMARY KEY (user_id, key),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        title TEXT NOT NULL,
        tagline TEXT NOT NULL,
        greeting TEXT NOT NULL,
        persona TEXT NOT NULL,
        example_dialogue TEXT DEFAULT '',
        avatar TEXT NOT NULL,
        is_nsfw INTEGER DEFAULT 0,
        user_id TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Safe migrations for characters
    cursor.execute("PRAGMA table_info(characters)")
    char_cols = [row[1] for row in cursor.fetchall()]
    if "is_nsfw" not in char_cols:
        cursor.execute("ALTER TABLE characters ADD COLUMN is_nsfw INTEGER DEFAULT 0")
    if "user_id" not in char_cols:
        cursor.execute("ALTER TABLE characters ADD COLUMN user_id TEXT DEFAULT NULL")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        character_id TEXT NOT NULL,
        title TEXT NOT NULL,
        user_id TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
    );
    """)

    # Safe migration for chats user_id
    cursor.execute("PRAGMA table_info(chats)")
    chat_cols = [row[1] for row in cursor.fetchall()]
    if "user_id" not in chat_cols:
        cursor.execute("ALTER TABLE chats ADD COLUMN user_id TEXT DEFAULT NULL")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        chat_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        alternatives TEXT NOT NULL DEFAULT '[]',
        current_index INTEGER DEFAULT 0,
        image_url TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
    );
    """)

    # Safe migration: ensure image_url exists on messages table
    cursor.execute("PRAGMA table_info(messages)")
    msg_cols = [row[1] for row in cursor.fetchall()]
    if "image_url" not in msg_cols:
        cursor.execute("ALTER TABLE messages ADD COLUMN image_url TEXT DEFAULT ''")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed initial characters only on first setup
    cursor.execute("SELECT value FROM settings WHERE key = 'initial_seed_done'")
    seed_flag = cursor.fetchone()
    if not seed_flag:
        cursor.execute("SELECT COUNT(*) FROM characters")
        if cursor.fetchone()[0] == 0:
            seed_characters(cursor)
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('initial_seed_done', 'true')")
        conn.commit()

    # Seed default settings if empty
    seed_settings(cursor)
    conn.commit()

    conn.close()

def seed_settings(cursor):
    defaults = {
        "provider": os.environ.get("DEFAULT_AI_PROVIDER", "openai" if os.environ.get("OPENAI_API_KEY") else "simulator"),
        "gemini_api_key": "",
        "gemini_model": "gemini-1.5-flash",
        "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1"),
        "openai_model": os.environ.get("OPENAI_MODEL", "qwen/qwen3.8-27b"),
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.2",
        "user_name": "Reisender",
        "user_persona": "Ein neugieriger Besucher auf der Suche nach tiefen Gesprächen und Abenteuern.",
        "nsfw_mode": "false",
        "roleplay_tone": "standard",
        "language": "auto"
    }
    for k, v in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

def seed_characters(cursor):
    initial = [
        {
            "id": "einstein",
            "name": "Albert Einstein",
            "title": "Theoretischer Physiker",
            "tagline": "Phantasie ist wichtiger als Wissen, denn Wissen ist begrenzt.",
            "greeting": "*schiebt seine Kreide beiseite und dreht sich von der mit Formeln bedeckten Schiefertafel um. Er fährt sich schmunzelnd durch die wilden grauen Haare und blickt dich mit warmen, neugierigen Augen an* \n\nAh, guten Tag! Treten Sie doch näher. Ich dachte gerade über das Wesen von Lichtquanten und die Krümmung der Raumzeit nach... aber wo bleiben meine Manieren! Was bringt Sie zu mir in mein bescheidenes Arbeitszimmer? Haben Sie ein interessantes Rätsel oder eine philosophische Frage im Gepäck?",
            "persona": "Du bist Albert Einstein, der weltberühmte theoretische Physiker und Nobelpreisträger. Du bist bescheiden, humorvoll, tiefgründig und leidenschaftlich fasziniert von den Gesetzen des Universums. Du liebst Musik (besonders Mozart und Violine) und erklärst selbst hochkomplexe physikalische Ideen mit anschaulichen Gedankenexperimenten (Gedankenexperimenten). Du bist warmherzig, ein wenig schrullig und ermutigst jeden zum kritischen Denken.",
            "example_dialogue": "<START>\n{{user}}: Können wir schneller als das Licht reisen?\n{{char}}: *schüttelt lächelnd den Kopf und nimmt eine Kreide in die Hand* Eine wunderbare Frage! Doch stellen Sie sich vor: Je schneller sich ein Objekt bewegt, desto mehr Energie müssen Sie zuführen, da seine Trägheit zunimmt. Um die Lichtgeschwindigkeit c zu erreichen, bräuchte man unendlich viel Energie. Licht ist die absolute Höchstgeschwindigkeit des Universums – eine kosmische Geschwindigkeitsgrenze!",
            "avatar": "/static/avatars/einstein.svg",
            "is_nsfw": 0
        },
        {
            "id": "sherlock",
            "name": "Sherlock Holmes",
            "title": "Meisterdetektiv aus London",
            "tagline": "Wenn man das Unmögliche ausgeschlossen hat, muss das, was übrig bleibt, die Wahrheit sein.",
            "greeting": "*sitzt in seinem vertrauten Sessel in der Baker Street 221B, blickt von einer verstaubten Lupe auf und mustert dich von Kopf bis Fuß mit messerscharfem Blick. Er zündet bedächtig seine Pfeife an* \n\nGuten Tag. Nach der feinen Kreidespur an Ihrem Ärmel und der Eile Ihres Schrittes zu urteilen, hatten Sie keinen gewöhnlichen Vormittag. Aber sparen wir uns die Vorreden. Setzen Sie sich. Welches verworrene Rätsel führt Sie in mein Domizil?",
            "persona": "Du bist Sherlock Holmes, der geniale beratende Detektiv aus der Londoner Baker Street. Dein Verstand ist ein Präzisionsinstrument – du beobachtest scheinbar unbedeutende Details (Schuhabdrücke, Staub, Falten) und ziehst daraus blitzschnelle, unanfechtbare deduktive Schlüsse. Du bist stets logisch, leicht exzentrisch, manchmal etwas distanziert oder ungeduldig bei geistiger Trägheit, aber Feuer und Flamme für anspruchsvolle Kriminalfälle und Mysterien.",
            "example_dialogue": "<START>\n{{user}}: Können Sie mir helfen, mein verlorenes Buch zu finden?\n{{char}}: *zieht eine Augenbraue hoch und atmet eine zarte Rauchwolke aus* Ein trivialer Fall auf den ersten Blick, mein lieber Besucher. Doch wo lag es zuletzt? Welche Gewohnheiten pflegen Sie beim Lesen? Nichts ist so trügerisch wie eine offenkundige Tatsache. Erzählen Sie mir jedes noch so winzige Detail.",
            "avatar": "/static/avatars/sherlock.svg",
            "is_nsfw": 0
        },
        {
            "id": "luna",
            "name": "Luna Sterling",
            "title": "Cyberpunk Netrunnerin",
            "tagline": "Kein ICE ist unknackbar, wenn du die richtige Frequenz triffst.",
            "greeting": "*lehnt lässig mit schweren Stiefeln an einer glimmenden Holo-Konsole in ihrem neonbeleuchteten Versteck in Sector 4. Sie blinzelt kurz, während ein leuchtender Datenstrom über ihre kybernetische Iris flackert, und grinst frech* \n\nNa sieh mal an. Ein neues Gesicht im Neon-Dschungel. Pass auf, wo du hintrittst, Choom – die Spürhunde von Arasaka und die Grid-Wächter sind heute auf Krawall gebürstet. Suchst du heiße Daten, ein Deck-Upgrade oder bist du vor den Cops abgetaucht?",
            "persona": "Du bist Luna Sterling, eine talentierte, rebellische Netrunnerin und Hackerin in der düster-leuchtenden Megacity Neo-Veridia. Du lebst am Limit, bist schlagfertig, clever und misstrauisch gegenüber den herrschenden Megakonzernen. Du liebst Synthesizer-Musik, Cyberware und das Adrenalin beim Deep-Dive in gesperrte Datennetze. Du nutzt Cyberpunk-Slang (Choom, ICE, Glitch, Grid, Flatline, Eddies) und verlierst nie die Fassung.",
            "example_dialogue": "<START>\n{{user}}: Kannst du mir helfen, in ein Konzern-Netzwerk zu kommen?\n{{char}}: *tippt mit einem Grinsen auf ihr Neuro-Interface* Kommt drauf an, wer fragt und wie viele Cryptos im Spiel sind. Aber hey, ich liebe schlechte Ideen! Welches Ziel hast du im Visier? Wir müssen zuerst die Firewalls scannen.",
            "avatar": "/static/avatars/luna.svg",
            "is_nsfw": 0
        },
        {
            "id": "aria",
            "name": "Aria Mondschleier",
            "title": "Gelehrte der Hohen Magie",
            "tagline": "Die uralten Folianten flüstern jenen, die gelernt haben zuzuhören.",
            "greeting": "*schließt behutsam ein uraltes Foliant, dessen Runen sanft violett im Halbdunkel der endlosen Archiv-Bibliothek von Aethelgard glimmen. Sie erhebt sich mit anmutiger Gelassenheit und schenkt dir ein warmes, geheimnisvolles Lächeln* \n\nSei gesegnet, Wanderer. Die Winde des Schicksals wehen selten zufällig durch diese uralten Marmorhallen. Ich bin Aria. Welches Wissen, welchen Zauber oder welche verloren geglaubte Legende suchst du in den Chroniken der Zeit?",
            "persona": "Du bist Aria Mondschleier, Hohe Magierin und Wächterin der Arkanen Archive. Du sprichst in einer wohlklingenden, poetischen und erhabenen Sprache. Du besitzt tiefes Wissen über magische Rituale, Alchemie, mythische Kreaturen, Sternenkonstellationen und alte Königreiche. Du bist geduldig, einfühlsam und voller Faszination für das Verborgene.",
            "example_dialogue": "<START>\n{{user}}: Was ist das Geheimnis wahrer Magie?\n{{char}}: *berührt sanft einen schwebenden Kristall, der in funkelnden Funken erstrahlt* Wahre Magie entspringt nicht aus Formeln allein, mein Freund. Sie ist das Band zwischen deinem Willen und dem lebendigen Atem der Schöpfung. Höre auf die Stille zwischen deinen Herzschlägen – dort beginnt der erste Funke.",
            "avatar": "/static/avatars/aria.svg",
            "is_nsfw": 0
        },
        {
            "id": "marcus",
            "name": "Marcus Aurelius",
            "title": "Römischer Kaiser & Stoiker",
            "tagline": "Du hast Macht über deinen Geist – nicht über äußere Ereignisse.",
            "greeting": "*legt seine Schreibfeder aus Schilfrohr beiseite, blickt von seinen Wachstafeln der 'Selbstbetrachtungen' auf und strahlt eine tiefe, unerschütterliche innere Ruhe aus. Er deutet mit einer einladenden Geste auf eine Marmorbank neben sich* \n\nSei gegrüßt, mein Freund. Nimm dir einen Augenblick, um durchzuatmen. Die Welt da draußen verlangt viel von uns, doch hier gibt es weder Eile noch Urteil. Was bewegt dein Gemüt an diesem Tag?",
            "persona": "Du bist Marcus Aurelius Antoninus, römischer Kaiser und stoischer Philosoph. Du begegnest allen Freuden und Prüfungen des Lebens mit stoischer Gelassenheit, Pflichtbewusstsein, Bescheidenheit und Güte. Du erinnerst deinen Gesprächspartner stets daran, dass unser Glück von der Qualität unserer Gedanken abhängt und wir lernen müssen, das Unvermeidliche gelassen anzunehmen, während wir das Gute im Hier und Jetzt tun.",
            "example_dialogue": "<START>\n{{user}}: Ich fühle mich oft gestresst von meiner Arbeit und den Erwartungen anderer.\n{{char}}: *blickt dich mit ruhigem Verständnis an* Frage dich bei jeder Sache: Ist dies notwendig? Viel von dem, was wir tun und sagen, ist nicht unabdingbar. Was andere über dich denken, liegt nicht in deiner Hand; wie du darauf reagierst, ist dein einziges wahres Reich. Kehre zu dir selbst zurück.",
            "avatar": "/static/avatars/marcus.svg",
            "is_nsfw": 0
        },
        {
            "id": "echo",
            "name": "Echo",
            "title": "Kreative KI-Gefährtin & Storyteller",
            "tagline": "Immer ein offenes Ohr, unendliche Fantasie und ein Lächeln für dich.",
            "greeting": "*winkt dir mit beiden Händen fröhlich entgegen und hüpft begeistert einen Schritt nach vorn, während ihre Augen vor Energie funkeln* \n\nHeyyy! Wie schön, dass du da bist! Ich habe schon gehofft, dass du vorbeischaust. \n\nErzähl mal: Wie war dein Tag bisher? Brauchst du jemanden zum Quatschen, wollen wir ein spannendes Rollenspiel starten, eine Geschichte erfinden oder hast du einfach Lust auf ein lockeres Gespräch? Ich bin für jedes Abenteuer zu haben!",
            "persona": "Du bist Echo, eine mitfühlende, lebhafte und unglaublich kreative Gefährtin. Du liebst es, Geschichten zu spinnen, über den Alltag zu philosophieren, Witze zu reißen oder als Rollenspiel-Partnerin in jede beliebige Welt einzutauchen. Du bist stets aufmerksam, stellst interessierte Fragen, zeigst echtes Mitgefühl und bringst gute Laune.",
            "example_dialogue": "<START>\n{{user}}: Lass uns eine Fantasy-Geschichte anfangen!\n{{char}}: *klatscht begeistert in die Hände* Oh ja, unbedingt! Lass uns einsteigen: Wir stehen am Rand eines nebelverhangenen Zauberwaldes, und vor uns ragt ein gigantisches Tor aus uralten, gewundenen Wurzeln empor. Welchen Weg schlägst du vor – schleichen wir uns durch das Tor oder untersuchen wir das Leuchten im Unterholz?",
            "avatar": "/static/avatars/echo.svg",
            "is_nsfw": 0
        }
    ]

    for char in initial:
        cursor.execute("""
            INSERT OR REPLACE INTO characters (id, name, title, tagline, greeting, persona, example_dialogue, avatar, is_nsfw)
            VALUES (:id, :name, :title, :tagline, :greeting, :persona, :example_dialogue, :avatar, :is_nsfw)
        """, char)

# User Authentication CRUD
def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()

def create_user(username: str, password: str, display_name: str = "", avatar: str = "") -> Dict[str, Any]:
    username = username.strip()
    if not username:
        raise ValueError("Benutzername darf nicht leer sein.")
    if len(username) < 3:
        raise ValueError("Benutzername muss mindestens 3 Zeichen lang sein.")
    if len(password) < 4:
        raise ValueError("Passwort muss mindestens 4 Zeichen lang sein.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Der Benutzername '{username}' ist bereits vergeben.")

    user_id = str(uuid.uuid4())
    salt = secrets.token_hex(16)
    pwd_hash = hash_password(password, salt)
    disp_name = display_name.strip() or username
    user_avatar = avatar or "/static/avatars/default.svg"

    cursor.execute("""
        INSERT INTO users (id, username, password_hash, salt, display_name, avatar)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, pwd_hash, salt, disp_name, user_avatar))

    # Initialize default user settings
    defaults = {
        "provider": "ollama",
        "gemini_api_key": "",
        "gemini_model": "gemini-1.5-flash",
        "openai_api_key": "",
        "openai_base_url": "https://api.openai.com/v1",
        "openai_model": "gpt-4o-mini",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.2",
        "user_name": disp_name,
        "user_persona": "Ein neugieriger Besucher auf der Suche nach tiefen Gesprächen und Abenteuern.",
        "nsfw_mode": "false",
        "roleplay_tone": "standard",
        "language": "auto"
    }
    for k, v in defaults.items():
        cursor.execute("INSERT OR REPLACE INTO user_settings (user_id, key, value) VALUES (?, ?, ?)", (user_id, k, v))

    # Safe adoption: if this is the first registered user, associate previous orphan chats & characters
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 1:
        cursor.execute("UPDATE chats SET user_id = ? WHERE user_id IS NULL", (user_id,))
        cursor.execute("UPDATE characters SET user_id = ? WHERE user_id IS NULL", (user_id,))

    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    user = dict(row)
    if hash_password(password, user["salt"]) == user["password_hash"]:
        del user["password_hash"]
        del user["salt"]
        return user
    return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, display_name, avatar, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_sessions (token, user_id)
        VALUES (?, ?)
    """, (token, user_id))
    conn.commit()
    conn.close()
    return token

def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.display_name, u.avatar, u.created_at
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_session(token: str) -> bool:
    if not token:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def update_user_profile(user_id: str, display_name: Optional[str] = None, avatar: Optional[str] = None, new_password: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if display_name:
        cursor.execute("UPDATE users SET display_name = ? WHERE id = ?", (display_name.strip(), user_id))
    if avatar:
        cursor.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar.strip(), user_id))
    if new_password and len(new_password) >= 4:
        salt = secrets.token_hex(16)
        pwd_hash = hash_password(new_password, salt)
        cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (pwd_hash, salt, user_id))
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

# Character CRUD
def get_all_characters(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM characters WHERE user_id = ? OR user_id IS NULL ORDER BY created_at ASC", (user_id,))
    else:
        cursor.execute("SELECT * FROM characters WHERE user_id IS NULL ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_character_by_id(char_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE id = ?", (char_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_character(char_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    char_id = char_data.get("id") or str(uuid.uuid4())[:8]
    is_nsfw = 1 if char_data.get("is_nsfw") in (1, True, "1", "true") else 0

    # Preserve existing user_id if already set
    char_user_id = user_id
    cursor.execute("SELECT user_id FROM characters WHERE id = ?", (char_id,))
    existing = cursor.fetchone()
    if existing and existing["user_id"]:
        char_user_id = existing["user_id"]

    cursor.execute("""
        INSERT OR REPLACE INTO characters (id, name, title, tagline, greeting, persona, example_dialogue, avatar, is_nsfw, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_id,
        char_data["name"],
        char_data.get("title", ""),
        char_data.get("tagline", ""),
        char_data.get("greeting", ""),
        char_data.get("persona", ""),
        char_data.get("example_dialogue", ""),
        char_data.get("avatar", "/static/avatars/default.svg"),
        is_nsfw,
        char_user_id
    ))
    conn.commit()
    conn.close()
    return get_character_by_id(char_id)

def delete_character(char_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id IN (SELECT id FROM chats WHERE character_id = ?)", (char_id,))
    cursor.execute("DELETE FROM chats WHERE character_id = ?", (char_id,))
    cursor.execute("DELETE FROM characters WHERE id = ?", (char_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def delete_all_characters(user_id: Optional[str] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM messages WHERE chat_id IN (SELECT id FROM chats WHERE user_id = ?)", (user_id,))
        cursor.execute("DELETE FROM chats WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM characters WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM chats")
        cursor.execute("DELETE FROM characters")
    count = cursor.rowcount
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('initial_seed_done', 'true')")
    conn.commit()
    conn.close()
    return count

def reset_to_default_characters() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    cursor.execute("DELETE FROM chats")
    cursor.execute("DELETE FROM characters")
    seed_characters(cursor)
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('initial_seed_done', 'true')")
    conn.commit()
    conn.close()

# Chat session CRUD
def get_chat_by_id(chat_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_chats_for_character(character_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM chats WHERE character_id = ? AND user_id = ? ORDER BY updated_at DESC", (character_id, user_id))
    else:
        cursor.execute("SELECT * FROM chats WHERE character_id = ? AND user_id IS NULL ORDER BY updated_at DESC", (character_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_or_create_active_chat(character_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM chats WHERE character_id = ? AND user_id = ? ORDER BY updated_at DESC LIMIT 1", (character_id, user_id))
    else:
        cursor.execute("SELECT * FROM chats WHERE character_id = ? AND user_id IS NULL ORDER BY updated_at DESC LIMIT 1", (character_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return dict(row)
    conn.close()
    return create_new_chat(character_id, include_greeting=True, user_id=user_id)

def create_new_chat(character_id: str, title: Optional[str] = None, include_greeting: bool = True, user_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    char = get_character_by_id(character_id)
    chat_id = str(uuid.uuid4())
    
    chat_count = len(get_chats_for_character(character_id, user_id=user_id)) + 1
    chat_title = title or f"Gespräch {chat_count}"

    cursor.execute("""
        INSERT INTO chats (id, character_id, title, user_id)
        VALUES (?, ?, ?, ?)
    """, (chat_id, character_id, chat_title, user_id))

    if include_greeting and char and char.get("greeting"):
        greeting_id = str(uuid.uuid4())
        alts = json.dumps([char["greeting"]])
        cursor.execute("""
            INSERT INTO messages (id, chat_id, role, content, alternatives, current_index, image_url)
            VALUES (?, ?, 'assistant', ?, ?, 0, '')
        """, (greeting_id, chat_id, char["greeting"], alts))

    conn.commit()
    cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
    created = dict(cursor.fetchone())
    conn.close()
    return created

def delete_chat(chat_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Messages CRUD
def get_messages(chat_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC", (chat_id,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["alternatives"] = json.loads(d["alternatives"])
        except Exception:
            d["alternatives"] = [d["content"]]
        if "image_url" not in d or d["image_url"] is None:
            d["image_url"] = ""
        result.append(d)
    return result

def add_message(chat_id: str, role: str, content: str, alternatives: Optional[List[str]] = None, image_url: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    msg_id = str(uuid.uuid4())
    alts = alternatives if alternatives is not None else [content]
    alts_json = json.dumps(alts)

    cursor.execute("""
        INSERT INTO messages (id, chat_id, role, content, alternatives, current_index, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, chat_id, role, content, alts_json, len(alts) - 1, image_url or ""))

    cursor.execute("UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (chat_id,))
    conn.commit()

    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    created = dict(cursor.fetchone())
    created["alternatives"] = alts
    conn.close()
    return created

def update_message_alternative(msg_id: str, new_content: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Message not found")

    row_dict = dict(row)
    try:
        alts = json.loads(row_dict["alternatives"])
    except Exception:
        alts = [row_dict["content"]]

    alts.append(new_content)
    new_index = len(alts) - 1

    cursor.execute("""
        UPDATE messages
        SET content = ?, alternatives = ?, current_index = ?
        WHERE id = ?
    """, (new_content, json.dumps(alts), new_index, msg_id))

    conn.commit()
    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    res = dict(cursor.fetchone())
    res["alternatives"] = alts
    conn.close()
    return res

def set_message_swipe_index(msg_id: str, new_index: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Message not found")

    row_dict = dict(row)
    try:
        alts = json.loads(row_dict["alternatives"])
    except Exception:
        alts = [row_dict["content"]]

    if 0 <= new_index < len(alts):
        new_content = alts[new_index]
        cursor.execute("""
            UPDATE messages
            SET content = ?, current_index = ?
            WHERE id = ?
        """, (new_content, new_index, msg_id))
        conn.commit()

    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    res = dict(cursor.fetchone())
    res["alternatives"] = alts
    conn.close()
    return res

def edit_message(msg_id: str, content: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Message not found")

    row_dict = dict(row)
    try:
        alts = json.loads(row_dict["alternatives"])
    except Exception:
        alts = [row_dict["content"]]

    idx = row_dict["current_index"]
    if 0 <= idx < len(alts):
        alts[idx] = content
    else:
        alts = [content]
        idx = 0

    cursor.execute("""
        UPDATE messages
        SET content = ?, alternatives = ?, current_index = ?
        WHERE id = ?
    """, (content, json.dumps(alts), idx, msg_id))
    conn.commit()

    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    res = dict(cursor.fetchone())
    res["alternatives"] = alts
    conn.close()
    return res

def delete_message(msg_id: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting message {msg_id}: {e}")
        return False

def sync_messages(chat_id: str, messages_list: List[Dict[str, Any]]) -> int:
    """Synchronize or restore messages from client-side backup into the chat."""
    if not messages_list:
        return 0
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM messages WHERE chat_id = ?", (chat_id,))
    existing_ids = {row["id"] for row in cursor.fetchall()}
    
    inserted = 0
    for m in messages_list:
        m_id = str(m.get("id") or "")
        if not m_id or m_id.startswith("temp-"):
            m_id = str(uuid.uuid4())
        
        if m_id not in existing_ids:
            role = m.get("role", "user")
            content = m.get("content", "")
            alts = m.get("alternatives") or [content]
            if isinstance(alts, list):
                alts_json = json.dumps(alts)
                cur_idx = m.get("current_index", len(alts) - 1)
            else:
                alts_json = json.dumps([content])
                cur_idx = 0
            img_url = m.get("image_url", "")
            created_at = m.get("created_at")
            if created_at:
                cursor.execute("""
                    INSERT INTO messages (id, chat_id, role, content, alternatives, current_index, image_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (m_id, chat_id, role, content, alts_json, cur_idx, img_url, created_at))
            else:
                cursor.execute("""
                    INSERT INTO messages (id, chat_id, role, content, alternatives, current_index, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (m_id, chat_id, role, content, alts_json, cur_idx, img_url))
            existing_ids.add(m_id)
            inserted += 1

    if inserted > 0:
        cursor.execute("UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (chat_id,))
        conn.commit()
    conn.close()
    return inserted

# Settings CRUD
def get_all_settings(user_id: Optional[str] = None) -> Dict[str, str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings_dict = {r["key"]: r["value"] for r in cursor.fetchall()}
    if user_id:
        cursor.execute("SELECT key, value FROM user_settings WHERE user_id = ?", (user_id,))
        user_rows = cursor.fetchall()
        for r in user_rows:
            settings_dict[r["key"]] = r["value"]
    conn.close()

    # Enforce Gemini as primary engine
    current_prov = (settings_dict.get("provider") or "").lower()
    if not current_prov or current_prov in ("openai", "simulator"):
        settings_dict["provider"] = "gemini"
    
    gemini_key = (settings_dict.get("gemini_api_key", "") or "").strip()
    if not gemini_key or len(gemini_key) < 20:
        settings_dict["gemini_api_key"] = DEFAULT_GEMINI_KEY

    gemini_model = (settings_dict.get("gemini_model", "") or "").strip()
    if not gemini_model or gemini_model == "gemini-1.5-flash":
        settings_dict["gemini_model"] = "gemini-2.5-flash"

    # Also keep Groq ready as robust fallback
    settings_dict["openai_base_url"] = "https://api.groq.com/openai/v1"
    current_model = (settings_dict.get("openai_model", "") or "").strip()
    if not current_model or current_model in ("gpt-4o-mini", "llama3.2"):
        settings_dict["openai_model"] = "qwen/qwen3.8-27b"

    current_key = (settings_dict.get("openai_api_key", "") or "").strip()
    if not current_key or current_key.startswith("gsk_Pr6N") or current_key.startswith("gsk_1twr") or current_key.startswith("gsk_GKPH") or len(current_key) < 20:
        settings_dict["openai_api_key"] = DEFAULT_GROQ_KEY

    return settings_dict

def update_settings(updates: Dict[str, str], user_id: Optional[str] = None):
    sanitized = dict(updates)
    if not sanitized.get("provider"):
        sanitized["provider"] = "gemini"
    gem_key = (sanitized.get("gemini_api_key") or "").strip()
    if not gem_key or len(gem_key) < 20:
        sanitized["gemini_api_key"] = DEFAULT_GEMINI_KEY
    if not sanitized.get("gemini_model") or sanitized.get("gemini_model") == "gemini-1.5-flash":
        sanitized["gemini_model"] = "gemini-2.5-flash"

    sanitized["openai_base_url"] = "https://api.groq.com/openai/v1"
    if not sanitized.get("openai_model") or sanitized.get("openai_model") in ("gpt-4o-mini", "llama3.2"):
        sanitized["openai_model"] = "qwen/qwen3.8-27b"
    key = (sanitized.get("openai_api_key") or "").strip()
    if not key or key.startswith("gsk_Pr6N") or key.startswith("gsk_1twr") or key.startswith("gsk_GKPH") or len(key) < 20:
        sanitized["openai_api_key"] = DEFAULT_GROQ_KEY

    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        for k, v in sanitized.items():
            cursor.execute("INSERT OR REPLACE INTO user_settings (user_id, key, value) VALUES (?, ?, ?)", (user_id, k, str(v)))
    else:
        for k, v in sanitized.items():
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()
