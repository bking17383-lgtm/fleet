#!/usr/bin/env python3
"""Jane mobile voice page HTML."""
from __future__ import annotations

from bus_lane import bus_root, safe_is_file, safe_read_text

DESK_CSS = ""


def _domain() -> str:
    p = bus_root() / "fleet/HITME_DOMAIN.txt"
    if safe_is_file(p):
        line = safe_read_text(p).strip().splitlines()
        if line and line[0]:
            return line[0]
    local = __import__("pathlib").Path.home() / ".stan/fleet/HITME_DOMAIN.local.txt"
    if local.is_file():
        line = safe_read_text(local).strip().splitlines()
        if line and line[0]:
            return line[0]
    return "hitme.dev"

def jane_html(*, float_mode: bool = False, host: str = "") -> str:
    dom = _domain()
    h = (host or "").split(":")[0].lower()
    if h.startswith("jane."):
        public = f"https://{h}/"
        bookmark = public + "?float=1"
    else:
        public = f"https://{dom}/jane"
        bookmark = f"https://jane.{dom}/" if dom else public
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0a0a12">
<link rel="manifest" href="/jane/manifest.json">
<title>Jane — {dom}</title>
<style>{DESK_CSS}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: #0a0a12; color: #eee; }}
body {{ max-width: 28rem; margin: 0 auto; padding: 1rem 1rem 6rem; }}
body.float-mode {{ padding: 0.75rem 0.75rem 5.5rem; }}
.pageChrome {{ }}
#learnBadge {{ font-size: 0.9rem; padding: 0.35rem 0; }}
#voiceStatus {{ font-size: 1rem; font-weight: 700; }}
#transcriptBox {{ margin: 0.75rem 0 1rem; text-align: left; }}
#liveRow {{ display: flex; align-items: center; gap: 0.5rem; margin: 0.65rem 0 0.85rem;
  padding: 0.55rem 0.75rem; background: #12121f; border: 1px solid #333; border-radius: 10px; }}
#liveDot {{ width: 11px; height: 11px; border-radius: 50%; background: #555; flex-shrink: 0; }}
#liveDot.on {{ background: #7bed9f; box-shadow: 0 0 0 0 rgba(123,237,159,0.5);
  animation: livepulse 1.4s infinite; }}
#liveDot.think {{ background: #ffb347; animation: none; }}
#liveDot.speak {{ background: #ff6b9d; animation: livepulse 1s infinite; }}
@keyframes livepulse {{ 0%,100% {{ box-shadow: 0 0 0 0 rgba(123,237,159,0.45); }} 50% {{ box-shadow: 0 0 0 7px rgba(123,237,159,0); }} }}
#liveLabel {{ font-size: 0.92rem; font-weight: 700; flex: 1; text-align: left; }}
#liveHint {{ font-size: 0.75rem; color: #888; margin: -0.35rem 0 0.65rem; text-align: left; }}
.txLabel {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: #888; margin: 0.5rem 0 0.2rem; }}
.txLabel.you {{ color: #ffb347; }}
  .txTurn {{ margin: 0.65rem 0 0.85rem; padding-bottom: 0.65rem; border-bottom: 1px solid #222; }}
  .txTurn:last-child {{ border-bottom: none; }}
  .txTurn .g {{ color: #7bed9f; font-size: 0.95rem; white-space: pre-wrap; word-break: break-word; margin: 0.25rem 0 0; }}
  #voiceReply {{ max-height: min(42vh, 20rem); overflow-y: auto; }}
#heardLine {{ color: #ffb347; font-size: 1.05rem; min-height: 1.4rem; line-height: 1.4;
  white-space: pre-wrap; word-break: break-word; margin: 0; }}
#heardInterim {{ color: #888; font-size: 0.88rem; min-height: 1rem; font-style: italic; margin: 0; }}
#micBtn {{
  border: none; border-radius: 999px; cursor: pointer; font-weight: 800;
  background: #484f58; color: #e6edf3; touch-action: manipulation;
}}
#micBtn.on {{ background: #c77dff; color: #0a0a12; animation: pulse 2s infinite; }}
@keyframes pulse {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.03); }} }}
#typed {{ width: 100%; background: #151525; color: #eee; border: 1px solid #333;
  border-radius: 0.75rem; padding: 0.75rem; font-size: 1rem; }}
