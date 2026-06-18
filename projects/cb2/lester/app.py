#!/usr/bin/env python3
"""
Lester v5 - Modular Refactor + Piper TTS + Natural Interaction
Stan (AWS) architects. Lester (Groq/LLaMA) executes. $0 cost.
"""

import os, json, subprocess, time, uuid, sqlite3, re, threading, urllib.request, urllib.parse
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from groq import Groq
from langsmith import traceable

from tts_engine import speak
from conversation import convo
from prompts import LESTER_V5_SYSTEM, CHAIN_PLANNING_PROMPT

# === CONFIG ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "llama-3.1-8b-instant"
STAN_DIR = os.path.expanduser("~/.stan")
SANDBOX_DIR = os.path.join(STAN_DIR, "sandboxes")
DB_PATH = os.path.join(STAN_DIR, "memory.db")
MAX_CHAIN_STEPS = 5
NL = chr(10)

os.makedirs(SANDBOX_DIR, exist_ok=True)
os.makedirs(os.path.join(STAN_DIR, "downloads"), exist_ok=True)
os.makedirs(os.path.join(STAN_DIR, "tax"), exist_ok=True)
os.makedirs("static", exist_ok=True)

if not GROQ_API_KEY:
    print("Set GROQ_API_KEY: https://console.groq.com/keys"); exit(1)

groq_client = Groq(api_key=GROQ_API_KEY)

# === DATABASE ===
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.executescript("""
    CREATE TABLE IF NOT EXISTS instructions (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT UNIQUE, type TEXT, category TEXT, weight REAL DEFAULT 1.0, times_reinforced INTEGER DEFAULT 0, created TEXT, active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS saved_data (id INTEGER PRIMARY KEY AUTOINCREMENT, data_type TEXT, content TEXT, tags TEXT, priority INTEGER DEFAULT 2, created TEXT, active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS portfolio (symbol TEXT PRIMARY KEY, shares REAL, avg_cost REAL);
    CREATE TABLE IF NOT EXISTS expenses (id TEXT PRIMARY KEY, date TEXT, amount REAL, category TEXT, description TEXT, deductible INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS income_sources (id TEXT PRIMARY KEY, source TEXT, type TEXT, amount REAL, year INTEGER);
    CREATE TABLE IF NOT EXISTS traces (id TEXT PRIMARY KEY, timestamp TEXT, input TEXT, output TEXT, tools_called TEXT, latency_ms INTEGER);
""")
db.commit()

# === ACK SOUND ===
ACK_SOUND = "static/ack.wav"

def play_ack():
    if os.path.exists(ACK_SOUND):
        subprocess.Popen(['aplay', '-q', ACK_SOUND])


# === TOOL FUNCTIONS ===
@traceable(name="lester:open_app")
def tool_open_app(target):
    apps = {"chrome":"google-chrome","firefox":"firefox","files":"nautilus","terminal":"x-terminal-emulator","spotify":"spotify"}
    cmd = apps.get(target.lower(), target)
    if target.startswith("http"):
        cmd = target
    subprocess.Popen(f"xdg-open {cmd}", shell=True)
    return f"Opening {target}"

@traceable(name="lester:shell")
def tool_shell(command):
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() or r.stderr.strip() or "Done."
    except subprocess.TimeoutExpired:
        return "Timed out."
    except Exception as e:
        return f"Error: {e}"

@traceable(name="lester:focus_window")
def tool_focus_window(window_name):
    try:
        r = subprocess.run(["xdotool","search","--name",window_name], capture_output=True, text=True, timeout=5)
        wid = r.stdout.strip().split(NL)[0]
        if wid:
            subprocess.run(["xdotool","windowactivate",wid], timeout=5)
            return f"Focused: {window_name}"
    except:
        pass
    return f"Window '{window_name}' not found."

@traceable(name="lester:type_text")
def tool_type_text(text):
    subprocess.run(["xdotool","type","--delay","20",text], timeout=30)
    return "Typed."

@traceable(name="lester:copy")
def tool_copy():
    subprocess.run(["xdotool","key","ctrl+c"], timeout=5)
    return "Copied."

@traceable(name="lester:paste")
def tool_paste():
    subprocess.run(["xdotool","key","ctrl+v"], timeout=5)
    return "Pasted."

