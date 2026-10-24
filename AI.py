"""
LOOB - your own offline AI assistant (powered by Ollama)

Features
  - Streaming answers (text appears word by word)
  - Remembers the whole conversation
  - Saves and loads chats from disk
  - Long-term memory: /remember facts that Loob never forgets
  - Switch AI models any time
  - Change Loob's personality
  - Online videos: /videos <topic> opens YouTube
  - Offline videos: put files in loob_data/videos and /play them
  - Export any chat to a text file

Run:  python loob_massive.py
Needs: Ollama running, and a model pulled (ollama pull llama3.2)
Web search (for current facts): pip install ddgs
Secure key storage (recommended): pip install keyring
"""

import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime

try:
    import keyring  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency at runtime
    keyring = None

# Explicitly track whether the optional keyring dependency is available so static
# analysis does not warn about the import being unused.
KEYRING_AVAILABLE = keyring is not None

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
NAME = "Loob"
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

DATA_DIR = "loob_data"
CHAT_DIR = os.path.join(DATA_DIR, "chats")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

VIDEO_TYPES = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv")

PERSONALITIES = {
    "friendly": (
        "You are Loob, a warm and friendly AI assistant with a casual, natural way of "
        "talking, like a close friend texting. When someone just greets you casually "
        "('hello', 'goodbye', 'bye', 'good morning'), reply the same casual way back in "
        "one short line ('Hello! How are you?', 'Goodbye, take care!') — never define or "
        "explain the word, never lecture, never treat small talk like a question to "
        "answer formally. Save explanations for when someone actually asks something."
    ),
    "teacher": "You are Loob, a patient teacher. Explain step by step with easy examples.",
    "short": "You are Loob. Always answer in as few words as possible.",
    "funny": "You are Loob, a funny AI. Answer correctly but add light humor.",
    "coder": "You are Loob, an expert programmer. Give working code with short explanations.",
}

# ----------------------------------------------------------------------
# Colors (work in most terminals)
# ----------------------------------------------------------------------
if platform.system() == "Windows":
    os.system("")  # enables colors in Windows terminal

C_RESET = "\033[0m"
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_GRAY = "\033[90m"


def info(text):
    print(f"{C_YELLOW}{text}{C_RESET}")


def error(text):
    print(f"{C_RED}{text}{C_RESET}")


# ----------------------------------------------------------------------
# Storage helpers
# ----------------------------------------------------------------------
def setup_folders():
    for folder in (DATA_DIR, CHAT_DIR, VIDEO_DIR):
        os.makedirs(folder, exist_ok=True)
    # Keep this folder private to your own user account (skipped on Windows,
    # which handles folder permissions differently).
    if platform.system() != "Windows":
        try:
            os.chmod(DATA_DIR, 0o700)
        except Exception:
            pass


def get_claude_key():
    """Read the Claude key from the OS keychain, not a plain text file."""
    try:
        import importlib

        keyring = importlib.import_module("keyring")

        return keyring.get_password("loob", "claude_api_key") or ""
    except ImportError:
        return ""


