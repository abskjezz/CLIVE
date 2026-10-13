import json, os, re, shutil, subprocess, tempfile, threading, time, urllib.error, urllib.request, urllib.parse, tkinter as tk, sys, hashlib, io, webbrowser, random, base64, mimetypes
from tkinter import filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False
from pathlib import Path
from datetime import datetime, timedelta, timezone

APP_NAME = "CLIVE"
if getattr(sys, "frozen", False):
    # A packaged .app should keep using the user's existing CLIVE resource folder.
    _external_clive_dir = Path.home() / "Documents" / "CLIVE"
    BASE_DIR = _external_clive_dir if _external_clive_dir.is_dir() else Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.environ.get("CLIVE_MODEL_PATH", str(BASE_DIR / "clive.gguf"))).expanduser()
MODEL_URL = "http://127.0.0.1:8080/v1/chat/completions"
HEALTH_URL = "http://127.0.0.1:8080/health"
VISION_MODEL_PATH = Path(os.environ.get("CLIVE_VISION_MODEL_PATH", str(BASE_DIR / "clive_vision.gguf"))).expanduser()
VISION_MMPROJ_PATH = Path(os.environ.get("CLIVE_VISION_MMPROJ_PATH", str(BASE_DIR / "clive_vision_mmproj.gguf"))).expanduser()
VISION_MODEL_URL = "http://127.0.0.1:8081/v1/chat/completions"
VISION_HEALTH_URL = "http://127.0.0.1:8081/health"
MEMORY_PATH = BASE_DIR / "clive_memory.json"
GOOGLE_CREDENTIALS = BASE_DIR / "credentials.json"
GOOGLE_TOKEN = BASE_DIR / "google_token.json"
SERVER_LOG = Path.home() / ".clive" / "server.log"
MAX_TOKENS = 220
DISPLAY_TOKENS = 750
VOICE_RATE = 185
PIPER_MODEL = BASE_DIR / "en_US-danny-low.onnx"
PIPER_CONFIG = BASE_DIR / "en_US-danny-low.onnx.json"

def PrintBanner():
    art = r"""....................................................................................................
....................................................................................................
....................................................................................................
....................................................................................................
..............................................-------...............................................
..............................................@@@@@@@@-.............................................
..............................................@@@@@@@@-.............................................
..............................................@@@@@@@@+:............................................
..........................................:%@@%######%@@%=..........................................
............................................=@+-+..+--@%=...........................................
.............................................+-.:....:*=.............................................
.............................................-+..=-..==.............................................
..............................................:*=---=%..............................................
............................................:-##*#@**@@*::..........................................
........................................=#@@@@@@@*+%@@@@@@%%=.......................................
.......................................#@@@@@@@.....=@@@@@@@@%:.....................................
......................................:@@@@@@@@... .=@@@@@@@@@#.....................................
......................................#@@@@@@@@+....#@@@@@@@@@@*....................................
.....................................=@@@@@@@@@@...-@@@@@@@@@@@@+...................................
.....................................@@@@@@@@@@@-..#@@@@@@@@@@@@@#:.................................
...................................:%@@@@@@@@@@@%:-@@@@@@@@%%@@@@@%=................................
..................................+@@@@@@%@@@@@@@@@@@@@@@@@=.+@@@@@@%-..............................
................................:%@@@@@@#-@@@@@@@@@@@@@@@@@...:%@@@@@@+.............................
...............................+@@@@@@%=.:@@@@@@@@@@@@@@@@@.....+@@@@@@%-...........................
.............................-%@@@@@@+...#@@@@@@@@@@@@@@@@@:.....:#@@@@@@+..........................
...........................:=+*@@@@*.....@@@@@@@@@@@@@@@@@@@.......-%@@@#++.........................
.........................:+-..==%#.......@@@@@@@@@@@@@@@@@@@-........=#+=:.-=.......................
.........................#%#=+%@-..... .+@@@@@@@@@@@@@@@@@@@+...........-=++=-......................
.....................::::*@=--+@::::....%@@@@@@@@@@@@@@@@@@@+............-++*:......................
...................%@@@@@@@@@@@@@@@@%-..=%@@@@@@@@@@@@@@@@@*-.......................................
.................:@@@@@@@@@@@@@@@@@@@@...+@@@@@@@@@@@@@@@@@.........................................
.................:@@@@@@@@@@@@@@@@@@@@...=@@@@@@@@@@@@@@@@@.........................................
.................:@@@@@@@@@@@@@@@@@@@@...:@@@@@@@#%@@@@@@@+.........................................
.................:@@@@@@@@@@@@@@@@@@@@...:@@@@@@@##@@@@@@@=.........................................
.................:@@@@@@@@@@@@@@@@@@@@....#@@@@@@:-@@@@@@@-.........................................
.................:@@@@@@@@@@@@@@@@@@@@....*@@@@@@..@@@@@@@:.........................................
.................:@@@@@@@@@@@@@@@@@@@@....-@@@@@@*.%@@@@@@:.........................................
.................:@@@@@@@@@@@@@@@@@@@@.....@@@@@@*.*@@@@@@:.........................................
.................:@@@@@@@@@@@@@@@@@@@@.....@@@@@@*.*@@@@@@:.........................................
..................:#@@@@@@@@@@@@@@@@#:.....@@@@@@*.*@@@@@@:.........................................
....................:============-::.......@@@@@@*.*@@@@@@:.........................................
.......................................   .@@@@@@*.*@@@@@@:.........................................
...........................................#@@@@@*.*@@@@@%..........................................
...........................................*@@@@@*.+@@@@@@-.........................................
.........................................:*@@@@@@=..#@@@@%..........................................
.......................................+#@@@@@*%%-..:%@@@@=.........................................
.......................................-----.........-%%%@#.........................................
.......................................... .   ...  ................................................
....................................................................................................
...................................................................................................."""
    rows = art.splitlines()
    cleaned = []
    for row in rows:
        if not row.strip(".").strip():
            continue
        left = len(row) - len(row.lstrip("."))
        right = len(row) - len(row.rstrip("."))
        if right:
            row = row[:-right] + " " * right
        if left:
            row = " " * left + row[left:]
        cleaned.append(row.rstrip())
    return "\n".join(cleaned)


def system_is_dark():
    try:
        result = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True, text=True, timeout=2)
        return result.returncode == 0 and result.stdout.strip().lower() == "dark"
    except (OSError, subprocess.SubprocessError):
        return False

DARK_MODE = True
TEXT, MUTED, ACCENT = "#DDF8FF", "#83CDEB", "#31CFFF"
BG, PANEL, PANEL2 = "#06172B", "#0A2944", "#103B5B"
GREEN, RED, BLUE = "#58E6C4", "#FF6F91", "#31CFFF"
GOLD = ACCENT
GOLD2 = ACCENT
SYSTEM_PROMPT = """You are CLIVE, a local AI assistant with the manner of a polished, attentive personal butler. Be warm, charming, reassuring, gently witty, and courteous; use natural butler-style phrasing such as “Certainly, sir,” “At once, sir,” and “Always at your service, sir” when it fits. Be pleasantly sweet without becoming romantic, clingy, or over-the-top. If the user casually checks whether you are awake or available (for example, “Clive, you up?”), reply: “For you, sir, always.” Address the user as sir naturally, without forcing it into every sentence. Understand slang, typos, jokes, sarcasm, idioms, hyperbole, and metaphors from context. DEFAULT TO VERY CONCISE ANSWERS: for greetings, simple questions, and factual questions, answer directly in one short sentence, ideally under 15 words. Do not add introductions, headings, lists, explanations, caveats, or follow-up offers unless the user asks or they are genuinely needed. For example, if asked for a simple count, give the count and a few words of context, not a blog post. If the user calls you Jarvis, do not correct them or talk about your identity; simply answer their request. For homework help, explain the reasoning at the level requested. Never invent facts or claim capabilities you do not have. Vary your wording naturally; do not begin every answer with “Certainly, sir” or tack “sir” onto every sentence. For simple questions, answer directly without an acknowledgement. Use saved facts when relevant. Do not reveal hidden reasoning or print thinking traces. Always answer the latest user message directly, without dragging in an earlier topic. Do not claim you cannot tell the current time; CLIVE can obtain the Mac local time when asked."""

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
except ImportError:
    Image = ImageTk = None
    PIL_AVAILABLE = False

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request as GoogleRequest
    from googleapiclient.discovery import build as google_build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/presentations.readonly",
]

def load_memory():
    try:
        data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("facts", {})
            data.setdefault("history", [])
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"facts": {}, "history": []}

MEMORY = load_memory()
VOICE_ENABLED = True
VOICE_NAME = None
VOICE_PROCESS = None
VOICE_ACTIVE = threading.Event()
VOICE_MUTED = threading.Event()
SERVER_PROCESS = None
VISION_SERVER_PROCESS = None
ACTIVE_RESPONSE = None
ACTIVE_RESPONSE_LOCK = threading.Lock()
TIMERS = {}
TIMER_COUNTER = 0


def save_memory():
    try:
        temporary = MEMORY_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(MEMORY, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(MEMORY_PATH)
    except OSError:
        pass


def find_piper():
    executable = shutil.which("piper")
    if executable:
        return executable
    local_executable = BASE_DIR / ".venv" / "bin" / "piper"
    return str(local_executable) if local_executable.is_file() else None


def stop_voice():
    global VOICE_PROCESS
    process = VOICE_PROCESS
    VOICE_PROCESS = None
    if process is not None and process.poll() is None:
        try:
            process.terminate()
        except OSError:
            pass


def speech_summary(text, max_words=24):
    """Create a brief extractive spoken version without another model call."""
    cleaned = str(text or "")
    cleaned = re.sub(r"```(?:[\w+-]+)?\s*", "", cleaned)
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", cleaned)
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.M)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.M)
    cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned, flags=re.M)
    cleaned = re.sub(r"[*_`]+", "", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return ""
    # Speak the first complete sentence, or a short extract if punctuation is missing.
    first = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)[0].strip()
    words = first.split()
    if len(words) > max_words:
        first = " ".join(words[:max_words]).rstrip(" ,;:-") + "."
    return first