#sendBtn {{ width: 100%; margin-top: 0.5rem; padding: 0.75rem; font-size: 1rem;
  background: #151525; color: #7bed9f; border: 1px solid #333; border-radius: 0.75rem; }}
#voiceReply pre {{ background: #0a0a12; border: 1px solid #333; border-radius: 0.75rem;
  padding: 0.75rem; font-size: 0.95rem; white-space: pre-wrap; word-break: break-word;
  max-height: none; overflow: visible; margin: 0; }}
.oneMic {{ font-size: 0.75rem; color: #888; margin: 0.25rem 0; }}
#janeFloat {{
  display: none; position: fixed; left: 0; right: 0; bottom: 0; z-index: 2147483646;
  padding: 0 0.5rem calc(0.5rem + env(safe-area-inset-bottom, 0px));
  pointer-events: none;
}}
body.float-mode #janeFloat {{ display: block; }}
body.float-mode .pageMic {{ display: none; }}
.floatShell {{
  pointer-events: auto; background: rgba(10,10,18,0.94); backdrop-filter: blur(12px);
  border: 1px solid #333; border-radius: 1.1rem 1.1rem 0.85rem 0.85rem;
  box-shadow: 0 -8px 32px rgba(0,0,0,0.55); overflow: hidden;
}}
.floatBar {{
  display: flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.65rem;
}}
.floatBar #micBtn {{ flex: 0 0 auto; min-width: 4.5rem; min-height: 3.2rem; padding: 0 1rem; font-size: 0.85rem; }}
.floatBar #voiceStatus {{ flex: 1; font-size: 0.85rem; min-height: auto; margin: 0; }}
#expandBtn {{
  flex: 0 0 auto; width: 2.5rem; height: 2.5rem; border-radius: 999px;
  border: 1px solid #444; background: #151525; color: #7bed9f; font-size: 1rem;
}}
#floatPanel {{ display: none; padding: 0 0.65rem 0.65rem; border-top: 1px solid #222; }}
#floatPanel.open {{ display: block; }}
.pageMic #micBtn {{ display: block; width: 100%; min-height: 4.5rem; margin: 0.75rem 0; font-size: 1.35rem; }}
</style></head><body class="float-mode">
<div class="pageChrome">
<h1>Jane</h1>
<p class="sub">Mobile Jane · Opus on cb1 · Daddy hosts · <a href="/lab">lab</a> · bookmark <strong>{public}</strong></p>
<p class="sub warn" style="color:#ff6b6b;font-size:.85rem">jane.hitme.dev may lag DNS · use {public}</p>
<p id="netNote" class="oneMic"></p>
<p id="learnBadge">Loading…</p>
<div id="liveRow"><span id="liveDot"></span><span id="liveLabel">Tap MIC — talk live</span></div>
<p id="liveHint">Type works · voice needs MIC tap · tap MIC again while Jane talks to stop her</p>
<p class="oneMic" id="voiceNote">Voice: loading…</p>
<p class="oneMic" id="oneMicNote">One mic only — close Jane on other phones/tabs</p>
<div id="transcriptBox">
  <p class="txLabel you">You said</p>
  <p id="heardLine">(mic or type below)</p>
  <p id="heardInterim"></p>
  <p class="txLabel jane">Jane</p>
  <div id="voiceReply"><pre>…</pre></div>
</div>
</div>
<div id="janeFloat">
  <div class="floatShell">
    <div class="floatBar">
      <button id="micBtn" type="button">MIC</button>
      <div id="voiceStatus">Starting…</div>
      <button id="expandBtn" type="button" aria-label="Expand">▲</button>
    </div>
    <div id="floatPanel">
      <textarea id="typed" rows="2" placeholder="Type if mic blocked…"></textarea>
      <button type="button" id="sendBtn">Send typed</button>
    </div>
  </div>