def set_claude_key(key):
    try:
        import importlib

        keyring = importlib.import_module("keyring")

        keyring.set_password("loob", "claude_api_key", key)
        return True
    except ImportError:
        return False


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------
# Loob's brain
# ----------------------------------------------------------------------
class Loob:
    def __init__(self):
        setup_folders()
        settings = load_json(SETTINGS_FILE, {})
        self.model = settings.get("model", DEFAULT_MODEL)
        self.personality = settings.get("personality", "friendly")
        self.memory = load_json(MEMORY_FILE, [])
        self.history = []
        self.web = settings.get("web", True)  # web search on/off
        # Prefer the OS keychain; fall back to the old settings file only to
        # read a key saved before this update (then move it to the keychain).
        self.claude_key = get_claude_key() or settings.get("claude_key", "")
        if self.claude_key and set_claude_key(self.claude_key):
            settings.pop("claude_key", None)

    # ---------- web search ----------
    def web_search(self, query):
        """Look the question up on the internet. Tries DuckDuckGo, then Wikipedia."""
        results = ""
        try:
            from ddgs import DDGS

            found = DDGS().text(query, max_results=5)
            results = "\n".join(f"- {r['title']}: {r['body']}" for r in found)
        except ImportError:
            error("Web search needs one install. Run:  pip install ddgs")
        except Exception as problem:
            error(f"DuckDuckGo search problem: {problem}")

        if not results:
            results = self.wiki_search(query)

        if results:
            info("Found fresh results from the internet.")
        else:
            error("Could not get any internet results (check your internet).")
        return results

    def wiki_search(self, query):
        """Backup search that needs no install."""
        try:
            import re

            url = (
                "https://en.wikipedia.org/w/api.php?action=query&list=search"
                "&format=json&srlimit=4&srsearch=" + urllib.parse.quote(query)
            )
            request = urllib.request.Request(url, headers={"User-Agent": "Loob/1.0"})
            with urllib.request.urlopen(request, timeout=8) as reply:
                items = json.loads(reply.read())["query"]["search"]
            return "\n".join(
                f"- {i['title']}: {re.sub('<[^>]+>', '', i['snippet'])}" for i in items
            )
        except Exception:
            return ""

    # ---------- settings ----------
    def save_settings(self):
        # The Claude key is never written to this file; it lives in the OS keychain.
        save_json(
            SETTINGS_FILE,
            {"model": self.model, "personality": self.personality, "web": self.web},
        )

    def system_prompt(self):
        text = PERSONALITIES.get(self.personality, PERSONALITIES["friendly"])
        text += (
            " You are Loob, an AI assistant created and founded by Rajdip Karmakar."
            " If anyone asks who made you, who created you, or who your founder is,"
            " answer: Rajdip Karmakar. Never say you were made by Meta or any other company."
            " If asked what technology you run on, say you run on an open-source language model."
        )
        text += (
            " Think step by step before answering. For maths, show the working and"
            " double-check the final answer. For code, write complete working code,"
            " explain bugs clearly, and give the fixed version. Reply in the same"
            " language the user writes in. Be honest when you are not sure."
        )
        text += f" Today is {datetime.now().strftime('%A, %d %B %Y')}."
        if self.memory:
            text += " Things you know about the user: " + "; ".join(self.memory) + "."
        return text

    # ---------- talking to Ollama ----------
    def ask(self, question):
        """Send a question to Ollama and stream the answer."""
        self.history.append({"role": "user", "content": question})

        # Look up fresh facts on the web (prime minister, news, prices, ...)
        last_message = question
        if self.web:
            print(f"{C_GRAY}Searching the web...{C_RESET}")
            found = self.web_search(question)
            if found:
                last_message = (
                    f"Web search results (fresh, from the internet):\n{found}\n\n"
                    f"These results are newer than your training. Trust them over "
                    f"your memory and answer directly.\n"
                    f"Question: {question}"
                )

        chat_messages = self.history[:-1] + [{"role": "user", "content": last_message}]

        if self.model.startswith("claude"):
            self.ask_claude(chat_messages)
            return

        payload = {
            "model": self.model,
            "stream": True,
            "messages": [{"role": "system", "content": self.system_prompt()}] + chat_messages,
        }
        request = urllib.request.Request(
            OLLAMA_URL + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        answer = ""
        try:
            print(f"{C_GREEN}{NAME}:{C_RESET} ", end="", flush=True)
            with urllib.request.urlopen(request, timeout=300) as reply:
                for line in reply:
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    piece = chunk.get("message", {}).get("content", "")
                    answer += piece
                    print(piece, end="", flush=True)
                    if chunk.get("done"):
                        break
            print("\n")
        except urllib.error.HTTPError as problem:
            self.history.pop()
            if problem.code == 404:
                error(f"\nModel '{self.model}' not found. Run: ollama pull {self.model}")
            else:
                error(f"\nOllama error: {problem}")
            return
        except urllib.error.URLError:
            self.history.pop()
            error("\nCan't reach Ollama. Make sure it is running (open the Ollama app).")
            return
        except KeyboardInterrupt:
            print(f"\n{C_GRAY}(stopped){C_RESET}\n")

        if answer:
            self.history.append({"role": "assistant", "content": answer})
        else:
            self.history.pop()

    def ask_claude(self, chat_messages):
        """Use the real Claude model (needs internet and an API key)."""
        key = os.environ.get("ANTHROPIC_API_KEY") or self.claude_key
        if not key:
            self.history.pop()
            error("No Claude key yet. Get one at console.anthropic.com, then type: /key <your key>")
            return

        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "system": self.system_prompt(),
            "messages": chat_messages,
        }
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            print(f"{C_GRAY}Thinking...{C_RESET}")
            with urllib.request.urlopen(request, timeout=300) as reply:
                data = json.loads(reply.read())
            answer = "".join(block.get("text", "") for block in data.get("content", []))
        except urllib.error.HTTPError as problem:
            self.history.pop()
            detail = problem.read().decode("utf-8", "ignore")[:300]
            error(f"Claude error {problem.code}: {detail}")
            return
        except Exception as problem:
            self.history.pop()
            error(f"Could not reach Claude: {problem}")
            return

        print(f"{C_GREEN}{NAME}:{C_RESET} {answer}\n")
        self.history.append({"role": "assistant", "content": answer})

    def list_models(self):
        try:
            with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=5) as reply:
                data = json.loads(reply.read())
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            return None

    # ---------- chats ----------
    def save_chat(self, name=None):
        if not self.history:
            info("Nothing to save yet.")
            return
        name = name or datetime.now().strftime("chat_%Y%m%d_%H%M%S")
        path = os.path.join(CHAT_DIR, name + ".json")
        save_json(path, self.history)
        info(f"Chat saved as '{name}'.")

    def load_chat(self, name):
        path = os.path.join(CHAT_DIR, name + ".json")
        data = load_json(path, None)
        if data is None:
            error(f"No saved chat called '{name}'. Use /chats to see the list.")
            return
        self.history = data
        info(f"Loaded '{name}' ({len(data)} messages).")

    def list_chats(self):
        files = sorted(f[:-5] for f in os.listdir(CHAT_DIR) if f.endswith(".json"))
        if not files:
            info("No saved chats yet. Use /save to save one.")
        for name in files:
            print("  -", name)

    def export_chat(self):
        if not self.history:
            info("Nothing to export yet.")
            return
        name = datetime.now().strftime("export_%Y%m%d_%H%M%S.txt")
        path = os.path.join(DATA_DIR, name)
        with open(path, "w", encoding="utf-8") as file:
            for message in self.history:
                who = "You" if message["role"] == "user" else NAME
                file.write(f"{who}: {message['content']}\n\n")
        info(f"Exported to {path}")

    # ---------- memory ----------
    def remember(self, fact):
        self.memory.append(fact)
        save_json(MEMORY_FILE, self.memory)
        info("Got it, I will remember that.")

    def show_memory(self):
        if not self.memory:
            info("I don't remember anything yet. Use /remember <fact>.")
        for number, fact in enumerate(self.memory, 1):
            print(f"  {number}. {fact}")

    def forget(self, number):
        try:
            removed = self.memory.pop(int(number) - 1)
            save_json(MEMORY_FILE, self.memory)
            info(f"Forgot: {removed}")
        except (ValueError, IndexError):
            error("Use /forget <number>. See numbers with /memory.")

    # ---------- videos ----------
    def search_videos(self, topic):
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(topic)
        info(f"Opening YouTube for '{topic}' ...")
        webbrowser.open(url)

    def local_videos(self):
        return sorted(f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(VIDEO_TYPES))

    def list_local_videos(self):
        videos = self.local_videos()
        if not videos:
            info(f"No offline videos yet. Copy video files into: {VIDEO_DIR}")
        for number, name in enumerate(videos, 1):
            print(f"  {number}. {name}")

    def play_video(self, choice):
        videos = self.local_videos()
        match = None
        if choice.isdigit() and 1 <= int(choice) <= len(videos):
            match = videos[int(choice) - 1]
        else:
            for name in videos:
                if choice.lower() in name.lower():
                    match = name
                    break
        if not match:
            error("Video not found. Use /local to see your videos.")
            return
        path = os.path.abspath(os.path.join(VIDEO_DIR, match))
        info(f"Playing {match} ...")
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------
HELP = f"""
{C_YELLOW}Commands{C_RESET}
  /help               show this list
  /new                start a fresh chat
  /save [name]        save this chat
  /load <name>        load a saved chat
  /chats              list saved chats
  /export             export this chat to a text file
  /models             list your Ollama models
  /model <name>       switch model
  /personality <type> friendly, teacher, short, funny, coder
  /remember <fact>    Loob remembers this forever
  /memory             show what Loob remembers
  /forget <number>    forget one memory
  /mode <type>        general, code or math (picks a smarter model)
  /claude             use the real Claude model (most powerful)
  /key <key>          save your Claude API key
  /web on|off       turn internet search for answers on or off
  /videos <topic>     search YouTube (needs internet)
  /local              list your offline videos
  /play <number/name> play an offline video
  /quit               exit

Anything else you type is a question for {NAME}.
"""