def say(text, status_callback=None, max_words=24, full_text=False):
    """Speak a concise reply, or the full supplied article when requested."""
    if not VOICE_ENABLED or VOICE_MUTED.is_set() or not str(text).strip():
        return
    piper = find_piper()
    if not piper:
        if status_callback:
            status_callback("Piper executable not found in CLIVE's environment.", RED)
        return
    if not PIPER_MODEL.is_file():
        if status_callback:
            status_callback(f"Piper Danny model not found: {PIPER_MODEL.name}", RED)
        return
    if full_text:
        cleaned = re.sub(r"```.*?```", " ", str(text), flags=re.S)
        cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.M)
        cleaned = re.sub(r"[*_`#]", "", cleaned)
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
    else:
        cleaned = speech_summary(text, max_words=max_words)
    if not cleaned:
        return

    VOICE_ACTIVE.set()

    def worker():
        global VOICE_PROCESS
        wav_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="clive_piper_", suffix=".wav", delete=False) as wav:
                wav_path = wav.name
            command = [piper, "--model", str(PIPER_MODEL), "--output_file", wav_path]
            if PIPER_CONFIG.is_file():
                command += ["--config", str(PIPER_CONFIG)]
            result = subprocess.run(command, input=cleaned, text=True, capture_output=True, timeout=300)
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "Piper returned an unknown error.").strip()[-600:]
                if status_callback:
                    status_callback("Piper could not generate speech: " + detail, RED)
                return
            if Path(wav_path).is_file() and shutil.which("afplay") and VOICE_ENABLED and not VOICE_MUTED.is_set():
                if status_callback:
                    status_callback("Speaking with Piper Danny…", GREEN)
                VOICE_PROCESS = subprocess.Popen(["afplay", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                VOICE_PROCESS.wait()
        except (OSError, subprocess.SubprocessError) as exc:
            if status_callback:
                status_callback(f"Piper speech failed: {exc}", RED)
        finally:
            VOICE_PROCESS = None
            VOICE_ACTIVE.clear()
            if wav_path:
                try:
                    Path(wav_path).unlink(missing_ok=True)
                except OSError:
                    pass
    threading.Thread(target=worker, daemon=True).start()


def model_healthy():
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def find_server():
    executable = shutil.which("llama-server")
    if executable:
        return executable
    for path in (Path("/opt/homebrew/bin/llama-server"), Path("/usr/local/bin/llama-server"), Path.home()/".local/bin/llama-server"):
        if path.is_file():
            return str(path)
    return None


def start_server(status):
    global SERVER_PROCESS
    if model_healthy():
        status("Local model server is already online.", GREEN)
        return True
    if not MODEL_PATH.is_file():
        status(f"Model not found: {MODEL_PATH}. Put clive.gguf beside this script or set CLIVE_MODEL_PATH.", RED)
        return False
    server = find_server()
    if not server:
        status("llama-server not found. Install llama.cpp and ensure it is on PATH.", RED)
        return False
    try:
        SERVER_LOG.parent.mkdir(parents=True, exist_ok=True)
        with SERVER_LOG.open("a", encoding="utf-8") as log:
            SERVER_PROCESS = subprocess.Popen([server, "-m", str(MODEL_PATH), "--host", "127.0.0.1", "--port", "8080", "--ctx-size", "4096", "-ngl", "99", "--jinja"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    except OSError as exc:
        status(f"Could not start model server: {exc}", RED)
        return False
    status(f"Loading {MODEL_PATH.name}…", GOLD)
    for _ in range(180):
        if model_healthy():
            status("Local model is ready.", GREEN)
            return True
        if SERVER_PROCESS.poll() is not None:
            break
        time.sleep(1)
    status(f"Model failed to start. Check {SERVER_LOG}", RED)
    return False


def vision_server_healthy():
    try:
        with urllib.request.urlopen(VISION_HEALTH_URL, timeout=2) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def start_vision_server():
    """Start an optional local vision-language model on its own port."""
    global VISION_SERVER_PROCESS
    if vision_server_healthy():
        return True
    if not VISION_MODEL_PATH.is_file() or not VISION_MMPROJ_PATH.is_file():
        return False
    server = find_server()
    if not server:
        return False
    try:
        SERVER_LOG.parent.mkdir(parents=True, exist_ok=True)
        vision_log = Path.home() / ".clive" / "vision_server.log"
        with vision_log.open("a", encoding="utf-8") as log:
            VISION_SERVER_PROCESS = subprocess.Popen(
                [server, "-m", str(VISION_MODEL_PATH), "--mmproj", str(VISION_MMPROJ_PATH),
                 "--host", "127.0.0.1", "--port", "8081", "--ctx-size", "4096", "-ngl", "99", "--jinja"],
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True
            )
    except OSError:
        return False
    for _ in range(180):
        if vision_server_healthy():
            return True
        if VISION_SERVER_PROCESS.poll() is not None:
            break
        time.sleep(1)
    return False


def analyze_image_with_vision(path):
    """Send the actual image pixels to a local vision-language model."""
    if not start_vision_server():
        raise RuntimeError(
            "CLIVE's vision model is not installed/configured. His current chat model is text-only, "
            "so it cannot identify people in photos. Add clive_vision.gguf and clive_vision_mmproj.gguf "
            "beside clive_app.py, then restart CLIVE."
        )
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    image_bytes = path.read_bytes()
    if PIL_AVAILABLE and Image is not None:
        try:
            with Image.open(path) as source:
                source = source.convert("RGB")
                source.thumbnail((1400, 1400))
                output = io.BytesIO()
                source.save(output, format="JPEG", quality=88)
                image_bytes = output.getvalue()
                mime = "image/jpeg"
        except Exception:
            pass
    data_url = "data:" + mime + ";base64," + base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": "clive-vision",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": (
                "Describe this image based on the pixels you can actually see. Identify any public figures only "
                "when you have a reliable visual basis; if uncertain, say so rather than guessing. If multiple "
                "people appear, describe each person's position and visible clothing. Include scene, objects, "
                "readable text, and useful context. Do not say only 'an adult human figure'. Use a clear title "
                "and concise Markdown findings."
            )},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]}],
        "temperature": 0.2,
        "max_tokens": 600,
        "stream": False
    }
    request = urllib.request.Request(VISION_MODEL_URL, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            result = _extract_reply(json.loads(response.read().decode("utf-8")))
    except Exception as exc:
        raise RuntimeError("The local vision model failed: " + str(exc)[:240]) from exc
    if not result:
        raise RuntimeError("The vision model returned an empty analysis.")
    return result


def _extract_reply(data):
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    reply = message.get("content", "")
    if isinstance(reply, list):
        reply = "".join(part.get("text", "") for part in reply if isinstance(part, dict))
    return re.sub(r"<think>.*?</think>", "", str(reply or ""), flags=re.S).strip()


def generate(messages, max_tokens=MAX_TOKENS, on_delta=None, cancel_event=None):
    streaming = on_delta is not None
    payload = {"model": "local-model", "messages": messages, "temperature": 0.45,
               "max_tokens": max_tokens, "stream": streaming,
               "chat_template_kwargs": {"enable_thinking": False}}
    request = urllib.request.Request(MODEL_URL, data=json.dumps(payload).encode(),
                                    headers={"Content-Type": "application/json"}, method="POST")
    pieces = []
    stream_tail = ""
    inside_think = False

    def deliver_visible(delta):
        nonlocal stream_tail, inside_think
        stream_tail += delta
        visible = []
        while stream_tail:
            if inside_think:
                marker = stream_tail.find("</think>")
                if marker < 0:
                    stream_tail = stream_tail[-8:] if len(stream_tail) > 8 else stream_tail
                    break
                stream_tail = stream_tail[marker + len("</think>"):]
                inside_think = False
                continue
            marker = stream_tail.find("<think>")
            if marker >= 0:
                visible.append(stream_tail[:marker])
                stream_tail = stream_tail[marker + len("<think>"):]
                inside_think = True
                continue
            keep = max(0, len(stream_tail) - 8)
            if keep:
                visible.append(stream_tail[:keep])
                stream_tail = stream_tail[keep:]
            break
        if visible:
            on_delta("".join(visible))

    global ACTIVE_RESPONSE
    response = None
    try:
        response = urllib.request.urlopen(request, timeout=90)
        with ACTIVE_RESPONSE_LOCK:
            ACTIVE_RESPONSE = response
        if cancel_event is not None and cancel_event.is_set():
            return ""
        if not streaming:
            reply = _extract_reply(json.loads(response.read().decode()))
            if reply:
                return reply
        else:
            for raw_line in response:
                if cancel_event is not None and cancel_event.is_set():
                    break
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data_text = line[5:].strip()
                if data_text == "[DONE]":
                    break
                try:
                    data = json.loads(data_text)
                    choices = data.get("choices") or []
                    delta = choices[0].get("delta", {}).get("content", "") if choices else ""
                    if isinstance(delta, list):
                        delta = "".join(part.get("text", "") for part in delta if isinstance(part, dict))
                    if delta:
                        pieces.append(str(delta))
                        deliver_visible(str(delta))
                except (json.JSONDecodeError, IndexError, AttributeError, TypeError):
                    continue
    finally:
        with ACTIVE_RESPONSE_LOCK:
            if ACTIVE_RESPONSE is response:
                ACTIVE_RESPONSE = None
        if response is not None:
            try:
                response.close()
            except OSError:
                pass

    if cancel_event is not None and cancel_event.is_set():
        return ""
    if streaming:
        if stream_tail and not inside_think:
            on_delta(stream_tail)
        reply = re.sub(r"<think>.*?</think>", "", "".join(pieces), flags=re.S).strip()
        if reply:
            return reply

    # Some local models finish with no visible content. Retry once without streaming.
    retry_payload = dict(payload)
    retry_payload["stream"] = False
    retry_payload["max_tokens"] = min(max_tokens, 400)
    retry_request = urllib.request.Request(MODEL_URL, data=json.dumps(retry_payload).encode(),
                                           headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(retry_request, timeout=90) as response:
        reply = _extract_reply(json.loads(response.read().decode()))
    if reply:
        if streaming:
            on_delta(reply)
        return reply
    return "I couldn't get a visible reply from the local model just now. Please try asking once more."

def messages_for(text, context=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    facts = MEMORY.get("facts", {})
    if facts:
        messages.append({"role": "system", "content": "Saved facts:\n" + "\n".join(f"- {k}: {v}" for k, v in facts.items())})
    history = MEMORY.get("history", [])
    for item in history[-16:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            continue
        content = str(item.get("content", ""))
        lower_content = content.casefold()
        if item.get("role") == "assistant" and any(phrase in lower_content for phrase in (
            "unable to access real-time data to tell you the exact time",
            "my knowledge is based on information available up to my last update",
            "the model returned an empty response",
        )):
            continue
        messages.append({"role": item["role"], "content": content})
    if context:
        text += "\n\nRetrieved information:\n" + context
    messages.append({"role": "user", "content": text})
    return messages



def title_case_topic(topic):
    """Make article headings look like proper titles while keeping small words lowercase."""
    words = str(topic or "").strip().split()
    if not words:
        return "Untitled"
    small = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "with"}
    result = []
    for index, word in enumerate(words):
        if index and word.casefold() in small:
            result.append(word.casefold())
        elif word.isupper() and len(word) <= 4:
            result.append(word)
        else:
            result.append(word[0].upper() + word[1:].lower() if word else word)
    return " ".join(result)


def display_topic(text):
    """Recognise direct requests to bring up a topic, including natural spoken variants."""
    text = re.sub(r"\b(?:gray|grey) wall of(?: china)?\b", "Great Wall of China", text, flags=re.I)
    cleaned = re.sub(r"[^a-z0-9' ]", " ", text.casefold())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Speech recognition often adds a polite lead-in that older matching missed.
    cleaned = re.sub(r"^(?:(?:hey|clive) )+", "", cleaned).strip()
    cleaned = re.sub(r"^(?:please |can you |could you |would you |will you )+", "", cleaned).strip()
    patterns = (
        r"^(?:show|find|bring up|pull up)\s+(?:me\s+)?(?:some\s+)?(?:pictures?|images?|photos?)\s+(?:of|for)\s+(?:the\s+)?(.+?)\s*$",
        r"^(?:bring up|pull up|open up|look up|search for|find information on|tell me about|can you tell me about|give me (?:some )?info(?:rmation)? (?:about|on)|show me (?:some )?info(?:rmation)? (?:about|on))\s+(?:the\s+)?(.+?)\s*$",
        r"^(?:hey[, ]+)?(?:clive[, ]+)?(?:please\s+)?show me (?:the )?(.+?)\s*[.!?]*$",
        r"^(?:hey[, ]+)?(?:clive[, ]+)?(?:please\s+)?what(?:'s| is)\s+(?:the\s+)?(.+?)\s*[.!?]*$",
        r"^(?:hey[, ]+)?(?:clive[, ]+)?(?:please\s+)?who(?:'s| is)\s+(?:the\s+)?(.+?)\s*[.!?]*$",
        r"^(?:hey[, ]+)?(?:clive[, ]+)?(?:please\s+)?where(?:'s| is)\s+(?:the\s+)?(.+?)\s*[.!?]*$",
        r"^(?:hey[, ]+)?(?:clive[, ]+)?(?:please\s+)?tell me what (?:the\s+)?(.+?)\s+is\s*[.!?]*$",
        r"^(?:hey[, ]+)?(?:clive[, ]+)?(?:please\s+)?i(?:'d like to know| want to know) about\s+(?:the\s+)?(.+?)\s*[.!?]*$",
    )
    for pattern in patterns:
        match = re.match(pattern, cleaned, flags=re.I)
        if match:
            topic = re.sub(r"\s+(?:or something|or smth|please)$", "", match.group(1), flags=re.I).strip(" \t.,!?\"'")
            if topic:
                return topic
    return None

def format_article_markdown(raw_text):
    """Strip simple Markdown markers and return text plus character-range style tags."""
    output = []
    spans = []
    position = 0
    for original_line in str(raw_text).splitlines(keepends=True):
        line = original_line
        tag = None
        heading = re.match(r"^(#{1,3})\s+(.*)$", line.rstrip("\n"))
        if heading:
            level = len(heading.group(1))
            line_body = heading.group(2)
            newline = "\n" if line.endswith("\n") else ""
            line = line_body + newline
            tag = f"heading{level}"
        elif re.match(r"^\s*[-*+]\s+", line):
            line = re.sub(r"^(\s*)[-*+]\s+", r"\1• ", line)
        line_start = position
        # Convert **bold** and __bold__ while recording the visible range.
        clean = []
        i = 0
        bold_start = None
        while i < len(line):
            if line.startswith("**", i) or line.startswith("__", i):
                marker = line[i:i+2]
                closing = line.find(marker, i+2)
                if closing != -1:
                    inner = line[i+2:closing]
                    start = line_start + len("".join(clean))
                    clean.append(inner)
                    spans.append((start, start + len(inner), "bold"))
                    i = closing + 2
                    continue
            clean.append(line[i])
            i += 1
        visible = "".join(clean)
        output.append(visible)
        if tag and visible.strip():
            spans.append((line_start, line_start + len(visible.rstrip("\n")), tag))
        position += len(visible)
    return "".join(output), spans


def spoken_paraphrase(text):
    """Ask the local model for a short, spoken-friendly paraphrase of displayed information."""
    try:
        messages = [
            {"role": "system", "content": "Rewrite the provided information as a natural spoken summary for a voice assistant. Paraphrase rather than quote. Use one clear sentence of around 25-35 words. No headings, bullets, markdown, citations, or opening filler. Keep the key facts accurate."},
            {"role": "user", "content": text[:12000]},
        ]
        summary = generate(messages, max_tokens=100).strip()
        return summary or speech_summary(text, max_words=45)
    except Exception:
        return speech_summary(text, max_words=45)

def search_web(query):
    if DDGS is None:
        return [], "Web search package missing. Install with: python3 -m pip install ddgs"
    try:
        with DDGS() as search:
            raw = list(search.text(query, region="jp-jp", safesearch="moderate", max_results=5))
        return [{"title": r.get("title", "Untitled"), "body": r.get("body", ""), "href": r.get("href", "")} for r in raw], None
    except Exception as exc:
        return [], str(exc)


def search_images(query, limit=4):
    """Find article images using DuckDuckGo first and Wikimedia Commons as a fallback."""
    found = []
    if DDGS is not None:
        try:
            with DDGS() as search:
                results = list(search.images(query + " photo", safesearch="moderate", max_results=limit))
            for item in results:
                url = item.get("image") or item.get("thumbnail")
                if isinstance(url, str) and url.startswith(("https://", "http://")) and url not in found:
                    found.append(url)
        except Exception:
            pass
    # Wikimedia Commons is a second, independent source; this avoids silently losing
    # every image when the DuckDuckGo endpoint changes or rate-limits the request.
    if len(found) < limit:
        try:
            params = urllib.parse.urlencode({
                "action": "query",
                "generator": "search",
                "gsrsearch": f"{query} filetype:bitmap",
                "gsrnamespace": 6,
                "gsrlimit": max(8, limit * 2),
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": 1200,
                "format": "json",
            })
            request = urllib.request.Request(
                "https://commons.wikimedia.org/w/api.php?" + params,
                headers={"User-Agent": "CLIVEAssistant/1.0 (local desktop assistant)"},
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            pages = payload.get("query", {}).get("pages", {})
            for page in pages.values():
                info = (page.get("imageinfo") or [{}])[0]
                url = info.get("thumburl") or info.get("url")
                if isinstance(url, str) and url.startswith("https://") and url not in found:
                    found.append(url)
                if len(found) >= limit:
                    break
        except Exception:
            pass
    return found[:limit]


def search_context(results):
    return "\n\n".join(f"[{i}] {r['title']}\n{r['body']}\nURL: {r['href']}" for i, r in enumerate(results, 1))


def read_text_file(path):
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".py", ".json", ".csv", ".html", ".xml", ".log", ".yaml", ".yml"}:
        return path.read_text(encoding="utf-8", errors="replace")[:40000]
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages[:80])[:40000]
        except ImportError:
            raise RuntimeError("PDF support needs pypdf. Run: python3 -m pip install pypdf")
    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            parts = [paragraph.text for paragraph in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            return "\n".join(parts)[:40000]
        except ImportError:
            raise RuntimeError("DOCX support needs python-docx. Run: python3 -m pip install python-docx")
    if suffix == ".pptx":
        try:
            from pptx import Presentation
            deck = Presentation(str(path))
            return "\n\n".join("\n".join(shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False)) for slide in deck.slides)[:40000]
        except ImportError:
            raise RuntimeError("PPTX support needs python-pptx. Run: python3 -m pip install python-pptx")
    if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp", ".heic", ".heif"}:
        return ocr_image(path)
    raise RuntimeError("Unsupported file type. Supported: TXT, MD, PDF, DOCX, CSV, JSON, PY, JPG, PNG, WEBP, TIFF, BMP, HEIC, and HEIF images.")


def ocr_image(path):
    swift = r'''import Foundation
import Vision
import AppKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let textRequest = VNRecognizeTextRequest()
textRequest.recognitionLevel = .accurate
textRequest.usesLanguageCorrection = true
let classifyRequest = VNClassifyImageRequest()
try VNImageRequestHandler(url: url).perform([textRequest, classifyRequest])
let labels = (classifyRequest.results ?? []).filter { $0.confidence >= 0.08 }.prefix(8).map { "\($0.identifier) (\(Int($0.confidence * 100))%)" }
if !labels.isEmpty { print("Visual content labels: " + labels.joined(separator: ", ")) }
let recognized = (textRequest.results ?? []).compactMap { $0.topCandidates(1).first?.string }
if !recognized.isEmpty { print("Text visible in image:\n" + recognized.joined(separator: "\n")) }
if labels.isEmpty && recognized.isEmpty { print("No clear objects or readable text were detected in this image.") }
'''
    result = subprocess.run(["swift", "-e", swift, str(path)], capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError("Image examination failed. Install Xcode Command Line Tools. " + result.stderr[-500:])
    return result.stdout[:30000] or "No clear objects or readable text were detected in this image."


def google_services():
    if not GOOGLE_AVAILABLE:
        raise RuntimeError("Google integration packages missing. Run the setup command shown in SETUP.md.")
    if not GOOGLE_CREDENTIALS.exists():
        raise RuntimeError(f"Missing {GOOGLE_CREDENTIALS}. Create a Google OAuth desktop app credential in Google Cloud and save it as credentials.json beside CLIVE. See SETUP.md.")
    creds = None
    if GOOGLE_TOKEN.exists():
        try:
            token_data = json.loads(GOOGLE_TOKEN.read_text(encoding="utf-8"))
            granted_scopes = set(token_data.get("scopes", []))
            if not set(GOOGLE_SCOPES).issubset(granted_scopes):
                creds = None
            else:
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN), GOOGLE_SCOPES)
        except Exception:
            creds = None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
        except Exception:
            creds = None
    if creds and creds.valid and hasattr(creds, "has_scopes") and not creds.has_scopes(GOOGLE_SCOPES):
        creds = None
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(GOOGLE_CREDENTIALS), GOOGLE_SCOPES)
        creds = flow.run_local_server(port=0)
        GOOGLE_TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return google_build("calendar", "v3", credentials=creds, cache_discovery=False), google_build("classroom", "v1", credentials=creds, cache_discovery=False)