</div>
<script>
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) || window.innerWidth < 720;
if (isMobile || location.search.indexOf('float=1')>=0) document.body.classList.add('float-mode');
const floatMode = document.body.classList.contains('float-mode');
const status = document.getElementById('voiceStatus');
const heardLine = document.getElementById('heardLine');
const heardInterim = document.getElementById('heardInterim');
const micBtn = document.getElementById('micBtn');
const typed = document.getElementById('typed');
const reply = document.getElementById('voiceReply');
const expandBtn = document.getElementById('expandBtn');
const floatPanel = document.getElementById('floatPanel');
const liveDot = document.getElementById('liveDot');
const liveLabel = document.getElementById('liveLabel');
let micOn = false, speaking = false, sending = false, learnMode = false, lastReplyAt = 0;
let janeVoice = null, speechUnlocked = false;
const SPEAK_COOLDOWN_MS = 2800;
const JANE_PITCH = 0.86;
const JANE_RATE = 0.91;
let janeAudio = null;

function pickJaneVoice() {{
  if (!window.speechSynthesis) return null;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;
  const en = voices.filter(v => /^en([_-]|$)/i.test(v.lang || ''));
  const pool = en.length ? en : voices;
  const female = /female|samantha|zira|victoria|karen|moira|fiona|alice|susan|anna|kate|serena|tessa|google uk english female/i;
  const prefer = [
    /Daniel/i, /Alex/i, /Fred/i, /David/i, /Aaron/i, /Guy/i, /Mark/i, /James/i, /Tom/i,
    /Microsoft David/i, /Microsoft Guy/i, /Microsoft Mark/i,
    /Google US English/i, /en-us.*male/i, /Male/i, /com.apple.voice.compact.en-US.Alex/i
  ];
  for (const pat of prefer) {{
    const hit = pool.find(v => pat.test(v.name) && !female.test(v.name));
    if (hit) return hit;
  }}
  return pool.find(v => !female.test(v.name)) || pool[0] || null;
}}

