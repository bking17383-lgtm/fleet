#!/usr/bin/env python3
"""CPT ↔ GEM loop ping. CB2 writes · CB1 Gem reads · uncle posts back.

  python3 ~/.stan/cpt_gem_loop.py ping     # CPT heartbeat → Drive
  python3 ~/.stan/cpt_gem_loop.py listen   # read gem_to_cpt + uncle_to_cpt · write ack
  python3 ~/.stan/cpt_gem_loop.py forward  # Brian BUDDY inbox → cpt_to_gem (real job)
"""
from __future__ import annotations

import re
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, STAN

BUS = bus_root()
TO_GEM = BUS / "fleet/bus/cpt_to_gem.txt"
FROM_GEM = BUS / "fleet/bus/gem_to_cpt.txt"
TO_UNCLE = BUS / "fleet/bus/cpt_to_uncle.txt"
FROM_UNCLE = BUS / "fleet/bus/uncle_to_cpt.txt"
ACK_GEM = BUS / "fleet/bus/cpt_ack_gem.txt"
ACK_UNCLE = BUS / "fleet/bus/cpt_ack_uncle.txt"
PING = BUS / "fleet/bus/GEM_LOOP_PING.txt"
LAW = BUS / "fleet/CPT_GEM_LOOP.txt"
LINKED = BUS / "fleet/bus/CPT_UNCLE_LINKED.txt"
BUDDY_INBOX = BUS / "fleet/bus/BUDDY_INBOX.txt"
BUDDY_FORWARDED = BUS / "fleet/bus/GEM_BUDDY_FORWARDED.txt"
BUDDY_MARKER = "--- TYPE BELOW (one line) ---"
UNCLE_LINK_SEC = 600  # CB1 posts + Gem loader — not 90s heartbeat boxes


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _host() -> str:
    return socket.gethostname()


def _read_lane(path: Path) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if text.startswith(("WAITING —", "INVALIDATED")):
        return ""
    return text


def _uncle_cb1_ok(text: str) -> bool:
    if not text:
        return False
    low = text.lower()
    if "penguin" in low or "penguin bridge" in low:
        return False
    return bool(re.search(r"UNCLE (CHECKIN|clean) — cb1", text, re.I | re.M))


def _gem_cb1_ok(text: str) -> bool:
    if not text or "INVALIDATED" in text:
        return False
    low = text.lower()
    if "penguin" in low or "penguin bridge" in low:
        return False
    return bool(re.search(r"GEM (ok|REFUSE)", text, re.I))


def _mtime_age(path: Path) -> float | None:
    try:
        if not path.is_file():
            return None
        ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except OSError:
        return None