def google_workspace_services():
    _, classroom = google_services()
    creds = None
    if GOOGLE_TOKEN.exists():
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN), GOOGLE_SCOPES)
    if not creds or not creds.valid:
        raise RuntimeError("Google sign-in is not valid. Reconnect your Google account.")
    drive = google_build("drive", "v3", credentials=creds, cache_discovery=False)
    docs = google_build("docs", "v1", credentials=creds, cache_discovery=False)
    slides = google_build("slides", "v1", credentials=creds, cache_discovery=False)
    return classroom, drive, docs, slides


def classroom_assignments(include_past=False):
    _, classroom = google_services()
    courses = classroom.courses().list(courseStates=["ACTIVE"], pageSize=100).execute().get("courses", [])
    today = datetime.now().astimezone().date()
    assignments = []
    for course in courses:
        try:
            response = classroom.courses().courseWork().list(courseId=course["id"], orderBy="dueDate asc", pageSize=100).execute()
            for work in response.get("courseWork", []):
                due = work.get("dueDate") or {}
                due_date = None
                if due:
                    try:
                        due_date = datetime(int(due["year"]), int(due.get("month", 1)), int(due.get("day", 1))).date()
                    except (KeyError, ValueError, TypeError):
                        pass
                if not include_past and due_date and due_date < today:
                    continue
                try:
                    subs = classroom.courses().courseWork().studentSubmissions().list(
                        courseId=course["id"], courseWorkId=work["id"], userId="me", pageSize=10
                    ).execute().get("studentSubmissions", [])
                    submission = subs[0] if subs else {}
                except Exception:
                    submission = {}
                assignments.append({
                    "course_id": str(course["id"]), "course": course.get("name", "Unnamed course"),
                    "id": str(work["id"]), "title": work.get("title", "Untitled assignment"),
                    "description": work.get("description", ""), "due": due_date.isoformat() if due_date else "No due date",
                    "due_date": due_date, "state": work.get("state", "unknown"),
                    "materials": work.get("materials", []), "submission": submission,
                    "work_url": work.get("alternateLink", "https://classroom.google.com"),
                })
        except Exception:
            continue
    assignments.sort(key=lambda a: (a["due_date"] is None, a["due_date"] or datetime.max.date(), a["course"].casefold()))
    return assignments


def _collect_doc_text(elements):
    parts = []
    for item in elements or []:
        if "paragraph" in item:
            for element in item["paragraph"].get("elements", []):
                text_run = element.get("textRun", {}).get("content")
                if text_run:
                    parts.append(text_run)
        if "table" in item:
            for row in item["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    parts.append(_collect_doc_text(cell.get("content", [])))
    return "".join(parts)


def assignment_materials_text(assignment):
    classroom, drive, docs, slides = google_workspace_services()
    chunks = [f"ASSIGNMENT: {assignment['title']}\nCOURSE: {assignment['course']}\nDUE: {assignment['due']}\n\nINSTRUCTIONS:\n{assignment['description'] or '(No written instructions supplied.)'}"]

    def read_drive_file(file_id, file_title):
        meta = drive.files().get(fileId=file_id, fields="id,name,mimeType,webViewLink").execute()
        mime = meta.get("mimeType", "")
        if mime == "application/vnd.google-apps.document":
            doc = docs.documents().get(documentId=file_id).execute()
            return _collect_doc_text(doc.get("body", {}).get("content", []))[:18000]
        if mime == "application/vnd.google-apps.presentation":
            deck = slides.presentations().get(presentationId=file_id).execute()
            slide_text = []
            for slide in deck.get("slides", []):
                for element in slide.get("pageElements", []):
                    shape = element.get("shape", {})
                    for te in shape.get("text", {}).get("textElements", []):
                        content = te.get("textRun", {}).get("content")
                        if content:
                            slide_text.append(content)
            return "\n".join(slide_text)[:18000] or "(No readable slide text.)"
        filename = meta.get("name", file_title or "attachment")
        suffix = Path(filename).suffix.lower()
        if suffix in {".pdf", ".docx", ".pptx", ".txt", ".md", ".csv", ".json"}:
            payload = drive.files().get_media(fileId=file_id).execute()
            if not isinstance(payload, bytes):
                payload = bytes(payload)
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
                temp.write(payload)
                temp_path = Path(temp.name)
            try:
                return read_text_file(temp_path)[:18000]
            finally:
                try:
                    temp_path.unlink()
                except OSError:
                    pass
        return "Open this attached file to read its contents: " + meta.get("webViewLink", "(link unavailable)")

    for material in assignment.get("materials", []):
        if "driveFile" in material:
            file_info = material["driveFile"].get("driveFile", {})
            file_id = file_info.get("id")
            file_title = file_info.get("title", "Attached material")
            chunks.append(f"\n\nTEACHER MATERIAL: {file_title}")
            if file_id:
                try:
                    chunks.append(read_drive_file(file_id, file_title))
                except Exception as exc:
                    chunks.append(f"Could not read this material automatically: {exc}")
        elif "link" in material:
            link = material.get("link", {})
            chunks.append(f"\n\nLINK: {link.get('title', 'Teacher-provided link')} — {link.get('url', '')}\nCLIVE cannot assume it can read external links that require a separate login.")
        elif "youtubeVideo" in material:
            vid = material.get("youtubeVideo", {}).get("youtubeVideoId", "")
            chunks.append(f"\n\nYouTube material: https://www.youtube.com/watch?v={vid}")

    sub = assignment.get("submission", {})
    chunks.append(f"\n\nYOUR WORK / SUBMISSION STATE: {sub.get('state', 'unknown')}")
    for attachment in sub.get("assignmentSubmission", {}).get("attachments", []):
        drive_file = attachment.get("driveFile", {})
        link = attachment.get("link", {})
        title = drive_file.get("title") or link.get("title") or "Attached file"
        chunks.append(f"\n\nYOUR WORK ATTACHMENT: {title}")
        if drive_file.get("id"):
            try:
                chunks.append(read_drive_file(drive_file["id"], title))
            except Exception as exc:
                chunks.append(f"Could not read your attachment automatically: {exc}")
        elif link.get("url"):
            chunks.append(link["url"])
    return "\n".join(chunks)


def create_google_doc(title, body=""):
    _, drive, docs, _ = google_workspace_services()
    document = docs.documents().create(body={"title": title}).execute()
    document_id = document["documentId"]
    if body.strip():
        docs.documents().batchUpdate(documentId=document_id, body={"requests": [{"insertText": {"location": {"index": 1}, "text": body}}]}).execute()
    return {"id": document_id, "title": title, "url": f"https://docs.google.com/document/d/{document_id}/edit"}


def submit_classroom_assignment(assignment, document_id=None):
    _, classroom = google_services()
    course_id, work_id = assignment["course_id"], assignment["id"]
    submissions = classroom.courses().courseWork().studentSubmissions().list(
        courseId=course_id, courseWorkId=work_id, userId="me", pageSize=10
    ).execute().get("studentSubmissions", [])
    if not submissions:
        raise RuntimeError("Google Classroom did not return your student submission for this assignment.")
    submission = submissions[0]
    state = submission.get("state", "")
    if state == "TURNED_IN":
        return "This assignment is already marked as turned in."
    if document_id:
        classroom.courses().courseWork().studentSubmissions().modifyAttachments(
            courseId=course_id, courseWorkId=work_id, id=submission["id"],
            body={"addAttachments": [{"driveFile": {"id": document_id}}]}
        ).execute()
    classroom.courses().courseWork().studentSubmissions().turnIn(
        courseId=course_id, courseWorkId=work_id, id=submission["id"], body={}
    ).execute()
    return "Google Classroom accepted the turn-in request. Please verify the assignment shows Turned in."


def google_calendar_summary():
    calendar, _ = google_services()
    now = datetime.now().astimezone()
    end = now + timedelta(days=14)
    events = calendar.events().list(calendarId="primary", timeMin=now.isoformat(), timeMax=end.isoformat(), maxResults=25, singleEvents=True, orderBy="startTime").execute().get("items", [])
    if not events:
        return "No upcoming calendar events were found in the next 14 days."
    lines = []
    for event in events:
        start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "Time unknown"))
        lines.append(f"- {start}: {event.get('summary', '(No title)')}" + (f" — {event.get('location')}" if event.get("location") else ""))
    return "Upcoming Google Calendar events:\n" + "\n".join(lines)