function initJaneVoice() {{
  janeVoice = pickJaneVoice();
  const note = document.getElementById('voiceNote');
  if (!note) return;
  if (janeVoice) {{
    const short = janeVoice.name.split(/[ (]/).slice(0, 2).join(' ');
    note.textContent = isMobile ? 'Voice: Jane · warm female' : ('Voice: ' + short + ' · warm female');
  }} else {{
    note.textContent = 'Voice: Jane · warm female';
  }}
}}
if (window.speechSynthesis) {{
  speechSynthesis.onvoiceschanged = initJaneVoice;
  initJaneVoice();
  setTimeout(initJaneVoice, 300);
  setTimeout(initJaneVoice, 1200);
}}
const TAB_ID = sessionStorage.getItem('jane_tab') || ('g'+Math.random().toString(36).slice(2,9));
sessionStorage.setItem('jane_tab', TAB_ID);
const MIC_KEY = 'jane_mic_lock';

function claimMic() {{
  try {{
    const raw = localStorage.getItem(MIC_KEY);
    const lock = raw ? JSON.parse(raw) : null;
    const now = Date.now();
    if (lock && lock.id !== TAB_ID && (now - lock.ts) < 12000) {{
      status.textContent = 'Mic busy — close other Jane tab';
      document.getElementById('oneMicNote').textContent = 'Another tab has the mic. Close it here or there.';
      return false;
    }}
    localStorage.setItem(MIC_KEY, JSON.stringify({{id: TAB_ID, ts: now}}));
    return true;
  }} catch(e) {{ return true; }}
}}
function heartbeatMic() {{
  if (!micOn) return;
  try {{ localStorage.setItem(MIC_KEY, JSON.stringify({{id: TAB_ID, ts: Date.now()}})); }} catch(e) {{}}
}}
setInterval(heartbeatMic, 4000);

async function loadLearnMode() {{
  try {{
    const [lr, st] = await Promise.all([
      fetch('/api/alexa/learn').then(r=>r.json()),
      fetch('/api/jane/status').then(r=>r.json()).catch(()=>({{}}))
    ]);
    learnMode = lr.learn !== false;
    const badge = learnMode ? 'LEARN only — tap MIC still talks' : 'LIVE · Jane talks back';
    document.getElementById('learnBadge').textContent = badge;
  }} catch (e) {{ learnMode = false; document.getElementById('learnBadge').textContent = 'LIVE · Jane talks back'; }}
}}
loadLearnMode();

function setLive(state, label) {{
  liveDot.className = '';
  if (state === 'listen') {{ liveDot.classList.add('on'); }}
  else if (state === 'think') {{ liveDot.classList.add('think'); }}
  else if (state === 'speak') {{ liveDot.classList.add('speak'); }}
  else if (state === 'on') {{ liveDot.classList.add('on'); }}
  liveLabel.textContent = label;
}}

function micStatus() {{
  if (sending) return 'Jane thinking…';
  if (speaking) return 'Jane speaking…';
  return micOn ? 'Listening — talk now' : 'Tap MIC to talk';
}}

function appendTurn(you, jane, meta) {{
  const box = document.getElementById('voiceReply');
  if (box.querySelector('pre') && box.children.length === 1) box.innerHTML = '';
  const turn = document.createElement('div');
  turn.className = 'txTurn';
  const y = document.createElement('p');
  y.className = 'txLabel you';
  y.textContent = 'You';
  const yt = document.createElement('p');
  yt.textContent = you;
  const gl = document.createElement('p');
  gl.className = 'txLabel jane';
  gl.textContent = 'Jane' + (meta ? ' · ' + meta : '');
  const gt = document.createElement('p');
  gt.className = 'g';
  gt.textContent = jane;
  turn.appendChild(y); turn.appendChild(yt); turn.appendChild(gl); turn.appendChild(gt);
  box.appendChild(turn);
  box.scrollTop = box.scrollHeight;
}}

function stopSpeaking() {{
  try {{ speechSynthesis.cancel(); }} catch(x) {{}}
  if (janeAudio) {{ try {{ janeAudio.pause(); janeAudio.src = ''; }} catch(x) {{}} janeAudio = null; }}
  speaking = false;
  setLive(micOn ? 'listen' : 'idle', micOn ? 'Listening — your turn' : 'Tap MIC to talk live');
  status.textContent = micStatus();
}}

function speakDone() {{
  speaking = false;
  lastReplyAt = Date.now();
  heardInterim.textContent = '';
  setLive(micOn ? 'listen' : 'idle', micOn ? 'Listening — your turn' : 'Tap MIC for next line');
  status.textContent = micStatus();
  if (micOn && recOpen && claimMic()) setTimeout(() => {{ try {{ recOpen.start(); }} catch(x) {{}} }}, SPEAK_COOLDOWN_MS);
}}

function speakBrowser(t) {{
  if (!window.speechSynthesis) {{ speakDone(); return; }}
  speechSynthesis.cancel();
  const chunks = String(t).match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [String(t)];
  let idx = 0;
  function speakNext() {{
    if (idx >= chunks.length) {{ speakDone(); return; }}
    const bit = chunks[idx++].trim();
    if (!bit) {{ speakNext(); return; }}
    const u = new SpeechSynthesisUtterance(bit);
    applyJaneVoice(u);
    u.onend = () => {{ setTimeout(speakNext, 140); }};
    u.onerror = () => {{ stopSpeaking(); }};
    speechSynthesis.speak(u);
  }}
  speakNext();
}}

async function speakServer(t) {{
  try {{
    const r = await fetch('/api/jane/tts', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{text: t}})
    }});
    if (!r.ok) throw new Error('tts ' + r.status);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    if (janeAudio) {{ try {{ janeAudio.pause(); }} catch(x) {{}} }}
    janeAudio = new Audio(url);
    janeAudio.onended = () => {{ URL.revokeObjectURL(url); janeAudio = null; speakDone(); }};
    janeAudio.onerror = () => {{ URL.revokeObjectURL(url); janeAudio = null; speakBrowser(t); }};
    await janeAudio.play();
  }} catch (e) {{
    speakBrowser(t);
  }}
}}

function speak(t) {{
  if (!t) return;
  speaking = true;
  setLive('speak', 'Jane speaking…');
  status.textContent = 'Jane speaking… · tap MIC to stop';
  if (micOn && recOpen) {{ try {{ recOpen.stop(); }} catch(x) {{}} }}
  try {{ speechSynthesis.cancel(); }} catch(x) {{}}
  speakServer(t);
}}