@traceable(name="lester:clipboard_get")
def tool_clipboard_get():
    try:
        r = subprocess.run(["xclip","-selection","clipboard","-o"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip()[:500] or "(empty)"
    except:
        return "(unavailable)"

@traceable(name="lester:sandbox_create")
def tool_sandbox_create(name="default"):
    sid = str(uuid.uuid4())[:8]
    os.makedirs(os.path.join(SANDBOX_DIR, sid), exist_ok=True)
    return f"Sandbox {sid} ready."

@traceable(name="lester:sandbox_exec")
def tool_sandbox_exec(command, sandbox_id=""):
    if not sandbox_id:
        sbs = sorted(os.listdir(SANDBOX_DIR))
        sandbox_id = sbs[-1] if sbs else ""
    path = os.path.join(SANDBOX_DIR, sandbox_id)
    if not os.path.isdir(path):
        path = SANDBOX_DIR
    try:
        r = subprocess.run(["sh","-c",command], capture_output=True, text=True, timeout=30, cwd=path)
        return r.stdout.strip() or r.stderr.strip() or "Done."
    except Exception as e:
        return f"Error: {e}"

@traceable(name="lester:web_search")
def tool_web_search(query):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)', html)
        results = []
        for l, t in links[:5]:
            u = urllib.parse.unquote(l.split("uddg=")[1].split("&")[0]) if "uddg=" in l else l
            results.append(f"{t.strip()} - {u}")
        return NL.join(results) if results else "No results."
    except Exception as e:
        return f"Search error: {e}"

@traceable(name="lester:web_fetch")
def tool_web_fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()[:3000]
    except:
        return "Couldn't fetch."

@traceable(name="lester:calculate_tax")
def tool_calculate_tax(income, filing="single", state="CA", deductions=0):
    income = float(income); deductions = float(deductions)
    brackets = [(11600,0.10),(47150,0.12),(100525,0.22),(191950,0.24),(243725,0.32),(609350,0.35),(float("inf"),0.37)]
    std_ded = {"single":14600,"married":29200,"head_of_household":21900}
    state_rates = {"CA":0.133,"NY":0.109,"TX":0.0,"FL":0.0,"WA":0.0,"IL":0.0495,"OR":0.099,"NV":0.0,"PA":0.0307}
    std = std_ded.get(filing, 14600); ded = max(std, deductions); taxable = max(0, income - ded)
    tax = 0; prev = 0; rem = taxable
    for limit, rate in brackets:
        if rem <= 0: break
        chunk = min(rem, limit-prev); tax += chunk*rate; rem -= chunk; prev = limit
    st_rate = state_rates.get(state.upper(), 0.05); state_tax = taxable * st_rate
    ss = min(income, 168600)*0.062; med = income*0.0145
    if income > 200000: med += (income-200000)*0.009
    fica = ss+med; total = tax+state_tax+fica; take_home = income-total
    return f"Tax ({filing}, {state.upper()}): Gross ${income:,.0f} | Taxable ${taxable:,.0f} | Fed ${tax:,.0f} | State ${state_tax:,.0f} | FICA ${fica:,.0f} | TOTAL ${total:,.0f} ({total/income*100:.1f}%) | Take-home ${take_home:,.0f}/yr (${take_home/12:,.0f}/mo)"

@traceable(name="lester:quarterly_tax")
def tool_quarterly_tax(income, filing="single", state="CA"):
    income = float(income)
    brackets = [(11600,0.10),(47150,0.12),(100525,0.22),(191950,0.24),(243725,0.32),(609350,0.35),(float("inf"),0.37)]
    std = {"single":14600,"married":29200,"head_of_household":21900}.get(filing, 14600)
    state_rates = {"CA":0.133,"NY":0.109,"TX":0.0,"FL":0.0,"WA":0.0}
    taxable = max(0, income-std); tax = 0; prev = 0; rem = taxable
    for limit, rate in brackets:
        if rem <= 0: break
        chunk = min(rem, limit-prev); tax += chunk*rate; rem -= chunk; prev = limit
    state_tax = taxable * state_rates.get(state.upper(), 0.05)
    fica = min(income,168600)*0.062 + income*0.0145
    q = (tax + state_tax + fica) / 4
    return f"Quarterly: ${q:,.0f} each | Q1 Apr 15 | Q2 Jun 16 | Q3 Sep 15 | Q4 Jan 15 | Annual: ${q*4:,.0f}"

@traceable(name="lester:add_expense")
def tool_add_expense(amount, category, description="", deductible=False):
    eid = str(uuid.uuid4())[:8]
    db.execute("INSERT INTO expenses VALUES (?,?,?,?,?,?)", (eid, datetime.now().strftime("%Y-%m-%d"), float(amount), category, description, int(deductible)))
    db.commit()
    return f"Logged: ${float(amount):.2f} ({category}){' deductible' if deductible else ''}"

@traceable(name="lester:expenses_summary")
def tool_expenses_summary(year=0):
    year = int(year) or datetime.now().year
    rows = db.execute("SELECT category, SUM(amount), COUNT(*) FROM expenses WHERE date LIKE ? GROUP BY category", (f"{year}%",)).fetchall()
    if not rows: return f"No expenses for {year}."
    total = sum(r[1] for r in rows)
    lines = [f"  {c}: ${a:,.0f} ({n})" for c,a,n in sorted(rows, key=lambda x:-x[1])]
    return f"Expenses {year}:" + NL + NL.join(lines) + NL + f"  Total: ${total:,.0f}"

@traceable(name="lester:add_income")
def tool_add_income(source, amount, income_type="W-2"):
    iid = str(uuid.uuid4())[:8]
    db.execute("INSERT INTO income_sources VALUES (?,?,?,?,?)", (iid, source, income_type, float(amount), datetime.now().year))
    db.commit()
    return f"Added: ${float(amount):,.0f} from {source} ({income_type})"

@traceable(name="lester:tax_deadlines")
def tool_tax_deadlines():
    now = datetime.now()
    dls = [("2026-04-15","2025 return"),("2026-06-16","Q2 estimated"),("2026-09-15","Q3 estimated"),("2026-10-15","Extended return"),("2027-01-15","Q4 estimated")]
    lines = []
    for ds, desc in dls:
        d = datetime.strptime(ds, "%Y-%m-%d")
        if d >= now:
            days = (d-now).days
            lines.append(f"  {ds}: {desc} ({days}d)")
    return "Deadlines:" + NL + NL.join(lines[:5])

@traceable(name="lester:stock_price")
def tool_stock_price(symbol):
    symbol = symbol.upper()
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice",0); prev = meta.get("previousClose",price)
        chg = price-prev; pct = (chg/prev*100) if prev else 0
        arrow = "UP" if chg>=0 else "DOWN"
        return f"{arrow} {symbol}: ${price:.2f} ({pct:+.1f}%)"
    except:
        return f"Can't find {symbol}"

@traceable(name="lester:market_summary")
def tool_market_summary():
    indices = [("^GSPC","S&P"),("^DJI","Dow"),("^IXIC","NASDAQ")]
    lines = []
    for sym, name in indices:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice",0); prev = meta.get("previousClose",price)
            pct = ((price-prev)/prev*100) if prev else 0
            lines.append(f"{name}: {price:,.0f} ({pct:+.1f}%)")
        except:
            pass
    return ("Markets:" + NL + NL.join(lines)) if lines else "Markets unavailable."

@traceable(name="lester:portfolio_add")
def tool_portfolio_add(symbol, shares, cost_per_share=0):
    symbol = symbol.upper(); shares = float(shares); cost_per_share = float(cost_per_share)
    if cost_per_share <= 0:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            cost_per_share = data["chart"]["result"][0]["meta"].get("regularMarketPrice", 0)
        except:
            pass
    db.execute("INSERT OR REPLACE INTO portfolio VALUES (?,?,?)", (symbol, shares, cost_per_share)); db.commit()
    return f"Added {shares} {symbol} @ ${cost_per_share:.2f}"

@traceable(name="lester:portfolio_summary")
def tool_portfolio_summary():
    rows = db.execute("SELECT symbol, shares, avg_cost FROM portfolio").fetchall()
    if not rows: return "Portfolio empty."
    total = 0; lines = []
    for sym, shares, avg in rows:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            price = data["chart"]["result"][0]["meta"].get("regularMarketPrice", avg)
            val = shares*price; pnl = val-(shares*avg); pct = (pnl/(shares*avg)*100) if avg else 0
            total += val; lines.append(f"{sym}: {shares:.0f}x${price:.2f}=${val:,.0f} ({pct:+.1f}%)")
        except:
            lines.append(f"{sym}: {shares:.0f} shares")
    return f"Portfolio ${total:,.0f}:" + NL + NL.join(lines)

@traceable(name="lester:save_memory")
def tool_save_memory(content, data_type="personal", **kwargs):
    db.execute("INSERT INTO saved_data (data_type,content,tags,priority,created,active) VALUES (?,?,?,2,?,1)",
        (data_type, content, json.dumps([data_type]), datetime.now().isoformat()))
    db.commit()
    return f"Saved: {content[:80]}"

@traceable(name="lester:recall_memory")
def tool_recall_memory(query):
    rows = db.execute("SELECT data_type, content FROM saved_data WHERE active=1 AND content LIKE ? ORDER BY priority DESC LIMIT 5", (f"%{query}%",)).fetchall()
    if not rows: return f"Nothing matching '{query}'."
    return "Recalled:" + NL + NL.join(f"  [{d}] {c[:80]}" for d,c in rows)

@traceable(name="lester:list_memories")
def tool_list_memories():
    rows = db.execute("SELECT data_type, content, created FROM saved_data WHERE active=1 ORDER BY created DESC LIMIT 20").fetchall()
    if not rows: return "Nothing saved."
    return f"Saved ({len(rows)}):" + NL + NL.join(f"  [{d}] {c[:60]}" for d,c,_ in rows)

@traceable(name="lester:delete_memory")
def tool_delete_memory(keyword):
    rows = db.execute("SELECT id FROM saved_data WHERE active=1 AND content LIKE ?", (f"%{keyword}%",)).fetchall()
    if not rows: return f"Nothing matching '{keyword}'."
    for r in rows: db.execute("UPDATE saved_data SET active=0 WHERE id=?", (r[0],))
    db.commit()
    return f"Deleted {len(rows)} item(s)."

@traceable(name="lester:notify")
def tool_notify(title, message):
    try: subprocess.run(["notify-send","--app-name=Lester",title,message], timeout=5)
    except: pass
    topic = os.environ.get("STAN_NTFY_TOPIC", "stan-brian-alerts")
    try: urllib.request.urlopen(urllib.request.Request(f"https://ntfy.sh/{topic}", data=message.encode(), headers={"Title":title}), timeout=10)
    except: pass
    return f"Notified: {title}"

@traceable(name="lester:set_timer")
def tool_set_timer(seconds, label="Timer"):
    seconds = int(seconds)
    def _t():
        time.sleep(seconds); tool_notify(label, f"{seconds}s done!")
    threading.Thread(target=_t, daemon=True).start()
    return f"Timer: {label} ({seconds}s)"

@traceable(name="lester:media_control")
def tool_media_control(command, volume=50):
    if command == "volume":
        subprocess.Popen(f"pactl set-sink-volume @DEFAULT_SINK@ {int(volume)}%", shell=True)
        return f"Volume -> {volume}%"
    cmds = {"play":"playerctl play","pause":"playerctl pause","next":"playerctl next","prev":"playerctl previous","toggle":"playerctl play-pause"}
    if command in cmds: subprocess.Popen(cmds[command], shell=True)
    return f"Media: {command}"

@traceable(name="lester:screenshot")
def tool_screenshot():
    path = os.path.join(STAN_DIR, f"ss_{int(time.time())}.png")
    try: subprocess.run(["gnome-screenshot","-f",path], timeout=10); return f"Saved: {path}"
    except: return "Screenshot failed."

@traceable(name="lester:system_info")
def tool_system_info():
    try:
        cpu = subprocess.run("top -bn1 | grep Cpu | awk '{print $2}'", shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
        mem = subprocess.run("free -h | awk '/Mem:/{print $3\\\"/\\\"$2}'", shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
        disk = subprocess.run("df -h / | awk 'NR==2{print $3\\\"/\\\"$2}'", shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
        return f"CPU: {cpu}% | RAM: {mem} | Disk: {disk}"
    except:
        return "Unavailable."

@traceable(name="lester:list_instructions")
def tool_list_instructions():
    rows = db.execute("SELECT text, type, category, weight FROM instructions WHERE active=1 ORDER BY weight DESC").fetchall()
    if not rows: return "No instructions. Tell me your preferences."
    return f"Instructions ({len(rows)}):" + NL + NL.join(f"  [{c}] {t}" for t,tp,c,w in rows)

@traceable(name="lester:forget_instruction")
def tool_forget_instruction(keyword):
    if keyword == "last":
        row = db.execute("SELECT id,text FROM instructions WHERE active=1 ORDER BY id DESC LIMIT 1").fetchone()
        if not row: return "Nothing to forget."
        db.execute("UPDATE instructions SET active=0 WHERE id=?", (row[0],)); db.commit()
        return f"Forgot: '{row[1]}'"
    rows = db.execute("SELECT id FROM instructions WHERE active=1 AND text LIKE ?", (f"%{keyword}%",)).fetchall()
    if not rows: return f"Nothing matching '{keyword}'."
    for r in rows: db.execute("UPDATE instructions SET active=0 WHERE id=?", (r[0],))
    db.commit()
    return f"Forgot {len(rows)} instruction(s)."


# === TOOL REGISTRY ===
TOOL_FUNCTIONS = {
    "speak": speak, "open_app": tool_open_app, "shell": tool_shell,
    "focus_window": tool_focus_window, "type_text": tool_type_text,
    "copy": tool_copy, "paste": tool_paste, "clipboard_get": tool_clipboard_get,
    "sandbox_create": tool_sandbox_create, "sandbox_exec": tool_sandbox_exec,
    "web_search": tool_web_search, "web_fetch": tool_web_fetch,
    "calculate_tax": tool_calculate_tax, "quarterly_tax": tool_quarterly_tax,
    "add_expense": tool_add_expense, "expenses_summary": tool_expenses_summary,
    "add_income": tool_add_income, "tax_deadlines": tool_tax_deadlines,
    "stock_price": tool_stock_price, "market_summary": tool_market_summary,
    "portfolio_add": tool_portfolio_add, "portfolio_summary": tool_portfolio_summary,
    "save_memory": tool_save_memory, "recall_memory": tool_recall_memory,
    "list_memories": tool_list_memories, "delete_memory": tool_delete_memory,
    "notify": tool_notify, "set_timer": tool_set_timer,
    "media_control": tool_media_control, "screenshot": tool_screenshot,
    "system_info": tool_system_info, "list_instructions": tool_list_instructions,
    "forget_instruction": tool_forget_instruction,
}

# === TOOLS DESCRIPTION FOR LLM ===
TOOLS_DESC = ('AVAILABLE ACTIONS (respond with exactly ONE JSON object):\n'
    '{"action":"speak","text":"..."} - respond to Brian\n'
    '{"action":"open_app","target":"..."} - open app/URL\n'
    '{"action":"shell","command":"..."} - run shell command\n'
    '{"action":"focus_window","window_name":"..."} - bring window to front\n'
    '{"action":"type_text","text":"..."} - type into focused window\n'
    '{"action":"copy"} - copy selection\n'
    '{"action":"paste"} - paste clipboard\n'
    '{"action":"clipboard_get"} - read clipboard\n'
    '{"action":"sandbox_create","name":"..."} - create sandbox\n'
    '{"action":"sandbox_exec","command":"..."} - run in sandbox\n'
    '{"action":"web_search","query":"..."} - search internet\n'
    '{"action":"web_fetch","url":"..."} - read webpage\n'
    '{"action":"calculate_tax","income":N,"filing":"single","state":"CA"} - calc taxes\n'
    '{"action":"quarterly_tax","income":N} - quarterly estimates\n'
    '{"action":"add_expense","amount":N,"category":"...","description":"...","deductible":false} - log expense\n'
    '{"action":"expenses_summary","year":2026} - show expenses\n'
    '{"action":"add_income","source":"...","amount":N,"income_type":"W-2"} - record income\n'
    '{"action":"tax_deadlines"} - show deadlines\n'
    '{"action":"stock_price","symbol":"..."} - get stock price\n'
    '{"action":"market_summary"} - S&P, Dow, NASDAQ\n'
    '{"action":"portfolio_add","symbol":"...","shares":N,"cost_per_share":N} - add to portfolio\n'
    '{"action":"portfolio_summary"} - show portfolio\n'
    '{"action":"save_memory","content":"...","data_type":"personal"} - save for later\n'
    '{"action":"recall_memory","query":"..."} - search saved data\n'
    '{"action":"list_memories"} - show all saved\n'
    '{"action":"delete_memory","keyword":"..."} - delete saved data\n'
    '{"action":"notify","title":"...","message":"..."} - push notification\n'
    '{"action":"set_timer","seconds":N,"label":"..."} - countdown timer\n'
    '{"action":"media_control","command":"play/pause/next/volume","volume":50} - control music\n'
    '{"action":"screenshot"} - take screenshot\n'
    '{"action":"system_info"} - CPU/RAM/disk\n'
    '{"action":"list_instructions"} - show preferences\n'
    '{"action":"forget_instruction","keyword":"..."} - delete preference')

CHAIN_DESC = ('\n\nMULTI-STEP CHAINS:\n'
    'For complex requests requiring multiple actions, respond with:\n'
    '{"chain": [{"action":"...", ...}, {"action":"...", ...}, {"action":"speak","text":"..."}]}\n'
    '\n'
    'CHAIN RULES:\n'
    '- Use {result} in any field to reference the output of the previous step\n'
    '- Maximum 5 steps per chain\n'
    '- Always end chains with a speak action to report results\n'
    '- Use chains when Brian asks to: search AND save, check AND notify, fetch AND summarize, or any multi-part task\n'
    '- For simple requests, still use a single action (no chain needed)\n'
    '\n'
    'CHAIN EXAMPLES:\n'
    '"Research X and save it" -> {"chain":[{"action":"web_search","query":"X"},{"action":"save_memory","content":"{result}","data_type":"research"},{"action":"speak","text":"Found info on X and saved it."}]}\n'
    '"Check NVDA and alert me if down" -> {"chain":[{"action":"stock_price","symbol":"NVDA"},{"action":"speak","text":"{result}"}]}\n')


# === INSTRUCTION DETECTION ===
INST_PATTERNS = {
    "rule": [r"\b(always|never|don't|do not|must|from now on)\b"],
    "preference": [r"\b(i prefer|i like|i want|use .+ for|default to)\b"],
    "fact": [r"\b(my name is|i am|i live|i work|i use|i have|my .+ is)\b"],
    "workflow": [r"\b(when i say|if i ask|before you|after you)\b"],
}

def detect_instruction(text):
    if len(text) < 10 or text.strip().endswith("?"):
        return
    text_lower = text.lower()
    detected_type = None
    for t, patterns in INST_PATTERNS.items():
        if any(re.search(p, text_lower) for p in patterns):
            detected_type = t
            break
    if not detected_type:
        return
    weight = {"rule":2.0,"fact":1.5,"preference":1.5,"workflow":2.0}.get(detected_type, 1.0)
    try:
        db.execute("INSERT INTO instructions (text,type,category,weight,created) VALUES (?,?,?,?,?)",
            (text.strip(), detected_type, "general", weight, datetime.now().isoformat()))
        db.commit()
    except sqlite3.IntegrityError:
        pass

def get_instructions_context():
    rows = db.execute("SELECT text FROM instructions WHERE active=1 ORDER BY weight DESC LIMIT 10").fetchall()
    if not rows:
        return ""
    return "\nBRIAN'S RULES:\n" + "\n".join(f"- {r[0]}" for r in rows)


# === CHAIN EXECUTION ===
@traceable(name="lester:execute_chain")
def execute_chain(chain_steps):
    """Execute a multi-step chain, passing {result} between steps."""
    results = []
    prev_result = ""
    for i, step in enumerate(chain_steps[:MAX_CHAIN_STEPS]):
        action_name = step.get("action", "speak")
        args = {}
        for k, v in step.items():
            if k == "action":
                continue
            if isinstance(v, str) and "{result}" in v:
                v = v.replace("{result}", prev_result[:500])
            args[k] = v
        if action_name in TOOL_FUNCTIONS:
            try:
                result = TOOL_FUNCTIONS[action_name](**args)
            except Exception as e:
                result = f"Step {i+1} error: {e}"
        else:
            result = args.get("text", "Done.")
        prev_result = result if isinstance(result, str) else str(result)
        results.append({"step": i+1, "action": action_name, "result": prev_result[:200]})
        print(f"  CHAIN[{i+1}/{len(chain_steps)}]: {action_name} -> {prev_result[:60]}")
    return results


# === MAIN BRAIN ===
@traceable(name="lester:process_input", run_type="chain")
def process_input(user_input):
    start_time = time.time()
    tools_called = []
    detect_instruction(user_input)
    instructions = get_instructions_context()
    full_system = LESTER_V5_SYSTEM + "\n" + TOOLS_DESC + CHAIN_DESC + instructions
    convo.add("user", user_input)
    messages = convo.get_messages(full_system)

    try:
        response = groq_client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.3,
            max_tokens=600, response_format={"type": "json_object"},
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = json.dumps({"action": "speak", "text": f"Error: {e}"})

    try:
        action = json.loads(reply)
    except json.JSONDecodeError:
        match = re.search(r"\{[^{}]+\}", reply)
        if match:
            try: action = json.loads(match.group())
            except: action = {"action": "speak", "text": reply[:200]}
        else:
            action = {"action": "speak", "text": reply[:200]}

    # Chain or single action
    if "chain" in action and isinstance(action["chain"], list):
        chain_steps = action["chain"]
        print(f"\n  CHAIN DETECTED: {len(chain_steps)} steps")
        for step in chain_steps:
            tools_called.append({"name": step.get("action","?"), "args": {k:v for k,v in step.items() if k != "action"}})
        chain_results = execute_chain(chain_steps)
        final_text = chain_results[-1]["result"] if chain_results else "Chain complete."
        if chain_steps[-1].get("action") == "speak":
            final_text = chain_steps[-1].get("text", final_text)
            if "{result}" in final_text and len(chain_results) > 1:
                final_text = final_text.replace("{result}", chain_results[-2]["result"][:300])
    else:
        action_name = action.get("action", "speak")
        tools_called.append({"name": action_name, "args": {k:v for k,v in action.items() if k != "action"}})
        if action_name in TOOL_FUNCTIONS:
            args = {k: v for k, v in action.items() if k != "action"}
            try: result = TOOL_FUNCTIONS[action_name](**args)
            except Exception as e: result = f"Error: {e}"
        else:
            result = action.get("text", "Done.")
        if action_name == "speak":
            final_text = action.get("text", result)
        else:
            final_text = result

    convo.add("assistant", reply)
    latency = int((time.time() - start_time) * 1000)
    trace_id = str(uuid.uuid4())[:8]
    db.execute("INSERT INTO traces VALUES (?,?,?,?,?,?)",
        (trace_id, datetime.now().isoformat(), user_input[:200], final_text[:200], json.dumps(tools_called), latency))
    db.commit()

    print(f"\n{'~'*50}")
    print(f"  IN:    {user_input[:80]}")
    print(f"  STEPS: {len(tools_called)}")
    print(f"  OUT:   {final_text[:80]}")
    print(f"  TIME:  {latency}ms")
    print(f"{'~'*50}")
    return final_text


# === FLASK APP ===
app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'))

HTML_PAGE = ('<!DOCTYPE html><html><head><title>Lester</title>'
    '<style>'
    '*{margin:0;padding:0;box-sizing:border-box}'
    'body{font-family:-apple-system,sans-serif;background:#0d1117;color:#c9d1d9;height:100vh;display:flex;flex-direction:column;align-items:center;padding-top:10px}'
    'h1{color:#58a6ff;font-size:1.5em}.badge{background:linear-gradient(135deg,#238636,#2ea043);color:#fff;padding:2px 9px;border-radius:12px;font-size:0.58em;margin-left:5px}'
    '.sub{color:#484f58;font-size:0.68em;margin-bottom:5px}'
    '#orb{width:72px;height:72px;border-radius:50%;background:radial-gradient(circle,#161b22,#0d1117);border:3px solid #3fb950;display:flex;align-items:center;justify-content:center;font-size:1.7em;margin:5px;transition:all 0.5s}'
    '#orb.listening{border-color:#3fb950;box-shadow:0 0 20px rgba(63,185,80,0.2);animation:breathe 3s infinite}'
    '#orb.thinking{border-color:#d29922;box-shadow:0 0 30px rgba(210,153,34,0.25);animation:spin 1s linear infinite}'
    '#orb.speaking{border-color:#a371f7;box-shadow:0 0 30px rgba(163,113,247,0.25);animation:pulse 0.5s infinite}'
    '#orb.muted{border-color:#f85149;box-shadow:0 0 20px rgba(248,81,73,0.2);opacity:0.6;animation:none}'
    '#orb.waiting{border-color:#8b949e;box-shadow:none;animation:none}'
    '@keyframes breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.03)}}'
    '@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.6}}'
    '@keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}'
    '#state{font-size:0.72em;color:#484f58;margin:2px}'
    '#log{width:95%;max-width:700px;height:350px;overflow-y:auto;background:#161b22;border:1px solid #21262d;border-radius:10px;padding:10px;margin:4px;font-size:0.7em;font-family:monospace;white-space:pre-wrap}'
    '.u{color:#58a6ff}.a{color:#3fb950}.s{color:#484f58;font-style:italic}.e{color:#f85149}.t{color:#d29922}'
    '#inp{display:flex;gap:5px;margin-top:4px;width:95%;max-width:700px}'
    '#inp input{flex:1;padding:8px 14px;border-radius:20px;border:1px solid #21262d;background:#161b22;color:#c9d1d9;font-size:0.82em}'
    '#inp input:focus{border-color:#58a6ff;outline:none}'
    '#inp button{padding:8px 16px;border-radius:20px;border:none;background:linear-gradient(135deg,#238636,#2ea043);color:#fff;cursor:pointer;font-weight:bold;font-size:0.82em}'
    '.hint{position:fixed;bottom:10px;right:10px;color:#484f58;font-size:0.6em}'
    '</style></head><body>'
    '<h1>Lester <span class="badge">GROQ FREE</span></h1>'
    '<div class="sub">Always listening | Ctrl+M mute | $0 cost | chains enabled</div>'
    '<div id="orb" class="waiting">&#128075;</div>'
    '<div id="state">Click anywhere to start...</div>'
    '<div id="log"></div>'
    '<div id="inp"><input type="text" id="ti" placeholder="Or type..." onkeypress="if(event.key===\'Enter\')send()"><button onclick="send()">Send</button></div>'
    '<div class="hint">Ctrl+M = mute | Groq free | chains: up to 5 steps</div>'
    '<script>'
    'const syn=window.speechSynthesis;let st="waiting",rec=null,muted=false,started=false,listenTimer=null,buffer="";'
    'const LISTEN_TIMEOUT=7000;'
    'document.addEventListener("keydown",(e)=>{if(e.ctrlKey&&e.key==="m"){e.preventDefault();toggleMute();}});'
    'function startLester(){if(started)return;started=true;const o=document.getElementById("orb"),s=document.getElementById("state");'
    'o.className="listening";o.textContent="\\u{1F3A4}";s.textContent="Listening...";'
    'log("s","Lester v5 (Groq/LLaMA) ONLINE");log("s","Cost: $0.00 forever");log("s","Piper TTS | 7-second listening | Chains enabled");'
    'if(rec){try{rec.start();}catch(e){}}}'
    'document.addEventListener("click",startLester,{once:true});'
    'function toggleMute(){if(!started)startLester();muted=!muted;const o=document.getElementById("orb"),s=document.getElementById("state");'
    'if(muted){try{rec.stop();}catch(e){}clearTimeout(listenTimer);buffer="";o.className="muted";o.textContent="\\u{1F507}";s.textContent="Muted (Ctrl+M)";log("s","Muted");}'
    'else{o.className="listening";o.textContent="\\u{1F3A4}";s.textContent="Listening...";try{rec.start();}catch(e){}log("s","Unmuted");}}'
    'const SR=window.SpeechRecognition||window.webkitSpeechRecognition;'
    'if(SR){rec=new SR();rec.continuous=true;rec.interimResults=true;rec.lang="en-US";'
    'rec.onresult=(e)=>{if(muted)return;let transcript="";for(let i=e.resultIndex;i<e.results.length;i++){transcript+=e.results[i][0].transcript;}'
    'buffer=transcript.trim();if(buffer.length>0){document.getElementById("state").textContent=buffer+" ...";'
    'clearTimeout(listenTimer);listenTimer=setTimeout(()=>{if(buffer.length>0){const final=buffer;buffer="";proc(final);}},LISTEN_TIMEOUT);}};'
    'rec.onend=()=>{if(!muted&&st!=="thinking"&&st!=="speaking"&&started)setTimeout(()=>{try{rec.start();}catch(e){}},100);};'
    'rec.onerror=(e)=>{if(e.error!=="no-speech")log("e","Err: "+e.error);if(!muted&&started)setTimeout(()=>{try{rec.start();}catch(e){}},500);};}'
    'function setState(s){st=s;const o=document.getElementById("orb"),l=document.getElementById("state");o.className=s;'
    'const m={listening:["\\u{1F3A4}","Listening..."],thinking:["\\u{1F9E0}","Processing..."],speaking:["\\u{1F5E3}","Speaking..."],muted:["\\u{1F507}","Muted"],waiting:["\\u{1F44B}","Click anywhere to start..."]};'
    'o.textContent=(m[s]||m.listening)[0];l.textContent=(m[s]||m.listening)[1];}'
    'async function proc(text){if(!started)startLester();setState("thinking");log("u","> "+text);try{rec.stop();}catch(e){}clearTimeout(listenTimer);buffer="";'
    'try{const r=await fetch("/cmd",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});'
    'const d=await r.json();log("a","< "+d.text);if(d.trace)log("t","  "+d.trace);'
    'setState("speaking");const aud=new Audio("/static/speech.wav?v=" + new Date().getTime());'
    'aud.onended=()=>{setState("listening");setTimeout(()=>{if(!muted)try{rec.start();}catch(e){}},200);};'
    'aud.onerror=()=>{log("e","Audio playback failed");setState("listening");setTimeout(()=>{if(!muted)try{rec.start();}catch(e){}},200);};'
    'aud.play().catch(()=>{log("e","Audio blocked - click page first");setState("listening");setTimeout(()=>{if(!muted)try{rec.start();}catch(e){}},200);});'
    '}catch(e){log("e","ERR: "+e.message);setState("listening");setTimeout(()=>{if(!muted)try{rec.start();}catch(e){}},300);}}'
    'function send(){if(!started)startLester();const i=document.getElementById("ti");if(i.value.trim()){proc(i.value.trim());i.value="";}}'
    'function log(c,m){const l=document.getElementById("log"),d=document.createElement("div");d.className=c;d.textContent=m;l.appendChild(d);l.scrollTop=l.scrollHeight;}'
    '</script></body></html>')


@app.route("/")
def index():
    return HTML_PAGE

@app.route("/cmd", methods=["POST"])
def cmd():
    text = request.json.get("text", "")
    if not text:
        return jsonify({"text": "Didn't catch that.", "trace": ""})
    threading.Thread(target=play_ack).start()
    result = process_input(text)
    convo.add_turn(text, result)
    trace_row = db.execute("SELECT tools_called, latency_ms FROM traces ORDER BY timestamp DESC LIMIT 1").fetchone()
    trace_info = ""
    if trace_row:
        tools = json.loads(trace_row[0]) if trace_row[0] else []
        trace_info = f"{' > '.join(t['name'] for t in tools)} ({trace_row[1]}ms)"
    return jsonify({"text": result, "trace": trace_info})

@app.route("/traces")
def traces():
    rows = db.execute("SELECT timestamp, input, output, tools_called, latency_ms FROM traces ORDER BY timestamp DESC LIMIT 50").fetchall()
    return jsonify([{"time": r[0], "input": r[1], "output": r[2], "tools": json.loads(r[3]), "ms": r[4]} for r in rows])

@app.route("/status")
def status():
    return jsonify({
        "agent": "Lester", "version": "v5", "model": MODEL, "cost": "$0",
        "tools": len(TOOL_FUNCTIONS), "max_chain": MAX_CHAIN_STEPS,
        "instructions": db.execute("SELECT COUNT(*) FROM instructions WHERE active=1").fetchone()[0],
        "saved": db.execute("SELECT COUNT(*) FROM saved_data WHERE active=1").fetchone()[0],
        "traces": db.execute("SELECT COUNT(*) FROM traces").fetchone()[0],
        "langsmith_project": os.environ.get("LANGSMITH_PROJECT", "stan_to_lester"),
    })


# === STARTUP ===
if __name__ == "__main__":
    if not os.path.exists(ACK_SOUND):
        subprocess.run(f"sox -n {ACK_SOUND} synth 0.1 sine 800 fade 0 0.1 0.05 vol 0.3", shell=True)
        print("  Generated ack.wav")

    ls_active = os.environ.get("LANGSMITH_TRACING", "") == "true"
    print("\n" + "="*50)
    print("  LESTER v5 - GROQ (FREE) + PIPER TTS")
    print("="*50)
    print(f"  Model:     {MODEL}")
    print(f"  Cost:      $0.00 (free tier)")
    print(f"  Speed:     ~500 tokens/sec")
    print(f"  Tools:     {len(TOOL_FUNCTIONS)} functions")
    print(f"  Chains:    up to {MAX_CHAIN_STEPS} steps")
    print(f"  Tracing:   {'ON -> stan_to_lester' if ls_active else 'OFF'}")
    print(f"  Memory:    {DB_PATH}")
    print(f"  Mode:      Always listening (Ctrl+M = mute)")
    print(f"  Listen:    7-second window")
    print(f"  TTS:       Piper (lessac-high)")
    print("="*50)
    print("  http://localhost:5000")
    print("  http://localhost:5000/traces")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