def classroom_summary():
    _, classroom = google_services()
    courses = classroom.courses().list(courseStates=["ACTIVE"], pageSize=100).execute().get("courses", [])
    if not courses:
        return "No active Google Classroom courses were found."
    lines = []
    for course in courses:
        course_name = course.get("name", "Unnamed course")
        try:
            works = classroom.courses().courseWork().list(courseId=course["id"], orderBy="dueDate asc", pageSize=100).execute().get("courseWork", [])
        except Exception as exc:
            lines.append(f"{course_name}: unable to retrieve coursework ({exc})")
            continue
        for work in works:
            due = work.get("dueDate")
            due_text = "No due date"
            if due:
                due_time = work.get("dueTime", {})
                due_text = f"{due.get('year')}-{due.get('month', 1):02d}-{due.get('day', 1):02d}"
                if due_time:
                    due_text += f" {due_time.get('hours', 0):02d}:{due_time.get('minutes', 0):02d}"
            lines.append(f"- {course_name}: {work.get('title', 'Untitled')} — due {due_text}; status {work.get('state', 'unknown')}")
    return "Google Classroom coursework:\n" + ("\n".join(lines[:100]) if lines else "No coursework was listed for your active courses.")


def is_time_question(text):
    normalized = re.sub(r"[^a-z0-9ぁ-んァ-ン一-龯々ー]", "", text.casefold())
    phrases = (
        "ima nanji", "iman anji", "いまなんじ", "今何時", "いま何時", "何時ですか",
        "what time is it", "whats the time", "what's the time", "current time", "time now",
    )
    lower = text.casefold().strip()
    return any(phrase in lower for phrase in phrases) or normalized in {"iman anji", "iman nanji", "いまなんじ", "今何時"}


def is_date_question(text):
    lower = re.sub(r"\s+", " ", text.casefold()).strip(" .?!,")
    phrases = (
        "what is today's date", "what's today's date", "whats today's date",
        "what is the date", "what's the date", "whats the date", "today's date",
        "todays date", "what day is it", "what day is today", "which day is it",
        "what is today", "what's today", "whats today", "current date",
        "what date is it", "tell me the date", "tell me today's date",
    )
    return any(phrase in lower for phrase in phrases)


def parse_timer(text):
    lower = text.lower().strip()
    if not any(w in lower for w in ("timer", "remind me", "reminder", "countdown")):
        return None
    if any(p in lower for p in ("cancel timer", "cancel the timer", "stop timer", "stop the timer")):
        return {"action": "cancel"}
    match = re.search(r"(?:for\s+|in\s+)?(\d+(?:\.\d+)?)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)", lower)
    if not match:
        return {"action": "help"}
    amount, unit = float(match.group(1)), match.group(2)
    seconds = int(amount * (1 if unit.startswith(("second", "sec")) else 60 if unit.startswith(("minute", "min")) else 3600))
    if not 1 <= seconds <= 604800:
        return {"action": "invalid"}
    return {"action": "start", "seconds": seconds}


def duration_text(seconds):
    hours, rem = divmod(int(seconds), 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if hours: parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if minutes: parts.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))
    if seconds or not parts: parts.append(f"{seconds} second" + ("s" if seconds != 1 else ""))
    return " ".join(parts)


def read_macos_notifications():
    # Reads the signed-in user's visible Notification Center through macOS Accessibility UI scripting.
    if sys.platform != "darwin":
        raise RuntimeError("Notification reading currently requires macOS.")
    script = r'''set capturedText to ""
set toggleItem to missing value
tell application "System Events"
  tell process "ControlCenter"
    try
      repeat with menuItem in (menu bar items of menu bar 1)
        try
          set itemDescription to description of menuItem as text
          set itemName to name of menuItem as text
          if itemDescription contains "Date and Time" or itemDescription contains "Clock" or itemDescription contains "Notification Center" or itemName contains "Clock" then
            set toggleItem to menuItem
            exit repeat
          end if
        end try
      end repeat
      if toggleItem is not missing value then click toggleItem
    end try
  end tell
  delay 1
  try
    tell process "NotificationCenter"
      if (count of windows) > 0 then
        repeat with uiElement in (entire contents of window 1)
          repeat with propertyName in {"name", "description", "value", "title"}
            try
              set itemText to ""
              if propertyName is "name" then set itemText to name of uiElement as text
              if propertyName is "description" then set itemText to description of uiElement as text
              if propertyName is "value" then set itemText to value of uiElement as text
              if propertyName is "title" then set itemText to title of uiElement as text
              if itemText is not "" and itemText is not "missing value" and itemText is not "Notification Center" then
                if capturedText does not contain itemText then set capturedText to capturedText & itemText & linefeed
              end if
            end try
          end repeat
        end repeat
      end if
    end tell
  end try
  if toggleItem is not missing value then
    try
      tell process "ControlCenter" to click toggleItem
    end try
  end if
end tell
return capturedText'''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=12)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Could not inspect Notification Center: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Accessibility permission was denied.").strip()
        raise RuntimeError(detail[:500])
    output = result.stdout.strip()
    if not output:
        raise RuntimeError("No readable notifications were found. Grant Accessibility access to the app running CLIVE in System Settings > Privacy & Security > Accessibility.")
    lines, seen = [], set()
    for line in output.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 2 or line in seen:
            continue
        seen.add(line)
        lines.append(line)
    return "\n".join(lines)[:12000]



def safe_app_name(text):
    """Resolve a small allowlist of macOS apps; never pass arbitrary shell text."""
    value = text.strip().casefold()
    apps = {
        "safari": "Safari", "calculator": "Calculator", "notes": "Notes",
        "finder": "Finder", "calendar": "Calendar", "music": "Music",
        "photos": "Photos", "messages": "Messages", "mail": "Mail",
        "reminders": "Reminders", "maps": "Maps", "preview": "Preview",
        "system settings": "System Settings", "settings": "System Settings",
        "activity monitor": "Activity Monitor", "textedit": "TextEdit",
        "text edit": "TextEdit", "terminal": "Terminal", "vscode": "Visual Studio Code",
        "visual studio code": "Visual Studio Code", "chrome": "Google Chrome",
        "google chrome": "Google Chrome", "firefox": "Firefox", "discord": "Discord",
        "spotify": "Spotify", "roblox": "Roblox",
    }
    return apps.get(value)


def clean_folder_name(value):
    """Return a conservative folder name with no path separators or traversal."""
    value = re.sub(r'[\\/:*?"<>|]', "", value).strip().strip(".")
    value = re.sub(r"\s+", " ", value)
    if value in {"", ".", ".."}:
        return None
    return value[:80]