async function sendText(text) {{
  const msg = text.trim();
  if (!msg || sending) return;
  if (!deskLinked) {{
    status.textContent = 'Not linked — wait or reload';
    await pingJane();
    if (!deskLinked) return;
  }}
  sending = true;
  setLive('think', 'Jane heard you · thinking…');
  status.textContent = 'Jane heard you · thinking…';
  heardLine.textContent = msg;
  heardInterim.textContent = '';
  if (!floatPanel.classList.contains('open')) {{ floatPanel.classList.add('open'); expandBtn.textContent = '▼'; }}
  const t0 = Date.now();
  try {{
    const body = {{text: msg, source: 'jane', mode: 'execute'}};
    const r = await fetch('/api/jane/talk', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(body)
    }});
    if (!r.ok) throw new Error('server ' + r.status);
    const d = await r.json();
    const display = d.reply || d.full || d.error || '?';
    const toSpeak = d.speak || d.aloud || display;
    const modeTag = d.mode === 'learn' ? ' [learn-only]' : '';
    const meta = (d.skill || '') + modeTag + ' · ' + (Date.now()-t0) + 'ms';
    if (display && display !== '?') appendTurn(msg, display, meta);
    else reply.innerHTML = '<pre>' + (d.error || '?') + '</pre>';
    if (d.ok && toSpeak && toSpeak !== '?') {{
      setLive('speak', 'Jane replying…');
      speak(toSpeak);
    }} else {{
      setLive('idle', 'Tap MIC to try again');
      status.textContent = d.error || 'Error';
    }}
    const shouldOpen = d.open_url && (d.skill === 'open' || (d.actions || []).some(a => String(a).startsWith('open:')));
    if (shouldOpen) setTimeout(() => {{ window.location.href = d.open_url; }}, 800);
    typed.value = '';
  }} catch (e) {{
    setLive('idle', 'Offline — try hitme.dev/jane');
    status.textContent = 'Offline? ' + String(e.message || e);
    const nn = document.getElementById('netNote');
    if (nn) nn.textContent = 'Can\\'t reach desk — bookmark https://hitme.dev/jane';
    reply.innerHTML = '<pre>' + String(e) + '</pre>';
  }} finally {{ sending = false; if (!speaking) {{ setLive(micOn?'listen':'idle', micOn?'Listening — your turn':'Tap MIC to talk live'); status.textContent = micStatus(); }} }}
}}

document.getElementById('sendBtn').onclick = () => sendText(typed.value);
expandBtn.onclick = () => {{
  const open = floatPanel.classList.toggle('open');
  expandBtn.textContent = open ? '▼' : '▲';
}};

let recOpen = null;
function applyJaneVoice(u) {{
  if (janeVoice) u.voice = janeVoice;
  u.lang = 'en-US';
  try {{ u.pitch = JANE_PITCH; u.rate = JANE_RATE; u.volume = 1; }} catch(e) {{}}
}}

function unlockSpeech() {{
  if (speechUnlocked || !window.speechSynthesis) return;
  initJaneVoice();
  const u = new SpeechSynthesisUtterance(' ');
  u.volume = 0.01;
  applyJaneVoice(u);
  u.onend = () => {{ speechUnlocked = true; initJaneVoice(); }};
  u.onerror = () => {{ speechUnlocked = true; }};
  try {{ speechSynthesis.speak(u); }} catch(e) {{ speechUnlocked = true; }}
}}

let deskLinked = true;
async function pingJane() {{
  const nn = document.getElementById('netNote');
  try {{
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const r = await fetch('/health', {{ cache: 'no-store', signal: ctrl.signal }});
    clearTimeout(timer);
    if (!r.ok) throw new Error('health ' + r.status);
    deskLinked = true;
    if (nn && !sending) nn.textContent = 'Linked to desk';
    if (!micOn && !speaking && !sending) liveLabel.textContent = 'Linked · tap MIC to talk';
  }} catch (e) {{
    deskLinked = false;
    if (nn) nn.textContent = 'Not linked — reload or open https://hitme.dev/jane';
    if (!sending && !speaking) setLive('idle', 'Not linked to desk');
  }}
}}