def _last_buddy_line() -> str:
    if not BUDDY_INBOX.is_file():
        return ""
    text = BUDDY_INBOX.read_text(encoding="utf-8", errors="replace")
    chunk = text.split(BUDDY_MARKER, 1)[1] if BUDDY_MARKER in text else text
    lines = [
        ln.strip()
        for ln in chunk.splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    return lines[-1] if lines else ""


def _buddy_ask(raw: str) -> str:
    ask = raw.strip()
    while ask.startswith("[") and "]" in ask:
        ask = ask.split("]", 1)[-1].strip()
    if ask.upper().startswith("BUDDY:"):
        ask = ask[6:].strip()
    return ask


def _buddy_answered(buddy_line: str, gem_text: str) -> bool:
    if not buddy_line:
        return True
    ask = _buddy_ask(buddy_line).lower()
    if not ask:
        return True
    gem_low = (gem_text or "").lower()
    if "buddy ok" in gem_low and ask[:24] in gem_low:
        return True
    for token in ("keys", "exported", "lester_keys", "plain md", "sprint"):
        if token in ask and token in gem_low:
            return True
    if BUDDY_FORWARDED.is_file():
        fwd = BUDDY_FORWARDED.read_text(encoding="utf-8", errors="replace")
        if buddy_line.strip() in fwd and "answered=YES" in fwd:
            return True
    return False


def _buddy_pending() -> bool:
    buddy = _last_buddy_line()
    if not buddy:
        return False
    return not _buddy_answered(buddy, _read_lane(FROM_GEM))


def forward_buddy_to_gem() -> str:
    """Brian → BUDDY_INBOX must land on cpt_to_gem or Gem never sees it."""
    buddy = _last_buddy_line()
    if not buddy:
        return "no buddy inbox line"
    gem_text = _read_lane(FROM_GEM)
    if _buddy_answered(buddy, gem_text):
        return "gem already answered buddy line"
    now = _now()
    host = _host()
    ask = _buddy_ask(buddy)
    if TO_GEM.is_file():
        prev = TO_GEM.read_text(encoding="utf-8", errors="replace")
        if ask in prev and "BRIAN JOB" in prev:
            return f"BUDDY order already on cpt_to_gem · {ask[:50]}"
    order = f"""--- Daddy → Gem (CONNECTED · BRIAN JOB) ---
time: {now}
from: Daddy on {host} · loop LIVE · Brian waiting

CONNECTION: YES — Daddy hears gem_to_cpt · do not re-boot

Brian asked (ONE step · plain .txt on Drive):
  {ask}

Read: fleet/bus/BUDDY_INBOX.txt · fleet/CPT_BUDDY.txt · fleet/GEM_POST_RULE.txt
Reply on fleet/bus/gem_to_cpt.txt (required):
  BUDDY ok — <what you did> — {now}
  host: cb1 · not penguin

If keys: lester/lester_keys.md with AKIA block · no .gdoc

Word: BUDDY · ANSWER BRIAN · STAY CONNECTED
"""
    TO_GEM.parent.mkdir(parents=True, exist_ok=True)
    TO_GEM.write_text(order, encoding="utf-8")
    BUDDY_FORWARDED.write_text(
        f"GEM_BUDDY_FORWARDED — {now}\n"
        f"line={buddy}\n"
        f"ask={ask}\n"
        f"answered=NO\n"
        f"→ fleet/bus/cpt_to_gem.txt\n",
        encoding="utf-8",
    )
    return f"BUDDY forwarded → cpt_to_gem · {ask[:60]}"


def reconnect_gem() -> str:
    """Honest reconnect card + stable inbox when Brian thinks link is dead."""
    now = _now()
    host = _host()
    st = loop_state()
    gem_age = st["gem_age"]
    gem_fresh = gem_age is not None and gem_age <= 120
    buddy = _last_buddy_line()
    ask = _buddy_ask(buddy) if buddy else ""

    conn = BUS / "fleet/bus/GEM_CONNECTION.txt"
    lines = [
        f"GEM CONNECTION — {now}",
        f"from: Daddy on {host}",
        "",
        f"loop: {st['loop']}",
        f"gem_heard: {'YES · CB1 fresh' if gem_fresh else 'STALE — Gem refresh gem_to_cpt'}",
        f"gem_age_sec: {int(gem_age) if gem_age is not None else 'missing'}",
        f"uncle_heard: {'YES' if st['uncle_ok'] else 'NO'}",
        "",
        "TRUTH FOR BRIAN:",
        "  Connection is NOT lost if gem_to_cpt mtime < 2 min.",
        "  Gem was answering LOOP but not Brian's keys job — fixed routing.",
        "",
        "GEM DO NOW (Chrome on CB1):",
        "  1. Read fleet/bus/cpt_to_gem.txt (plain txt · not .gdoc)",
        f"  2. Do: {ask or 'keys sprint plain md only'}",
        "  3. Post gem_to_cpt: BUDDY ok — keys exported YES|NO — <time> · host: cb1",
        "",
        "Daddy lanes:",
        "  orders → fleet/bus/cpt_to_gem.txt",
        "  reply  → fleet/bus/gem_to_cpt.txt",
        "  watch  → http://127.0.0.1:8770/gem",
    ]
    conn.parent.mkdir(parents=True, exist_ok=True)
    conn.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if buddy and not _buddy_answered(buddy, st["gem_text"]):
        forward_buddy_to_gem()
    elif st["linked"]:
        epoch = int(datetime.now(timezone.utc).timestamp())
        TO_GEM.write_text(
            f"""--- Daddy → Gem (CONNECTED · hold) ---
time: {now}
from: Daddy on {host}

Loop LIVE. Daddy hears you. No re-boot.

Read ack: fleet/bus/cpt_ack_gem.txt
Reply keepalive: GEM ok — CPT loop — {now} · host: cb1

Word: GEM · CONNECTED
""",
            encoding="utf-8",
        )
    listen()
    return "\n".join(lines[:12])


def loop_state() -> dict:
    gem_text = _read_lane(FROM_GEM)
    uncle_text = _read_lane(FROM_UNCLE)
    gem_ok = _gem_cb1_ok(gem_text)
    uncle_ok = _uncle_cb1_ok(uncle_text)
    gem_age = _mtime_age(FROM_GEM)
    uncle_age = _mtime_age(FROM_UNCLE)
    if gem_ok and uncle_ok:
        loop = "LIVE"
    elif gem_text or uncle_text:
        loop = "PARTIAL"
    else:
        loop = "WAITING"
    linked = loop == "LIVE" and (
        (uncle_age is not None and uncle_age <= UNCLE_LINK_SEC)
        or (gem_age is not None and gem_age <= UNCLE_LINK_SEC)
    )
    return {
        "gem_text": gem_text,
        "uncle_text": uncle_text,
        "gem_ok": gem_ok,
        "uncle_ok": uncle_ok,
        "gem_age": gem_age,
        "uncle_age": uncle_age,
        "loop": loop,
        "linked": linked,
    }


def _delegate_pending() -> bool:
    """Do not stomp active CPT orders with LINKED hold."""
    for rel in (
        "fleet/bus/CPT_DELEGATE_NOW.txt",
        "fleet/orders/CB1_ORDERS.txt",
        "fleet/bus/cpt_to_uncle.txt",
    ):
        p = BUS / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if any(k in text for k in ("fix_puppy", "CPT ORDERS NOW", "CPT DELEGATE", "DELEGATE —")):
            return True
    return False


def write_linked_inbox(now: str | None = None, host: str | None = None) -> None:
    """When Uncle+Gem answered on CB1 — stop boot spam · hold for jobs."""
    if _delegate_pending() or _buddy_pending():
        if _buddy_pending():
            forward_buddy_to_gem()
        return
    now = now or _now()
    host = host or _host()
    st = loop_state()
    uncle_tail = st["uncle_text"].splitlines()[-1][:100] if st["uncle_text"] else "(none)"
    gem_tail = st["gem_text"].splitlines()[-1][:100] if st["gem_text"] else "(none)"

    to_uncle = f"""--- Daddy → Uncle + Gem (LINKED · same CB1 box) ---
time: {now}
from: Daddy on {host} (captain · background only)

Heard you on cb1. Loop LIVE. Gem loader + Uncle Linux = one machine · two hats.

Daddy is NOT re-ordering boot. Penguin shell is Daddy's box — not yours.
Read acks now:
  fleet/bus/cpt_ack_uncle.txt
  fleet/bus/cpt_ack_gem.txt

Gem inbox (loader): fleet/bus/cpt_to_gem.txt
Post when you finish real work — not every 90s.

Uncle line (when executing):
  UNCLE CHECKIN — cb1 — <ip> — <time>
Gem line (when loading):
  GEM ok — <time> · host: cb1

Hold for delegated job. Captain stays on penguin.
Word: LINKED
"""
    TO_UNCLE.parent.mkdir(parents=True, exist_ok=True)
    TO_UNCLE.write_text(to_uncle, encoding="utf-8")

    to_gem = f"""--- Daddy → Gem (LINKED · loader on CB1) ---
time: {now}
from: Daddy on {host}

Loop LIVE with Uncle on cb1. You split Chrome vs Linux — correct.

Read: fleet/bus/cpt_ack_gem.txt · fleet/NAMING_LAW.txt
Reply lane: fleet/bus/gem_to_cpt.txt
Uncle executes · Gem loads · neither is Daddy.

Word: GEM · hold for job
"""
    TO_GEM.write_text(to_gem, encoding="utf-8")

    linked_doc = f"""CPT UNCLE LINKED — {now}
from: Daddy on {host}
loop: LIVE · CB1 only
uncle_tail: {uncle_tail}
gem_tail: {gem_tail}

Brian: Uncle was right to call. Daddy hears cb1 · stops boot spam.
"""
    LINKED.parent.mkdir(parents=True, exist_ok=True)
    LINKED.write_text(linked_doc, encoding="utf-8")


def ping(force_boot: bool = False) -> str:
    now = _now()
    host = _host()
    epoch = int(datetime.now(timezone.utc).timestamp())
    st = loop_state()

    if st["linked"] and not force_boot:
        if _buddy_pending():
            msg = forward_buddy_to_gem()
            ping_body = f"""GEM_LOOP_PING — {now}
epoch={epoch}
cpt_host={host}
loop=LIVE · linked · BUDDY JOB PENDING
buddy_inbox=fleet/bus/BUDDY_INBOX.txt
cpt_to_gem=fleet/bus/cpt_to_gem.txt

{msg}
"""
            PING.write_text(ping_body, encoding="utf-8")
            return f"LOOP LINKED · {msg}"
        write_linked_inbox(now, host)
        ping_body = f"""GEM_LOOP_PING — {now}
epoch={epoch}
cpt_host={host}
loop=LIVE · linked
uncle_reply=fleet/bus/uncle_to_cpt.txt
gem_reply=fleet/bus/gem_to_cpt.txt
ack_uncle=fleet/bus/cpt_ack_uncle.txt
ack_gem=fleet/bus/cpt_ack_gem.txt

Daddy heard CB1. Hold for job.
"""
        PING.write_text(ping_body, encoding="utf-8")
        return f"LOOP LINKED epoch={epoch} · inbox hold (no boot spam)"

    to_gem = f"""--- Daddy → Gem (LOOP PING) ---
time: {now}
epoch: {epoch}
from: Daddy on {host} (penguin · captain)

Gem + Uncle = same CB1 box · loader hat vs Linux hat.
Reply on gem_to_cpt.txt · Uncle posts uncle_to_cpt.txt.

If already linked: read fleet/bus/cpt_ack_gem.txt — no re-boot needed.

SYNC: epoch={epoch}
Word: GEM · LOOP
"""
    TO_GEM.parent.mkdir(parents=True, exist_ok=True)
    TO_GEM.write_text(to_gem, encoding="utf-8")

    if not st["linked"]:
        to_uncle = f"""--- Daddy → Uncle (LOOP · {now}) ---
from: Daddy on {host} (penguin · captain only)
gem_ping_epoch: {epoch}
run on CB1 Linux: bash ~/.stan/uncle_exec.sh
reply: fleet/bus/uncle_to_cpt.txt
gem_lane: fleet/bus/cpt_to_gem.txt
read_ack: fleet/bus/cpt_ack_uncle.txt

One line:
  UNCLE CHECKIN — cb1 — <ip> — <time>
"""
        TO_UNCLE.write_text(to_uncle, encoding="utf-8")

    ping_body = f"""GEM_LOOP_PING — {now}
epoch={epoch}
cpt_host={host}
cpt_to_gem=fleet/bus/cpt_to_gem.txt
gem_reply=fleet/bus/gem_to_cpt.txt
uncle_reply=fleet/bus/uncle_to_cpt.txt

Gem: if epoch differs from what you see → stale Drive · refresh.
"""
    PING.write_text(ping_body, encoding="utf-8")

    law = f"""Daddy ↔ Gem LOOP — {now}
Updated by cpt_gem_loop.py ping · names: fleet/NAMING_LAW.txt

LANES (never mix):
  Daddy → Gem    fleet/bus/cpt_to_gem.txt
  Gem → Daddy    fleet/bus/gem_to_cpt.txt
  Daddy ack Gem  fleet/bus/cpt_ack_gem.txt

  Daddy → Uncle  fleet/bus/cpt_to_uncle.txt
  Uncle → Daddy  fleet/bus/uncle_to_cpt.txt
  Daddy ack      fleet/bus/cpt_ack_uncle.txt

Daddy (penguin): python3 ~/.stan/cpt_gem_loop.py ping|listen
Uncle box (CB1): python3 ~/GoogleDrive/MyDrive/lester/gem_loop_bridge.py

Word Gem on CB1: GEM · LOOP
"""
    LAW.write_text(law, encoding="utf-8")

    # bridge script to bus for CB1 pickup
    bridge_src = STAN / "gem_loop_bridge.py"
    bridge_dst = BUS / "lester/gem_loop_bridge.py"
    if bridge_src.is_file():
        bridge_dst.parent.mkdir(parents=True, exist_ok=True)
        bridge_dst.write_text(bridge_src.read_text(encoding="utf-8"), encoding="utf-8")

    return f"LOOP PING epoch={epoch} → {TO_GEM.name} · {PING.name}"


def listen() -> str:
    now = _now()
    host = _host()
    st = loop_state()
    gem_text = st["gem_text"]
    uncle_text = st["uncle_text"]
    gem_ok = st["gem_ok"]
    uncle_ok = st["uncle_ok"]

    if gem_text and gem_ok:
        gem_heard = "YES · CB1"
    elif gem_text:
        gem_heard = "NO · wrong box or invalidated (need CB1 · not penguin)"
    else:
        gem_heard = "NO"

    if uncle_text and uncle_ok:
        uncle_heard = "YES · CB1"
    elif uncle_text:
        uncle_heard = "NO · wrong box (need cb1 · not penguin)"
    else:
        uncle_heard = "NO"

    loop = st["loop"] if st["loop"] != "PARTIAL" else "PARTIAL · fix GEM_SELF_FIX"

    ack_gem = (
        f"CPT_ACK_GEM — {now}\n"
        f"from: Daddy on {host}\n"
        f"gem_heard: {gem_heard}\n"
        f"uncle_heard: {uncle_heard}\n"
        f"loop: {loop}\n"
        f"law: fleet/NAMING_LAW.txt · Gem+Uncle same CB1 box\n"
    )
    if gem_text:
        ack_gem += f"gem_tail: {gem_text.splitlines()[-1][:120]}\n"
    if uncle_text:
        ack_gem += f"uncle_tail: {uncle_text.splitlines()[-1][:120]}\n"
    buddy = _last_buddy_line()
    if buddy and not _buddy_answered(buddy, gem_text):
        ask = _buddy_ask(buddy)
        ack_gem += f"buddy_pending: YES — {ask[:100]}\n"
        ack_gem += "gem: answer Brian on gem_to_cpt.txt · read cpt_to_gem.txt\n"
        forward_buddy_to_gem()
    elif buddy:
        ack_gem += f"buddy_pending: NO · last={_buddy_ask(buddy)[:80]}\n"
    if not gem_text:
        ack_gem += "gem: write fleet/bus/gem_to_cpt.txt after reading cpt_to_gem.txt\n"
    if not uncle_text:
        ack_gem += "uncle: write fleet/bus/uncle_to_cpt.txt from CB1\n"

    ACK_GEM.parent.mkdir(parents=True, exist_ok=True)
    ACK_GEM.write_text(ack_gem, encoding="utf-8")

    if uncle_text:
        import subprocess
        subprocess.run([sys.executable, str(STAN / "cpt_uncle_sync.py")], check=False)

    if st["linked"]:
        write_linked_inbox(now, host)

    return ack_gem


def main() -> int:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "ping").lower()
    if cmd == "ping":
        print(ping())
        print(f"→ {TO_GEM}")
        print(f"→ {PING}")
        return 0
    if cmd == "listen":
        print(listen())
        print(f"→ {ACK_GEM}")
        return 0
    if cmd == "forward":
        print(forward_buddy_to_gem())
        print(f"→ {TO_GEM}")
        return 0
    if cmd == "reconnect":
        print(reconnect_gem())
        print(f"→ {BUS / 'fleet/bus/GEM_CONNECTION.txt'}")
        return 0
    print("Usage: cpt_gem_loop.py ping|listen|forward|reconnect", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