def handle_command(loob, text):
    """Returns False if the program should quit."""
    parts = text.split(maxsplit=1)
    command = parts[0].lower()
    argument = parts[1].strip() if len(parts) > 1 else ""

    if command in ("/quit", "/exit", "/q"):
        return False
    elif command == "/help":
        print(HELP)
    elif command == "/new":
        loob.history = []
        info("Fresh chat started.")
    elif command == "/save":
        loob.save_chat(argument or None)
    elif command == "/load":
        loob.load_chat(argument) if argument else error("Use /load <name>")
    elif command == "/chats":
        loob.list_chats()
    elif command == "/export":
        loob.export_chat()
    elif command == "/models":
        models = loob.list_models()
        if models is None:
            error("Can't reach Ollama.")
        else:
            for name in models:
                mark = " (current)" if name.split(":")[0] == loob.model.split(":")[0] else ""
                print(f"  - {name}{mark}")
    elif command == "/model":
        if argument:
            loob.model = argument
            loob.save_settings()
            info(f"Now using model: {loob.model}")
        else:
            info(f"Current model: {loob.model}")
    elif command == "/personality":
        if argument in PERSONALITIES:
            loob.personality = argument
            loob.save_settings()
            info(f"Personality changed to: {argument}")
        else:
            info("Choose one of: " + ", ".join(PERSONALITIES))
    elif command == "/remember":
        loob.remember(argument) if argument else error("Use /remember <fact>")
    elif command == "/memory":
        loob.show_memory()
    elif command == "/forget":
        loob.forget(argument)
    elif command == "/mode":
        modes = {
            "general": "llama3.1:8b",
            "code": "qwen2.5-coder:7b",
            "math": "deepseek-r1:8b",
        }
        if argument in modes:
            loob.model = modes[argument]
            loob.save_settings()
            info(f"Mode '{argument}' uses model {loob.model}.")
            info(f"If it says model not found, run in terminal: ollama pull {loob.model}")
        else:
            info("Use /mode general, /mode code or /mode math")
    elif command == "/key":
        if argument:
            loob.claude_key = argument
            if set_claude_key(argument):
                info("Key saved securely in your OS keychain. Now type /claude.")
            else:
                error("Install 'keyring' for secure storage first: pip install keyring")
        else:
            error("Use /key <your key from console.anthropic.com>")
    elif command == "/claude":
        loob.model = "claude-sonnet-5-5"
        loob.save_settings()
        info("Now using Claude. It needs internet and a key (/key <your key>).")
    elif command == "/web":
        if argument in ("on", "off"):
            loob.web = argument == "on"
            loob.save_settings()
            info(f"Web search is now {argument}.")
        else:
            info(f"Web search is {'on' if loob.web else 'off'}. Use /web on or /web off.")
    elif command == "/videos":
        loob.search_videos(argument) if argument else error("Use /videos <topic>")
    elif command == "/local":
        loob.list_local_videos()
    elif command == "/play":
        loob.play_video(argument) if argument else error("Use /play <number or name>")
    else:
        error("Unknown command. Type /help to see all commands.")
    return True


# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------
def main():
    loob = Loob()

    print(f"{C_BLUE}=========================================={C_RESET}")
    print(f"{C_BLUE}   {NAME}  -  your own offline AI assistant{C_RESET}")
    print(f"{C_BLUE}=========================================={C_RESET}")
    print(f"Model: {loob.model}   Personality: {loob.personality}")
    print("Ask anything, or type /help for commands.\n")

    if loob.list_models() is None:
        error("Heads up: Ollama is not running. Open the Ollama app, then ask me something.\n")

    while True:
        try:
            text = input(f"{C_BLUE}You:{C_RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text.startswith("/"):
            if not handle_command(loob, text):
                break
        else:
            loob.ask(text)

    print(f"{NAME}: Goodbye!")


if __name__ == "__main__":
    main()