function startMic() {{
  unlockSpeech();
  initJaneVoice();
  if (!claimMic()) {{ micOn = false; micBtn.classList.remove('on'); micBtn.textContent = 'BUSY'; setLive('idle', 'Mic busy — close other Jane tab'); return; }}
  micOn = true;
  micBtn.textContent = 'ON';
  micBtn.classList.add('on');
  setLive('listen', 'Listening — talk now');
  status.textContent = micStatus();
  try {{ recOpen.start(); }} catch(x) {{ setLive('idle', 'Tap MIC · allow microphone'); status.textContent = 'Tap MIC · allow mic in browser settings'; }}
}}
function stopMic() {{
  micOn = false;
  micBtn.textContent = 'MIC';
  micBtn.classList.remove('on');
  try {{ recOpen.stop(); }} catch(x) {{}}
  heardInterim.textContent = '';
  setLive('idle', 'Tap MIC to talk live');
  status.textContent = 'MIC OFF · type still works';
}}
micBtn.onclick = () => {{
  if (speaking) {{ stopSpeaking(); return; }}
  micOn ? stopMic() : startMic();
}};

if (window.SpeechRecognition || window.webkitSpeechRecognition) {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recOpen = new SR();
  recOpen.continuous = !isMobile;
  recOpen.interimResults = true;
  recOpen.lang = 'en-US';
  recOpen.onstart = () => {{
    if (micOn) {{ setLive('listen', 'Listening — talk now'); status.textContent = micStatus(); }}
  }};
  recOpen.onspeechstart = () => {{
    if (micOn && !sending && !speaking) setLive('listen', 'Hearing you…');
  }};
  recOpen.onresult = ev => {{
    let fin = '', interim = '';
    for (let i = ev.resultIndex; i < ev.results.length; i++) {{
      const t = ev.results[i][0].transcript;
      if (ev.results[i].isFinal) fin += t; else interim += t;
    }}
    if (fin.trim()) {{
      const low = fin.trim().toLowerCase();
      if (speaking && /\\b(stop|enough|quiet|shut up|cancel|never mind)\\b/.test(low)) {{
        stopSpeaking();
        heardLine.textContent = fin.trim();
        heardInterim.textContent = '';
        return;
      }}
      heardLine.textContent = fin.trim();
      heardInterim.textContent = '';
      setLive('think', 'Got it — sending…');
      if (!speaking && !sending && (Date.now() - lastReplyAt) > SPEAK_COOLDOWN_MS) sendText(fin.trim());
    }} else if (interim.trim()) {{
      heardInterim.textContent = interim.trim();
      setLive('listen', 'Hearing: ' + interim.trim().slice(0, 36));
      status.textContent = interim.trim().slice(0, 48);
    }} else {{
      heardInterim.textContent = '';
      if (!sending && !speaking) status.textContent = micStatus();
    }}
  }};
  recOpen.onerror = ev => {{
    if (ev.error === 'not-allowed') {{ setLive('idle', 'Allow mic in browser settings'); status.textContent = 'Mic blocked — check settings'; }}
    else if (ev.error === 'aborted') {{}}
    else if (ev.error === 'no-speech' && micOn) {{ setLive('listen', 'Listening — say something'); status.textContent = 'Listening…'; }}
    else if (ev.error !== 'no-speech') {{ setLive('idle', 'Mic error: ' + ev.error); status.textContent = 'Mic: ' + ev.error; }}
  }};
  recOpen.onend = () => {{
    if (micOn && !speaking && !sending && claimMic() && (Date.now() - lastReplyAt) > SPEAK_COOLDOWN_MS)
      setTimeout(() => {{ try {{ recOpen.start(); }} catch(x) {{ setLive('idle', 'Tap MIC again'); micOn = false; micBtn.classList.remove('on'); micBtn.textContent = 'MIC'; }} }}, isMobile ? 650 : 400);
  }};
  fetch('/api/jane/history').then(r=>r.json()).then(d=>{{
    if(!d.ok||!d.turns)return;
    d.turns.forEach(t=>appendTurn(t[0], t[1], 'saved'));
  }}).catch(()=>{{}});
  document.addEventListener('visibilitychange', () => {{
    if (document.hidden) stopMic();
  }});
  pingJane();
  setInterval(pingJane, 25000);
  setLive('idle', 'Tap MIC to talk live');
  status.textContent = 'Tap MIC · then talk';
  micBtn.textContent = 'MIC';
}} else {{
  setLive('idle', 'No speech API — use type box');
  status.textContent = 'Voice not supported here — type below';
  micBtn.disabled = true;
  document.getElementById('liveHint').textContent = 'This browser has no speech-to-text — typed send works.';
}}
</script>
</body></html>"""