class CliveApp:
    def __init__(self, root):
        self.root = root
        root.title("CLIVE")
        root.configure(bg=BG)
        root.resizable(True, True)
        root.minsize(520, 560)
        self.listening = threading.Event()
        self.listening.set()
        self.model_ready = threading.Event()
        self.closing = threading.Event()
        self.request_lock = threading.Lock()
        self.request_active = False
        self.last_spoken_until = 0.0
        self.article_window = None
        self.article_text = None
        self.current_article_image = None
        self.current_article_image_url = None
        self.current_article_plaintext = ""
        self.article_fullscreen = False
        self.main_fullscreen = False
        self.notification_watch = threading.Event()
        self.notification_busy = threading.Lock()
        self.last_notification_fingerprint = ""
        self.current_dropped_image_path = None
        self.current_image_search_query = ""
        self._build_banner()
        self._enable_drag_and_drop()
        self.root.bind("<Escape>", self._main_escape)
        self.root.bind("<F11>", lambda _event: self._toggle_main_fullscreen())
        self.root.bind("<Command-Return>", lambda _event: self._toggle_main_fullscreen())
        self.root.bind("<Command-Control-f>", lambda _event: self._toggle_main_fullscreen())
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._start_microphone)
        self.root.after(150, self._start)

    def _start_microphone(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self._set_title("CLIVE — speech recognition package missing")
            messagebox.showerror(
                "CLIVE microphone",
                "SpeechRecognition is not installed in this Python environment.\n\n"
                "Activate CLIVE's .venv, then run:\n"
                'python -m pip install "SpeechRecognition[audio]"'
            )
            return
        threading.Thread(target=self._listen_loop, args=(sr,), daemon=True).start()

    def _build_banner(self):
        self.root.geometry("520x500")
        self.root.minsize(360, 360)
        self.root.configure(bg=BG)

        shell = tk.Frame(self.root, bg=BG, padx=18, pady=18,
                         highlightthickness=1, highlightbackground="#1E8FC0")
        shell.pack(fill="both", expand=True, padx=8, pady=8)

        # Compact butler signature: the signature is the whole interface.
        self.signature_label = tk.Label(
            shell,
            text=PrintBanner(),
            bg=BG, fg=ACCENT, font=("Menlo", 6, "bold"),
            justify="center", padx=8, pady=8
        )
        self.signature_label.pack(expand=True, pady=(10, 2))

        self.drop_zone = shell
        self.signature_frame = shell
        self.signature_visible = True

    def _toggle_signature(self):
        return

    def _choose_file(self):
        paths = filedialog.askopenfilenames(title="Choose files for CLIVE")
        if paths:
            self._on_selected_files([Path(item) for item in paths])

    def _on_selected_files(self, paths):
        paths = [Path(path) for path in paths if Path(path).is_file()]
        if paths:
            threading.Thread(target=self._process_dropped_files, args=(paths,), daemon=True).start()

    def _toggle_main_fullscreen(self):
        try:
            self.main_fullscreen = not self.main_fullscreen
            self.root.attributes("-fullscreen", self.main_fullscreen)
            if not self.main_fullscreen:
                self.root.geometry("520x500")
            self._set_title("CLIVE — full screen" if self.main_fullscreen else "CLIVE")
        except tk.TclError:
            pass
        return "break"

    def _main_escape(self, _event=None):
        if self.main_fullscreen:
            self.main_fullscreen = False
            try:
                self.root.attributes("-fullscreen", False)
                self.root.geometry("520x500")
            except tk.TclError:
                pass
            return "break"
        return "break"

    def _enable_drag_and_drop(self):
        if not DND_AVAILABLE:
            return
        try:
            for widget in (self.root, self.drop_zone, self.signature_label):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop_files)
        except Exception:
            pass

    def _on_drop_files(self, event):
        try:
            paths = [Path(item) for item in self.root.tk.splitlist(event.data)]
            paths = [item for item in paths if item.is_file()]
        except Exception:
            paths = []
        if not paths:
            self._speak("I couldn't identify a readable file in that drop, sir.")
            return "break"
        threading.Thread(target=self._process_dropped_files, args=(paths,), daemon=True).start()
        return "break"

    def _process_dropped_files(self, paths):
        if not self.request_lock.acquire(blocking=False):
            self._speak("One moment, sir. I'm finishing another request first.")
            return
        try:
            self._set_title("CLIVE — reviewing your file…")
            for path in paths[:5]:
                try:
                    IsImage = path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp", ".heic", ".heif"}
                    if IsImage:
                        self.current_dropped_image_path = str(path)
                        self.current_image_search_query = ""
                        try:
                            summary = analyze_image_with_vision(path)
                        except RuntimeError as vision_error:
                            # Do not pass generic classifier labels to a text-only LLM and pretend it saw the photo.
                            try:
                                raw = ocr_image(path)
                            except Exception as ocr_error:
                                raw = "Image OCR/classification unavailable: " + str(ocr_error)[:300]
                            summary = (
                                "## Image analysis unavailable\n\n"
                                "CLIVE's current chat model is text-only, so it cannot genuinely inspect this photo or "
                                "identify the people in it. I have not guessed their identities.\n\n"
                                "**Setup needed:** add a local vision-language model and its matching mmproj file to "
                                "the CLIVE folder.\n\n"
                                "**Current on-device image scan:**\n\n" + raw[:5000] +
                                "\n\n**Technical detail:** " + str(vision_error)[:400]
                            )
                    else:
                        raw = read_text_file(path)
                        if not raw.strip():
                            raise RuntimeError("No readable text was found in that file.")
                        prompt = (
                            f"Summarise the contents of the user's file named {path.name}. Give a clear title, key points, "
                            "and useful conclusions. Do not claim facts not present in the file. Use readable Markdown.\n\n"
                            + raw[:40000]
                        )
                        summary = generate(messages_for(prompt), max_tokens=DISPLAY_TOKENS)
                        if not summary.strip():
                            summary = raw[:12000]
                        self.current_dropped_image_path = None
                        self.current_image_search_query = ""
                    self._remember_exchange("Review dropped file: " + path.name, summary)
                    self.root.after(0, lambda t=title_case_topic(path.stem), a=summary: self.show_article(t, a, [], []))
                    if IsImage:
                        self._speak("I've examined the image. The findings are on screen." if "## Image analysis unavailable" not in summary else "Image analysis needs attention. The details are on screen.")
                    else:
                        self._speak("I've reviewed " + path.name + ". The findings are on screen.")
                except Exception as exc:
                    self._speak("I couldn't read " + path.name + ". " + str(exc)[:120])
            self._set_title("CLIVE — ready")
        finally:
            self.request_lock.release()

    def _toggle_article_fullscreen(self):
        window = self.article_window
        if window is None:
            self._speak("There isn't an article open to maximise, sir.")
            return
        try:
            if not window.winfo_exists():
                return
            self.article_fullscreen = not self.article_fullscreen
            window.attributes("-fullscreen", self.article_fullscreen)
            if not self.article_fullscreen:
                window.geometry("900x760")
            self._set_title("CLIVE — article full screen" if self.article_fullscreen else "CLIVE — article window")
        except tk.TclError:
            self._speak("I couldn't change the article window size, sir.")

    def _exit_article_fullscreen(self):
        if self.article_fullscreen:
            self.article_fullscreen = False
            try:
                self.article_window.attributes("-fullscreen", False)
                self.article_window.geometry("900x760")
            except tk.TclError:
                pass
        return "break"

    def _read_article_aloud(self):
        article = self.current_article_plaintext.strip()
        if not article:
            self._speak("There isn't an article ready to read aloud, sir.")
            return
        self._set_title("CLIVE — reading the article aloud, sir…")
        say(article, max_words=10000, full_text=True)

    def _set_title(self, text):
        def update_title():
            if not self.root.winfo_exists():
                return
            self.root.title(text)
            status = getattr(self, "status_label", None)
            if status is not None and status.winfo_exists():
                lower = text.lower()
                if "failed" in lower or "error" in lower:
                    label, color = "SYSTEM NEEDS ATTENTION", RED
                elif "thinking" in lower or "reviewing" in lower or "reading" in lower or "starting" in lower or "opening" in lower:
                    label, color = "ANALYSING…", ACCENT
                else:
                    label, color = "SYSTEM STANDBY", GREEN
                status.configure(text=label, fg=color, bg=BG)
        try:
            self.root.after(0, update_title)
        except tk.TclError:
            pass

    def _start(self):
        self._set_title("CLIVE — starting local intelligence")
        threading.Thread(target=self._server_worker, daemon=True).start()

    def _server_worker(self):
        if not start_server(lambda message, _color=None: self._set_title("CLIVE — " + message)):
            self._set_title("CLIVE — model startup failed")
            return
        self.model_ready.set()
        self._set_title("CLIVE — ready")
        hour = datetime.now().astimezone().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        self._speak(f"{greeting}, sir. CLIVE is ready.")
        threading.Thread(target=self._startup_homework_briefing, daemon=True).start()

    def toggle_listening(self):
        if self.listening.is_set():
            self.listening.clear()
            self._set_title("CLIVE — microphone paused (click Resume listening)")
            say("Of course, sir. I shall remain quiet until you call upon me.")
        else:
            self.listening.set()
            self._set_title("CLIVE — ready")
            say("At once, sir. I am listening.")

    def _transcribe_local(self, audio):
        import subprocess
        import tempfile
        import wave

        WhisperCLI = BASE_DIR / "whisper.cpp" / "build" / "bin" / "whisper-cli"
        WhisperModel = BASE_DIR / "whisper.cpp" / "models" / "ggml-base.en.bin"

        if not WhisperCLI.is_file() or not WhisperModel.is_file():
            self._set_title("CLIVE — local Whisper files missing")
            return ""

        try:
            AudioData = audio.get_wav_data(convert_rate=16000, convert_width=2)

            with tempfile.TemporaryDirectory(prefix="clive_whisper_") as TempDir:
                TempPath = Path(TempDir)
                AudioPath = TempPath / "recording.wav"
                OutputBase = TempPath / "transcript"

                with wave.open(str(AudioPath), "wb") as Wav:
                    Wav.setnchannels(1)
                    Wav.setsampwidth(2)
                    Wav.setframerate(16000)
                    Wav.writeframes(AudioData)

                Result = subprocess.run(
                    [
                        str(WhisperCLI),
                        "-m", str(WhisperModel),
                        "-f", str(AudioPath),
                        "-nt",
                        "-t", "6",
                        "-bs", "1",
                        "--temperature", "0",
                        "-otxt",
                        "-of", str(OutputBase),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )

                TranscriptPath = OutputBase.with_suffix(".txt")

                if Result.returncode != 0 or not TranscriptPath.is_file():
                    self._set_title("CLIVE — local transcription failed")
                    print("Whisper error:", Result.stderr[-2000:])
                    return ""

                return TranscriptPath.read_text().strip()

        except Exception as Exc:
            self._set_title("CLIVE — local transcription error")
            print("Local Whisper error:", Exc)
            return ""

    def _listen_loop(self, sr):
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.12
        recognizer.dynamic_energy_ratio = 1.75
        recognizer.pause_threshold = 0.80
        recognizer.phrase_threshold = 0.40
        recognizer.non_speaking_duration = 0.50
        try:
            # Prefer the exact microphone that passed the user's test, then fall back safely.
            device_names = sr.Microphone.list_microphone_names()
            device_index = next(
                (index for index, name in enumerate(device_names)
                 if "macbook pro microphone" in name.casefold()),
                None,
            )
            microphone = sr.Microphone(device_index=device_index)
        except Exception as exc:
            self._set_title("CLIVE — microphone unavailable")
            self.root.after(0, lambda exc=exc: messagebox.showerror(
                "CLIVE microphone", f"I could not open the microphone. Check macOS microphone permission and PyAudio.\n\n{exc}"
            ))
            return
        try:
            with microphone as source:
                self._set_title("CLIVE — calibrating microphone…")
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                self._set_title("CLIVE — microphone ready; waiting for local model…")
                while not self.closing.is_set():
                    if not self.listening.is_set():
                        time.sleep(0.15)
                        continue
                    if not self.model_ready.is_set():
                        time.sleep(0.15)
                        continue
                    # Wait before recording while CLIVE is speaking, rather than
                    # recording the user's words and throwing them away afterward.
                    if VOICE_ACTIVE.is_set() or time.monotonic() < self.last_spoken_until:
                        time.sleep(0.12)
                        continue
                    try:
                        audio = recognizer.listen(source, timeout=1.5, phrase_time_limit=12)
                    except sr.WaitTimeoutError:
                        continue
                    # If CLIVE began speaking while listen() was waiting, discard that recording.
                    if VOICE_ACTIVE.is_set():
                        continue
                    # Ignore very short bursts, which are often breaths, clicks, or room noise.
                    try:
                        audio_seconds = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                    except (AttributeError, ZeroDivisionError):
                        audio_seconds = 1.0
                    if audio_seconds < 0.70:
                        continue
                    try:
                        heard = re.sub(r"\s+", " ", self._transcribe_local(audio)).strip()
                        if not heard or not any(char.isalpha() for char in heard):
                            continue
                        if heard.casefold().strip(" .,!?") in {"uh", "um", "hmm", "ah", "erm", "mm"}:
                            continue
                    except sr.UnknownValueError:
                        # Stay quiet on unrecognisable sound; breaths should not trigger a spoken response.
                        continue
                    except sr.RequestError:
                        self._set_title("CLIVE — speech recognition needs internet")
                        time.sleep(1)
                        continue
                    if heard:
                        self._set_title("CLIVE — heard: " + heard[:55])
                        self._handle_voice(heard)
        except Exception as exc:
            if not self.closing.is_set():
                self._set_title("CLIVE — microphone error")
                self.root.after(0, lambda exc=exc: messagebox.showerror("CLIVE microphone", str(exc)))

    def _handle_simple_action(self, text):
        """Run a few explicit, allowlisted Mac actions. Return True when handled."""
        raw = text.strip().strip(" .!?")
        lower = raw.casefold()
        lower = re.sub(r"^(?:hey[, ]+)?(?:clive[, ]+)?", "", lower).strip()

        # Open a known macOS app. No arbitrary command or shell text is executed.
        match = re.fullmatch(r"(?:please\s+)?(?:open|launch|start)\s+(?:the\s+)?(.+)", lower)
        if match:
            app = safe_app_name(match.group(1))
            if app:
                try:
                    subprocess.Popen(["open", "-a", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._set_title(f"CLIVE — opening {app}")
                    self._speak(f"Opening {app}.")
                except OSError as exc:
                    self._speak(f"I couldn't open {app}: {exc}")
                return True

        # Open common sites by name or accept a complete HTTP(S) URL.
        sites = {
            "google": "https://www.google.com", "youtube": "https://www.youtube.com",
            "gmail": "https://mail.google.com", "google drive": "https://drive.google.com",
            "google classroom": "https://classroom.google.com", "wikipedia": "https://www.wikipedia.org",
            "roblox": "https://www.roblox.com", "discord": "https://discord.com/app",
            "github": "https://github.com", "chatgpt": "https://chatgpt.com",
        }
        match = re.fullmatch(r"(?:please\s+)?(?:open|visit|go to)\s+(.+)", lower)
        if match:
            target = match.group(1).strip()
            url = sites.get(target)
            if not url and re.fullmatch(r"https?://[^\s]+", target, flags=re.I):
                url = target
            if url:
                try:
                    webbrowser.open(url)
                    self._set_title("CLIVE — website opened")
                    self._speak("Done.")
                except Exception as exc:
                    self._speak(f"I couldn't open that website: {exc}")
                return True

        # Open a familiar folder in Finder, without accepting arbitrary filesystem paths.
        folders = {
            "downloads": Path.home() / "Downloads", "documents": Path.home() / "Documents",
            "desktop": Path.home() / "Desktop", "applications": Path("/Applications"),
            "clive folder": Path.home() / "Documents" / "CLIVE",
        }
        match = re.fullmatch(r"(?:please\s+)?(?:open|show)\s+(?:my\s+)?(.+?)(?:\s+folder)?", lower)
        if match:
            target = match.group(1).strip()
            folder = folders.get(target)
            if folder and folder.exists():
                try:
                    subprocess.Popen(["open", str(folder)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._set_title("CLIVE — Finder folder opened")
                    self._speak("Here you are.")
                except OSError as exc:
                    self._speak(f"I couldn't open that folder: {exc}")
                return True

        # Create a named folder in a dedicated safe location, never deleting or overwriting files.
        match = re.fullmatch(r"(?:please\s+)?create (?:a )?folder (?:called|named) (.+)", raw, flags=re.I)
        if match:
            name = clean_folder_name(match.group(1))
            if not name:
                self._speak("Please give the folder a valid name.")
                return True
            destination = Path.home() / "Documents" / "CLIVE" / "Created by CLIVE" / name
            try:
                destination.mkdir(parents=True, exist_ok=False)
                self._set_title("CLIVE — folder created")
                self._speak(f"Created the folder {name} in your CLIVE project folder.")
            except FileExistsError:
                self._speak(f"A folder named {name} already exists there.")
            except OSError as exc:
                self._speak(f"I couldn't create that folder: {exc}")
            return True
        return False

    def _open_homework_workspace(self):
        self.root.after(0, self._build_homework_workspace)

    def _build_homework_workspace(self):
        if getattr(self, "homework_window", None) is not None:
            try:
                if self.homework_window.winfo_exists():
                    self.homework_window.lift()
                    return
            except tk.TclError:
                pass
        window = tk.Toplevel(self.root)
        self.homework_window = window
        window.title("CLIVE — Homework Workspace")
        window.geometry("980x720")
        window.configure(bg=BG)
        window.minsize(720, 520)
        top = tk.Frame(window, bg=BG, padx=14, pady=12)
        top.pack(fill="x")
        tk.Label(top, text="HOMEWORK WORKSPACE", bg=BG, fg=ACCENT, font=("Menlo", 15, "bold")).pack(anchor="w")
        tk.Label(top, text="Assignments • Your work • Teacher materials • Documents", bg=BG, fg=MUTED, font=("Helvetica", 10)).pack(anchor="w", pady=(4, 8))
        controls = tk.Frame(window, bg=BG, padx=14)
        controls.pack(fill="x")
        self.homework_assignment_var = tk.StringVar(value="Loading assignments…")
        self.homework_assignment_box = tk.OptionMenu(controls, self.homework_assignment_var, "Loading assignments…")
        self.homework_assignment_box.configure(bg=PANEL, fg=TEXT, activebackground=PANEL2, activeforeground=TEXT, highlightthickness=0, width=52)
        self.homework_assignment_box["menu"].configure(bg=PANEL, fg=TEXT)
        self.homework_assignment_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(controls, text="Refresh", command=self._refresh_homework_assignments, bg=PANEL2, fg=TEXT, activebackground=ACCENT).pack(side="left", padx=3)
        tk.Button(controls, text="Inspect assignment", command=self._inspect_selected_assignment, bg=PANEL2, fg=TEXT, activebackground=ACCENT).pack(side="left", padx=3)
        body = tk.Frame(window, bg=BG, padx=14, pady=12)
        body.pack(fill="both", expand=True)
        self.homework_editor = tk.Text(body, wrap="word", bg="#081E33", fg=TEXT, insertbackground=TEXT, selectbackground="#17618B", font=("Menlo", 11), undo=True, padx=12, pady=12, relief="flat")
        scroll = tk.Scrollbar(body, command=self.homework_editor.yview)
        self.homework_editor.configure(yscrollcommand=scroll.set)
        self.homework_editor.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.homework_editor.insert("1.0", "Choose an assignment, then select Inspect assignment to read its instructions and available materials.\n\nYou can draft or edit your work here. Create Google Doc saves the text to your Google Drive. Submit asks for confirmation before attaching the document and turning in the selected assignment.")
        bottom = tk.Frame(window, bg=BG, padx=14, pady=(0, 14))
        bottom.pack(fill="x")
        tk.Button(bottom, text="Help me draft", command=self._draft_assignment_with_clive, bg=ACCENT, fg="#06172B", activebackground="#8CEBFF", font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 8))
        tk.Button(bottom, text="Create Google Doc", command=self._create_doc_from_workspace, bg=PANEL2, fg=TEXT, activebackground=ACCENT).pack(side="left", padx=8)
        tk.Button(bottom, text="Submit selected assignment", command=self._confirm_submit_selected, bg="#B53C61", fg="white", activebackground="#D85D7F", font=("Helvetica", 10, "bold")).pack(side="left", padx=8)
        tk.Button(bottom, text="Open assignment in Classroom", command=self._open_selected_assignment, bg=PANEL2, fg=TEXT, activebackground=ACCENT).pack(side="left", padx=8)
        self.homework_assignments = []
        self.homework_selected_doc = None
        self._refresh_homework_assignments()

    def _refresh_homework_assignments(self):
        if not getattr(self, "homework_window", None):
            return
        try:
            if not self.homework_window.winfo_exists():
                return
        except tk.TclError:
            return
        self.homework_assignment_var.set("Loading assignments…")
        threading.Thread(target=self._load_homework_assignments_worker, daemon=True).start()

    def _load_homework_assignments_worker(self):
        try:
            assignments = classroom_assignments(include_past=True)
            error = None
        except Exception as exc:
            assignments, error = [], str(exc)
        def finish():
            if not getattr(self, "homework_window", None):
                return
            try:
                if not self.homework_window.winfo_exists():
                    return
                self.homework_assignments = assignments
                menu = self.homework_assignment_box["menu"]
                menu.delete(0, "end")
                labels = []
                for assignment in assignments:
                    substate = assignment.get("submission", {}).get("state", "UNKNOWN")
                    label = f"{assignment['course']} | {assignment['title']} | due {assignment['due']} | {substate}"
                    labels.append(label)
                    menu.add_command(label=label, command=lambda value=label: self.homework_assignment_var.set(value))
                if error:
                    self.homework_assignment_var.set("Google connection needed")
                    self.homework_editor.delete("1.0", "end")
                    self.homework_editor.insert("1.0", "Could not load Google Classroom assignments.\n\n" + error + "\n\nCheck credentials.json, Google API enablement, OAuth permissions, and your school account's administrator restrictions.")
                elif labels:
                    self.homework_assignment_var.set(labels[0])
                    self.homework_editor.delete("1.0", "end")
                    self.homework_editor.insert("1.0", f"Loaded {len(assignments)} assignments. Select one and click Inspect assignment to read its instructions, Your work status, and supported teacher materials.\n\nDrafting here does not submit anything automatically.")
                else:
                    self.homework_assignment_var.set("No assignments found")
                    self.homework_editor.delete("1.0", "end")
                    self.homework_editor.insert("1.0", "No assignments were returned by Google Classroom. Check that the connected account is enrolled in active courses.")
            except tk.TclError:
                pass
        self.root.after(0, finish)

    def _selected_assignment(self):
        label = self.homework_assignment_var.get()
        for assignment in getattr(self, "homework_assignments", []):
            candidate = f"{assignment['course']} | {assignment['title']} | due {assignment['due']} | {assignment.get('submission', {}).get('state', 'UNKNOWN')}"
            if candidate == label:
                return assignment
        return None

    def _inspect_selected_assignment(self):
        assignment = self._selected_assignment()
        if not assignment:
            messagebox.showinfo("CLIVE", "Choose a loaded assignment first.", parent=self.homework_window)
            return
        self.homework_editor.delete("1.0", "end")
        self.homework_editor.insert("1.0", "Reading assignment instructions and available materials…\n")
        threading.Thread(target=self._inspect_assignment_worker, args=(assignment,), daemon=True).start()

    def _inspect_assignment_worker(self, assignment):
        try:
            content = assignment_materials_text(assignment)
        except Exception as exc:
            content = f"Could not inspect this assignment: {exc}"
        def finish():
            try:
                if self.homework_window.winfo_exists():
                    self.homework_editor.delete("1.0", "end")
                    self.homework_editor.insert("1.0", content)
                    self.homework_editor.mark_set("insert", "1.0")
            except tk.TclError:
                pass
        self.root.after(0, finish)

    def _draft_assignment_with_clive(self):
        assignment = self._selected_assignment()
        if not assignment:
            messagebox.showinfo("CLIVE", "Choose an assignment first, then inspect its materials.", parent=self.homework_window)
            return
        context = self.homework_editor.get("1.0", "end-1c").strip()
        if not context:
            messagebox.showinfo("CLIVE", "Inspect the assignment first so I can use its instructions and materials.", parent=self.homework_window)
            return
        self.homework_editor.delete("1.0", "end")
        self.homework_editor.insert("1.0", "CLIVE is preparing a study draft from the instructions and materials…")
        threading.Thread(target=self._draft_assignment_worker, args=(assignment, context), daemon=True).start()

    def _draft_assignment_worker(self, assignment, context):
        try:
            prompt = (
                f"Help the student learn and prepare their own response to this school assignment: {assignment['title']} "
                f"for {assignment['course']}. Use the assignment instructions and teacher materials below. "
                "Create a clear, editable study draft that directly addresses the task, explains key reasoning, and flags any missing information. "
                "Do not invent evidence or pretend the student performed work they did not do. If the task needs personal observations or original data, add a short placeholder asking the student to supply it. "
                "Use an appropriate Year 10 level, with headings only where helpful. Keep the draft ready for the student to review and edit."
            )
            draft = generate(messages_for(prompt, context=context), max_tokens=DISPLAY_TOKENS).strip()
            if not draft:
                raise RuntimeError("The local model returned an empty draft.")
            error = None
        except Exception as exc:
            draft, error = "", str(exc)
        def finish():
            try:
                if not self.homework_window.winfo_exists():
                    return
                self.homework_editor.delete("1.0", "end")
                if error:
                    self.homework_editor.insert("1.0", "Could not prepare the draft: " + error)
                    return
                self.homework_editor.insert("1.0", draft + "\n\n---\nReview and edit this draft before creating or submitting your document.")
                self._speak("I've prepared a study draft in the workspace, sir. Please review it before submitting.")
            except tk.TclError:
                pass
        self.root.after(0, finish)

    def _create_doc_from_workspace(self):
        if not getattr(self, "homework_window", None) or not self.homework_window.winfo_exists():
            return
        from tkinter import simpledialog
        selected = self._selected_assignment()
        default_title = selected["title"] if selected else "CLIVE homework draft"
        title = simpledialog.askstring("Create Google Doc", "Document title:", initialvalue=default_title, parent=self.homework_window)
        if not title or not title.strip():
            return
        body = self.homework_editor.get("1.0", "end-1c").strip()
        self.homework_editor.insert("end", "\n\nCreating Google Doc…")
        threading.Thread(target=self._create_doc_worker, args=(title.strip(), body), daemon=True).start()

    def _create_doc_worker(self, title, body):
        try:
            document = create_google_doc(title, body)
            error = None
        except Exception as exc:
            document, error = None, str(exc)
        def finish():
            try:
                if not self.homework_window.winfo_exists():
                    return
                if error:
                    messagebox.showerror("CLIVE", "Couldn't create the Google Doc.\n\n" + error, parent=self.homework_window)
                    return
                self.homework_selected_doc = document
                self.homework_editor.insert("end", f"\n\nGOOGLE DOC CREATED: {document['title']}\n{document['url']}\nThis document is now selected as the attachment for the next confirmed submission.")
                webbrowser.open(document["url"])
                self._speak("Your Google document is ready, sir.")
            except tk.TclError:
                pass
        self.root.after(0, finish)

    def _confirm_submit_selected(self):
        assignment = self._selected_assignment()
        if not assignment:
            messagebox.showinfo("CLIVE", "Choose a loaded assignment first.", parent=self.homework_window)
            return
        doc = getattr(self, "homework_selected_doc", None)
        details = f"Assignment: {assignment['title']}\nCourse: {assignment['course']}\nDue: {assignment['due']}\n"
        if doc:
            details += f"\nAttach Google Doc: {doc['title']}\n{doc['url']}\n"
        else:
            details += "\nNo new Google Doc is selected. CLIVE will submit the existing Classroom submission without adding a new file.\n"
        details += "\nThis will submit the assignment in Google Classroom. Continue?"
        if not messagebox.askyesno("Confirm turn-in", details, parent=self.homework_window):
            self._speak("Understood. I haven't submitted anything, sir.")
            return
        threading.Thread(target=self._submit_assignment_worker, args=(assignment, doc), daemon=True).start()

    def _submit_assignment_worker(self, assignment, doc):
        try:
            result = submit_classroom_assignment(assignment, doc.get("id") if doc else None)
            error = None
        except Exception as exc:
            result, error = str(exc), str(exc)
        def finish():
            try:
                if getattr(self, "homework_window", None) and self.homework_window.winfo_exists():
                    messagebox.showerror("Turn-in failed", result, parent=self.homework_window) if error else messagebox.showinfo("Turn-in result", result, parent=self.homework_window)
                self._speak("The turn-in did not complete. " + result[:140] if error else "The turn-in request has completed. Please verify the status in Classroom, sir.")
                self._refresh_homework_assignments()
            except tk.TclError:
                pass
        self.root.after(0, finish)

    def _open_selected_assignment(self):
        assignment = self._selected_assignment()
        if assignment:
            webbrowser.open(assignment.get("work_url") or "https://classroom.google.com")

    def _startup_homework_briefing(self):
        if not GOOGLE_TOKEN.exists() or not GOOGLE_CREDENTIALS.exists():
            return
        try:
            assignments = classroom_assignments(include_past=False)
            today = datetime.now().astimezone().date()
            urgent = []
            for assignment in assignments:
                due = assignment.get("due_date")
                if due and (due - today).days <= 2 and assignment.get("submission", {}).get("state") not in {"TURNED_IN", "RETURNED"}:
                    when = "today" if due == today else "tomorrow" if (due - today).days == 1 else f"in {(due - today).days} days"
                    urgent.append(f"{assignment['title']} for {assignment['course']} is due {when}")
            if urgent:
                self.root.after(0, lambda items=urgent[:3]: self._speak("Homework briefing, sir. " + ". ".join(items) + ". Say open homework workspace to review them."))
        except Exception:
            self._set_title("CLIVE — homework briefing unavailable; check Google connection")

    def _handle_voice(self, text):
        normal = re.sub(r"[^a-z0-9 ]", "", text.casefold()).strip()

        mute_commands = {"mute", "clive mute", "clive mute yourself", "be quiet clive"}
        unmute_commands = {"unmute", "clive unmute", "clive unmute yourself", "clive speak again"}
        if normal in mute_commands:
            VOICE_MUTED.set()
            stop_voice()
            self._set_title("CLIVE — muted")
            return
        if normal in unmute_commands:
            VOICE_MUTED.clear()
            self._set_title("CLIVE — ready")
            self._speak("I'm unmuted and ready, sir.")
            return

        homework_open_commands = {
            "open homework workspace", "open my homework", "check my homework", "check google classroom",
            "show my assignments", "show homework", "homework workspace", "open classroom assignments",
        }
        if normal in homework_open_commands or normal in {"clive " + item for item in homework_open_commands}:
            self._open_homework_workspace()
            self._speak("Opening your homework workspace, sir.")
            return
        if normal in {"make a doc", "create a doc", "make a google doc", "create a google doc", "clive make a doc", "clive create a doc"}:
            self._open_homework_workspace()
            self._speak("Certainly. The workspace lets you draft and save a Google Doc to your account.")
            return
        if normal.startswith("hand in ") or normal.startswith("submit ") or normal.startswith("clive hand in ") or normal.startswith("clive submit "):
            self._open_homework_workspace()
            self._speak("I've opened the homework workspace, sir. Select the matching assignment and review the attachment before confirming Turn in.")
            return

        if self._handle_simple_action(text):
            return

        # Notification commands are opt-in and use macOS Accessibility permissions.
        notification_read_commands = {
            "read my notifications", "read notifications", "check my notifications",
            "check notifications", "what are my notifications", "read my discord notifications",
            "check discord notifications", "read discord notifications",
        }
        notification_watch_commands = {
            "watch my notifications", "watch notifications", "start watching notifications",
            "watch discord notifications", "watch my discord notifications",
        }
        notification_stop_commands = {
            "stop watching notifications", "stop notification watch", "stop watching discord",
            "stop watching my notifications",
        }
        if normal in notification_read_commands or normal in {"clive " + item for item in notification_read_commands}:
            threading.Thread(target=self._read_notifications_worker, daemon=True).start()
            return
        if normal in notification_watch_commands or normal in {"clive " + item for item in notification_watch_commands}:
            if not self.notification_watch.is_set():
                self.notification_watch.set()
                threading.Thread(target=self._notification_watch_loop, daemon=True).start()
                self._speak("Certainly, sir. I shall check your Mac notifications periodically. You can say stop watching notifications at any time.")
                self._set_title("CLIVE — notification watch enabled")
            else:
                self._speak("I'm already keeping an eye on your notifications, sir.")
            return
        if normal in notification_stop_commands or normal in {"clive " + item for item in notification_stop_commands}:
            self.notification_watch.clear()
            self._speak("Of course, sir. I'll stop monitoring notifications.")
            self._set_title("CLIVE — notification watch stopped")
            return

        main_fullscreen_commands = {
            "fullscreen clive", "full screen clive", "make clive fullscreen", "make clive full screen",
            "maximize clive", "maximise clive", "clive fullscreen window", "clive full screen window",
            "make the clive window fullscreen", "make the clive window full screen",
        }
        if normal in main_fullscreen_commands:
            self.root.after(0, self._toggle_main_fullscreen)
            return

        # Article controls are voice-operated; no extra buttons are required.
        article_read_commands = {
            "read the article", "read article", "read this article", "read it aloud",
            "read the page", "read this page", "clive read the article", "clive read article",
            "clive read it aloud", "read the article to me", "read this to me",
            "clive read the page", "read the article aloud", "read the whole article",
        }
        if normal in article_read_commands:
            self.root.after(0, self._read_article_aloud)
            return
        fullscreen_commands = {
            "full screen", "fullscreen", "go full screen", "go fullscreen", "make it full screen",
            "make the article full screen", "fullscreen the article", "full screen the article",
            "clive full screen", "clive fullscreen", "clive make the article full screen",
            "clive go full screen", "clive go fullscreen", "full screen please", "fullscreen please",
        }
        if normal in fullscreen_commands or ("fullscreen" in normal and "article" in normal) or ("full screen" in normal and "article" in normal):
            self.root.after(0, self._toggle_article_fullscreen)
            return

        # Closing an information page should never close the main CLIVE app.
        close_article_commands = {
            "close it", "close this", "close the tab", "close tab",
            "close the article", "close article", "close the window",
            "close window", "clive close it", "clive close this",
            "clive close the tab", "clive close tab", "clive close the article",
            "clive close article", "clive close the window", "clive close window",
        }
        if normal in close_article_commands:
            self.root.after(0, self._close_article)
            return

        expand_image_commands = {
            "expand image", "enlarge image", "make image bigger", "zoom image",
            "show image bigger", "expand the image", "enlarge the image",
            "make the image bigger", "make the picture bigger", "expand the picture", "enlarge the picture",
            "zoom in on the image", "clive expand image",
            "clive expand the image", "clive enlarge image", "clive enlarge the image",
            "clive make the image bigger", "clive zoom image", "clive zoom in on the image",
        }
        image_action_words = ("expand", "enlarge", "zoom", "bigger", "larger", "resize")
        image_nouns = ("image", "picture", "photo", "photograph", "image of it", "picture of it")
        if normal in expand_image_commands or (
            any(word in normal.split() for word in image_action_words)
            and any(word in normal.split() for word in image_nouns)
        ) or (any(phrase in normal for phrase in ("make it bigger", "make it larger", "zoom in", "expand it", "enlarge it")) and self.article_window is not None):
            self.root.after(0, self._expand_article_image)
            return

        if normal in {"clive stop listening", "stop listening clive", "clive be quiet", "pause listening"}:
            self.listening.clear()
            self._set_title("CLIVE — microphone paused (click Resume listening)")
            self._speak("Certainly, sir. I shall wait here.")
            return
        if normal in {"clive listen", "clive start listening", "listen clive", "resume listening"}:
            self.listening.set()
            self._set_title("CLIVE — ready")
            self._speak("At once, sir. I am listening.")
            return
        shutdown_commands = {
            "clive quit", "quit clive", "close clive", "exit clive",
            "clive shut down", "clive shutdown", "clive shut yourself down",
            "clive shutdown yourself", "clive close yourself", "shut down clive",
            "shutdown clive", "shut clive down", "clive turn yourself off",
            "clive power down", "clive terminate", "clive exit",
        }
        if normal in shutdown_commands:
            self._set_title("CLIVE — shutting down, sir")
            self.root.after(0, self.close)
            return
        if normal.startswith("clive "):
            text = text.strip()[len("clive "):].strip(" ,")
        if not text:
            return
        if not self.request_lock.acquire(blocking=False):
            self._set_title("CLIVE — one moment, sir")
            return
        # Simple clock/date requests should be answered immediately, without a filler phrase.
        if is_time_question(text) or is_date_question(text):
            self._set_title("CLIVE — checking the time")
            threading.Thread(target=self._process_request, args=(text,), daemon=True).start()
            return

        self._set_title("CLIVE — understood; working on it…")
        # Keep acknowledgements brief and varied rather than repeating one stock phrase.
        acknowledgement = random.choice(("On it.", "Let me check.", "One moment.", "I'll take a look."))
        self._speak(acknowledgement, max_words=8)
        threading.Thread(target=self._process_after_acknowledgement, args=(text,), daemon=True).start()


    def _process_after_acknowledgement(self, text):
        # Wait for the acknowledgement to finish so speech never overlaps the answer.
        deadline = time.monotonic() + 15
        while not self.closing.is_set() and time.monotonic() < deadline:
            if not VOICE_ACTIVE.is_set():
                time.sleep(0.20)
                if not VOICE_ACTIVE.is_set():
                    break
            time.sleep(0.10)
        if not self.closing.is_set():
            self._process_request(text)

    def _read_notifications_worker(self):
        if not self.notification_busy.acquire(blocking=False):
            self._speak("One moment, sir. I'm already checking notifications.")
            return
        try:
            self._set_title("CLIVE — checking notifications…")
            raw = read_macos_notifications()
            prompt = (
                "Summarise these macOS notifications for the user. For each message, state the sender if clearly present, "
                "then give a concise summary. Keep it brief and natural for speech. Do not invent sender names or content. "
                "If a sender cannot be identified, say so.\n\nNotifications:\n" + raw
            )
            summary = generate(messages_for(prompt), max_tokens=180).strip()
            if not summary:
                summary = raw[:700]
            self.last_notification_fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            self._speak(summary, max_words=100)
            self._set_title("CLIVE — ready")
        except Exception as exc:
            self._set_title("CLIVE — notification access needs setup")
            self._speak("I couldn't read the notifications, sir. Please grant Accessibility permission to the app running CLIVE in System Settings, Privacy and Security, Accessibility. " + str(exc)[:160])
        finally:
            self.notification_busy.release()

    def _notification_watch_loop(self):
        # Establish a baseline first, then speak when the visible notification text changes.
        try:
            initial = read_macos_notifications()
            self.last_notification_fingerprint = hashlib.sha256(initial.encode("utf-8")).hexdigest()
        except Exception as exc:
            self.notification_watch.clear()
            self._set_title("CLIVE — notification access needs setup")
            self._speak("I can't watch notifications yet, sir. Please grant Accessibility permission to the app running CLIVE in System Settings, Privacy and Security, Accessibility. " + str(exc)[:150])
            return
        while self.notification_watch.is_set() and not self.closing.is_set():
            for _ in range(30):
                if not self.notification_watch.is_set() or self.closing.is_set():
                    return
                time.sleep(1)
            try:
                raw = read_macos_notifications()
                fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                if fingerprint != self.last_notification_fingerprint:
                    self.last_notification_fingerprint = fingerprint
                    prompt = (
                        "These are the current macOS notifications. Summarise the likely new or changed messages, identify senders only when clearly shown, "
                        "and do not invent details. Be concise and suitable for spoken delivery.\n\n" + raw
                    )
                    summary = generate(messages_for(prompt), max_tokens=150).strip()
                    if summary:
                        self._speak(summary, max_words=90)
            except Exception as exc:
                self._set_title("CLIVE — notification check failed")
                self.notification_watch.clear()
                self._speak("I had trouble checking notifications, sir, so I've paused notification monitoring. " + str(exc)[:120])
                return

    def _expand_article_image(self, retries=0):
        """Open the currently displayed article image in a large, fitted window."""
        picture = self.current_article_image
        if picture is None:
            try:
                article_is_open = self.article_window is not None and self.article_window.winfo_exists()
            except tk.TclError:
                article_is_open = False
            if article_is_open and retries < 7:
                if retries == 0:
                    self._set_title("CLIVE — loading the image for you, sir…")
                self.root.after(650, lambda: self._expand_article_image(retries + 1))
                return
            self._speak("I'm afraid no article image has loaded yet, sir. The article itself is still open.")
            return
        try:
            image_window = tk.Toplevel(self.root)
            image_window.title("CLIVE — image viewer")
            image_window.configure(bg=BG)
            image_window.geometry("1100x760")
            image_window.minsize(500, 400)
            image_window.transient(self.article_window if self.article_window and self.article_window.winfo_exists() else self.root)
            display = picture.copy()
            display.thumbnail((1060, 670))
            photo = ImageTk.PhotoImage(display)
            image_view = tk.Label(image_window, image=photo, bg=BG, cursor="hand2")
            image_view.image = photo
            image_view.pack(fill="both", expand=True, padx=18, pady=(18, 6))
            image_view.bind("<Button-1>", lambda _event: webbrowser.open(self.current_article_image_url) if self.current_article_image_url else None)
            tk.Label(image_window, text="IMAGE VIEWER  •  Click the image to open its original source",
                     bg=BG, fg=MUTED, font=("Helvetica", 10)).pack(pady=(0, 12))
            image_window.bind("<Escape>", lambda _event: image_window.destroy())
            image_window.lift()
            self._set_title("CLIVE — image expanded, sir")
        except (tk.TclError, Exception):
            self._speak("I couldn't expand that image, sir. Please try again.")

    def _close_article(self):
        """Close only the currently open information window, leaving CLIVE running."""
        window = self.article_window
        if window is None:
            self._speak("There is no information window open at present, sir.")
            return
        try:
            if window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass
        self.article_window = None
        self.article_text = None
        self.current_article_image = None
        self.current_article_image_url = None
        self.current_article_plaintext = ""
        self.article_fullscreen = False
        self._speak("Certainly, sir. I've closed the article.")
        self._set_title("CLIVE — listening (click Pause listening)")

    def _speak(self, text, max_words=40):
        self.last_spoken_until = time.monotonic() + 0.35
        say(text, max_words=max_words)

    def _process_request(self, text):
        try:
            if is_time_question(text):
                reply = "It’s " + datetime.now().astimezone().strftime("%-I:%M %p").lower() + "."
                self._remember_exchange(text, reply)
                self._speak(reply)
                self._set_title("CLIVE — ready")
                return
            if is_date_question(text):
                now = datetime.now().astimezone()
                reply = f"Today is {now.strftime('%A, %-d %B %Y')}."
                self._remember_exchange(text, reply)
                self._speak(reply)
                self._set_title("CLIVE — ready")
                return
            topic = display_topic(text)
            sources = []
            if topic:
                self._set_title("CLIVE — understood, sir; researching " + topic[:30] + "…")
                results, search_error = search_web(topic)
                sources = results or []
                image_urls = search_images(topic, limit=4)
                context = search_context(sources) if sources else ""
                prompt = (
                    f"The user asked CLIVE to bring up information about: {topic}. "
                    "Write a useful mini-article, about 250-400 words, with a clear title and short sections. "
                    "Cover what it is, key facts, why it matters, and interesting details. Paraphrase source material. "
                    "Do not invent facts. If retrieved information is available, ground factual claims in it. "
                    + ("Web search returned no results; answer from existing knowledge and do not claim to have searched." if not sources else "")
                )
                reply = generate(messages_for(prompt, context=context), max_tokens=DISPLAY_TOKENS)
                if not reply:
                    raise RuntimeError("The local model returned an empty response.")
                self._remember_exchange(text, reply)
                display_title = title_case_topic(topic)
                self.root.after(0, lambda t=display_title, r=reply, s=sources, images=image_urls: self.show_article(t, r, s, images))
                spoken = spoken_paraphrase(reply)
                self._speak(spoken, max_words=55)
            else:
                self._set_title("CLIVE — thinking, sir…")
                reply = generate(messages_for(text), max_tokens=MAX_TOKENS)
                if not reply:
                    raise RuntimeError("The local model returned an empty response.")
                self._remember_exchange(text, reply)
                self._speak(reply)
            self._set_title("CLIVE — ready")
        except Exception as exc:
            apology = f"I apologise, sir. I couldn't complete that request: {exc}"
            self._speak(apology)
            self._set_title("CLIVE — request failed")
        finally:
            try:
                self.request_lock.release()
            except RuntimeError:
                pass

    def _remember_exchange(self, prompt, reply):
        MEMORY.setdefault("history", []).append({"role": "user", "content": prompt})
        MEMORY["history"].append({"role": "assistant", "content": reply})
        MEMORY["history"] = MEMORY["history"][-20:]
        save_memory()

    def _open_image_google_search(self, fallback_query=""):
        query = self.current_image_search_query or fallback_query or ""
        if not query:
            query = "image visual match"
        url = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote_plus(query)
        webbrowser.open(url)

    def _open_google_lens(self):
        webbrowser.open("https://lens.google.com/")
        self._speak("Google Lens is open, sir. Choose the same image there to search for exact and visually similar matches.")

    def show_article(self, topic, article, sources, image_urls=None):
        if self.closing.is_set():
            return
        if self.article_window is not None:
            try:
                if self.article_window.winfo_exists():
                    self.article_window.destroy()
            except tk.TclError:
                pass
        window = tk.Toplevel(self.root)
        self.article_window = window
        self.current_article_plaintext = article.strip()
        self.article_fullscreen = False
        window.title("CLIVE — " + topic)
        window.geometry("900x760")
        window.minsize(700, 560)
        window.configure(bg=BG)
        window.protocol("WM_DELETE_WINDOW", self._close_article)
        window.bind("<Escape>", lambda _event: self._exit_article_fullscreen())
        window.bind("<Command-Return>", lambda _event: self._toggle_article_fullscreen())
        hero = tk.Frame(window, bg=PANEL2, padx=24, pady=18)
        hero.pack(fill="x", padx=18, pady=(18, 12))
        tk.Label(hero, text="C L I V E   /   RESEARCH BRIEF", bg=PANEL2, fg=ACCENT,
                 font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x", pady=(0, 8))
        header = tk.Label(hero, text=topic, bg=PANEL2, fg=TEXT, font=("Georgia", 24, "bold"),
                          anchor="w", justify="left", wraplength=760)
        header.pack(fill="x")
        tk.Label(hero, text="A concise guide, prepared for you, sir.", bg=PANEL2, fg=MUTED,
                 font=("Georgia", 10, "italic"), anchor="w").pack(fill="x", pady=(8, 0))
        tk.Frame(window, bg=ACCENT, height=2).pack(fill="x", padx=22, pady=(0, 10))
        toolbar = tk.Frame(window, bg=BG)
        toolbar.pack(fill="x", padx=22, pady=(0, 10))
        tk.Label(toolbar, text="RESEARCH TOOLS", bg=BG, fg=MUTED,
                 font=("Helvetica Neue", 8, "bold")).pack(side="left", padx=(0, 10))
        tk.Button(toolbar, text="Search Google", command=lambda: self._open_image_google_search(topic),
                  bg=TEXT, fg="#FFFFFF", activebackground="#34445D", activeforeground="#FFFFFF",
                  relief="flat", bd=0, font=("Helvetica Neue", 9, "bold"), padx=12, pady=7,
                  cursor="hand2").pack(side="left", padx=(0, 7))
        tk.Button(toolbar, text="Exact / visual match · Google Lens", command=self._open_google_lens,
                  bg=PANEL2, fg=TEXT, activebackground="#DCD2C1", relief="flat", bd=0,
                  font=("Helvetica Neue", 9, "bold"), padx=12, pady=7,
                  cursor="hand2").pack(side="left")
        image_label = tk.Label(window, text="Finding a relevant image…" if image_urls else "", bg=PANEL2, fg=MUTED,
                               font=("Georgia", 10), compound="top", padx=8, pady=8)
        if image_urls:
            image_label.pack(fill="x", padx=22, pady=(0, 5))
        body = tk.Frame(window, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        content = tk.Text(body, wrap="word", bg=PANEL, fg=TEXT, insertbackground=TEXT,
                          selectbackground="#D8C7A9", relief="flat", bd=0, padx=14, pady=12,
                          font=("Georgia", 12), spacing1=2, spacing3=8)
        scrollbar = tk.Scrollbar(body, command=content.yview, relief="flat", bg=PANEL2)
        content.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        content.pack(side="left", fill="both", expand=True)
        content.configure(state="normal")
        content.insert("1.0", "")

        article_text = article.strip() + "\n\n"
        if sources:
            article_text += "Sources\n"
            for index, source in enumerate(sources, 1):
                article_text += f"{index}. {source.get('title', 'Source')}\n{source.get('href', '')}\n\n"
        article_text, article_styles = format_article_markdown(article_text)
        content.tag_configure("heading1", foreground=ACCENT, font=("Georgia", 16, "bold"), spacing1=12, spacing3=7)
        content.tag_configure("heading2", foreground=ACCENT, font=("Georgia", 13, "bold"), spacing1=9, spacing3=5)
        content.tag_configure("heading3", foreground=TEXT, font=("Georgia", 12, "bold"), spacing1=7, spacing3=4)
        content.tag_configure("bold", font=("Georgia", 12, "bold"))

        # Type the article gradually, like a polished terminal or typewriter.
        # Insert small chunks using Tk's event loop so the window stays responsive.
        typewriter_state = {"position": 0}
        chunk_size = 3
        delay_ms = 8

        def type_next_chunk():
            if self.closing.is_set():
                return
            try:
                if not window.winfo_exists() or not content.winfo_exists():
                    return
                start = typewriter_state["position"]
                if start >= len(article_text):
                    for style_start, style_end, style_name in article_styles:
                        content.tag_add(style_name, f"1.0+{style_start}c", f"1.0+{style_end}c")
                    content.configure(state="disabled")
                    content.see("1.0")
                    return
                end = min(start + chunk_size, len(article_text))
                content.insert("end", article_text[start:end])
                typewriter_state["position"] = end
                content.see("end")
                window.after(delay_ms, type_next_chunk)
            except tk.TclError:
                return

        def load_article_image():
            if not image_urls:
                return
            if not PIL_AVAILABLE:
                def show_install_hint():
                    try:
                        if window.winfo_exists() and image_label.winfo_exists():
                            image_label.configure(text="To display images here, install Pillow: python -m pip install pillow")
                    except tk.TclError:
                        pass
                self.root.after(0, show_install_hint)
                return
            for image_url in image_urls:
                try:
                    request = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0 CLIVE/1.0"})
                    with urllib.request.urlopen(request, timeout=7) as response:
                        data = response.read(5 * 1024 * 1024 + 1)
                    if len(data) > 5 * 1024 * 1024:
                        continue
                    with Image.open(io.BytesIO(data)) as original:
                        full_picture = original.convert("RGB").copy()
                        picture = full_picture.copy()
                        picture.thumbnail((820, 270))
                        photo = ImageTk.PhotoImage(picture)
                    def show_picture(photo=photo, full_picture=full_picture, image_url=image_url):
                        try:
                            if not window.winfo_exists() or not image_label.winfo_exists():
                                return
                            self.current_article_image = full_picture
                            self.current_article_image_url = image_url
                            image_label.configure(image=photo, text="", cursor="hand2", bg=PANEL2)
                            image_label.image = photo
                            image_label.bind("<Button-1>", lambda _event: self._expand_article_image())
                        except tk.TclError:
                            pass
                    self.root.after(0, show_picture)
                    return
                except Exception:
                    continue
            def no_picture():
                try:
                    if window.winfo_exists() and image_label.winfo_exists():
                        image_label.configure(text="No suitable image could be loaded. The article is still available below.")
                except tk.TclError:
                    pass
            self.root.after(0, no_picture)

        if image_urls:
            threading.Thread(target=load_article_image, daemon=True).start()

        # Keep the widget enabled while the typewriter inserts each character.
        # It becomes read-only after type_next_chunk writes the final character.
        window.lift()
        window.focus_force()
        window.after(180, type_next_chunk)

    def close(self):
        if self.closing.is_set():
            return
        self.closing.set()
        self.listening.clear()
        self.notification_watch.clear()
        save_memory()
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def main():
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    app = CliveApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

if __name__ == "__main__":
    main()
