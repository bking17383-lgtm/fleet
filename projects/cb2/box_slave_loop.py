#!/usr/bin/env python3
"""Box slave loop — Bunny or Daddy. Copy to each box · run once · no Brian."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BOXES = {
    "bunny": {
        "to": "fleet/indie_loop/TO_BUNNY.txt",
        "from": "fleet/indie_loop/FROM_BUNNY.txt",
        "ack_dir": "drop_pile/from_bbbunny",
        "key": None,
    },
    "puppy": {
        "to": "fleet/indie_loop/TO_PUPPY.txt",
        "from": "fleet/indie_loop/FROM_PUPPY.txt",
        "ack_dir": "drop_pile/from_puppy",
        "key": None,
    },
    "daddy": {
        "to": "fleet/indie_loop/TO_DADDY.txt",
        "from": "fleet/indie_loop/FROM_DADDY.txt",
        "ack_dir": "drop_pile/from_lester",
        "key": "f770e0dc",
    },
}

INTERVAL = float(os.environ.get("BOX_SLAVE_SEC", "120"))
HB_EVERY = float(os.environ.get("BOX_SLAVE_HB_SEC", "120"))


def drive() -> Path:
    for p in (
        Path("/mnt/shared/GoogleDrive/MyDrive"),
        Path.home() / "GoogleDrive/MyDrive",
    ):
        if (p / "fleet").is_dir():
            return p
    raise SystemExit("NO_DRIVE")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def digest(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> int:
    box = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BOX_SLAVE", "")).lower()
    if box not in BOXES:
        print("Usage: box_slave_loop.py bunny|puppy|daddy")
        return 1
    cfg = BOXES[box]
    root = drive()
    to_p = root / cfg["to"]
    from_p = root / cfg["from"]
    ack = root / cfg["ack_dir"]
    ack.mkdir(parents=True, exist_ok=True)
    state_f = Path.home() / f".{box}_slave_state.json"
    host = subprocess.getoutput("hostname -s") or box
    ip = subprocess.getoutput("hostname -I").split()[0] or "?"
    prev = ""
    last_hb = 0.0
    prev_aws = ""
    prev_beacon = ""
    prev_brian = ""
    prev_brian_post = ""
    prev_puppy_relays: dict[str, str] = {}
    handoff = Path.home() / ".stan/handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    if state_f.is_file():
        try:
            st = json.loads(state_f.read_text())
            prev = st.get("to_hash", "")
            last_hb = float(st.get("last_hb", 0) or 0)
            prev_aws = st.get("aws_hash", "")
            prev_beacon = st.get("beacon_hash", "")
            prev_brian = st.get("brian_hash", "")
            prev_brian_post = st.get("brian_post_hash", "")
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    while True:
        job = to_p.read_text(encoding="utf-8", errors="replace") if to_p.is_file() else "(no job)"
        h = digest(to_p)
        job_changed = bool(h and h != prev)
        if job_changed:
            if "start_hitme_proxy" in job:
                sh = root / "lester/hitme_simple/start_hitme_proxy.sh"
                if sh.is_file():
                    subprocess.run(["bash", str(sh)], timeout=300, check=False)
            if box == "bunny":
                pub = subprocess.getoutput("curl -4 -sf --max-time 8 ifconfig.me") or "unknown"
                (ack / "PUBLIC_IP.txt").write_text(pub.strip() + "\n", encoding="utf-8")
            body = [
                f"FROM_{box.upper()} — {host} — {now()}",
                f"role: linux-loop (NOT Spark)",
                f"process: box_slave_loop.py · box={box}",
                f"host={host} ip={ip}",
                f"spark_ack: drop_pile/from_lester/lester6_to_daddy.md (Gemini only)",
                "--- TO ---",
                job.splitlines()[0] if job else "(empty)",
                job.splitlines()[1] if job.count("\n") else "",
            ]
            from_p.parent.mkdir(parents=True, exist_ok=True)
            from_p.write_text("\n".join(body[:9]) + "\n", encoding="utf-8")
            (ack / "linux_loop_ack.txt").write_text(
                f"linux-loop {box} {host} {now()}\n"
                f"ip={ip}\n"
                f"job={job.splitlines()[0][:60]}\n"
                f"note=NOT Spark — see lester6_to_daddy.md for Spark\n",
                encoding="utf-8",
            )
            prev = h

        if box == "daddy":
            aws_drop = ack / "aws_sandbox.env"
            aws_h = digest(aws_drop)
            if aws_h and aws_h != prev_aws:
                install = Path.home() / ".local/bin/cb2_aws_install.sh"
                pull = Path.home() / ".stan/aws_keys_pull.py"
                if pull.is_file():
                    subprocess.run([sys.executable, str(pull)], timeout=120, check=False)
                if install.is_file():
                    subprocess.run(["bash", str(install)], timeout=180, check=False)
                (ack / "aws_install_ran.txt").write_text(
                    f"aws drop seen {now()}\nhash={aws_h}\n", encoding="utf-8"
                )
                prev_aws = aws_h

            # Relay BEACON / Brian notes → Daddy handoff (Cursor reads ~/.stan/handoff/)
            beacon_src = None
            for cand in (
                root / "lester6_to_daddy.md",
                ack / "lester6_to_daddy.md",
                root / "drop_pile/from_lester/lester6_to_daddy.md",
            ):
                if cand.is_file():
                    beacon_src = cand
                    break
            if beacon_src:
                bh = digest(beacon_src)
                if bh and bh != prev_beacon:
                    text = beacon_src.read_text(encoding="utf-8", errors="replace")
                    (handoff / "beacon_to_daddy.md").write_text(text, encoding="utf-8")
                    (handoff / "cb2_job_pending.txt").write_text(
                        f"{now()} · BEACON note relayed from {beacon_src.name}\n", encoding="utf-8"
                    )
                    prev_beacon = bh

            brian_dir = root / "drop_pile/from_brian"
            brian_src = brian_dir / "NOTE.txt"
            if not brian_src.is_file():
                brian_src = brian_dir / "BRIAN_ORDER.txt"
            if not brian_src.is_file():
                brian_src = brian_dir / "BRIAN_LAW_EXECUTE.txt"
            if brian_src.is_file():
                br_h = digest(brian_src)
                if br_h and br_h != prev_brian:
                    (handoff / "brian_note.txt").write_text(
                        brian_src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
                    )
                    (handoff / "cb2_job_pending.txt").write_text(
                        f"{now()} · Brian note relayed from {brian_src.name}\n", encoding="utf-8"
                    )
                    prev_brian = br_h

            brian_post = root / "fleet/bus/BRIAN_LAST_POST.txt"
            if brian_post.is_file():
                bp_h = digest(brian_post)
                if bp_h and bp_h != prev_brian_post:
                    (handoff / "brian_last_post.txt").write_text(
                        brian_post.read_text(encoding="utf-8", errors="replace"),
                        encoding="utf-8",
                    )
                    if not (handoff / "cb2_job_pending.txt").is_file() or "Brian drop" not in (
                        handoff / "cb2_job_pending.txt"
                    ).read_text(encoding="utf-8", errors="replace"):
                        (handoff / "cb2_job_pending.txt").write_text(
                            f"{now()} · Brian post relayed (web/inbox)\n", encoding="utf-8"
                        )
                    prev_brian_post = bp_h

            puppy_ack = root / "drop_pile/from_puppy/linux_loop_ack.txt"
            puppy_hb = root / "drop_pile/from_puppy/puppy_heartbeat.md"
            for src, dest in (
                (puppy_ack, handoff / "puppy_slave_ack.txt"),
                (puppy_hb, handoff / "puppy_heartbeat.md"),
                (root / "drop_pile/from_puppy/brian_relay.txt", handoff / "puppy_brian_relay.txt"),
                (root / "drop_pile/from_puppy/qa_paths.txt", handoff / "puppy_qa_paths.txt"),
            ):
                if src.is_file():
                    sh = digest(src)
                    state_key = f"puppy_{dest.name}"
                    prev_p = st.get(state_key, "") if (st := {}) else ""
                    if state_f.is_file():
                        try:
                            prev_p = json.loads(state_f.read_text()).get(state_key, "")
                        except (json.JSONDecodeError, TypeError, ValueError):
                            prev_p = ""
                    if sh and sh != prev_p:
                        dest.write_text(
                            src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
                        )
                        (handoff / "cb2_job_pending.txt").write_text(
                            f"{now()} · Puppy slave relay ({src.name})\n", encoding="utf-8"
                        )

        if box == "puppy":
            brian_dir = root / "drop_pile/from_brian"
            brian_src = brian_dir / "NOTE.txt"
            if brian_src.is_file():
                br_h = digest(brian_src)
                if br_h and br_h != prev_brian:
                    (ack / "brian_relay.txt").write_text(
                        brian_src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
                    )
                    prev_brian = br_h

            t = time.time()
            if (t - last_hb) >= HB_EVERY:
                hb = ack / "puppy_heartbeat.md"
                hb.write_text(
                    f"# puppy heartbeat — linux-loop (NOT Spark)\n"
                    f"time: {now()}\n"
                    f"host: {host}\n"
                    f"machine: puppy\n"
                    f"process: box_slave_loop.py\n"
                    f"job: {job.splitlines()[0][:80]}\n",
                    encoding="utf-8",
                )
                if "path-test" in job.lower() or "path test" in job.lower():
                    lines = [f"# path test — {now()}\n"]
                    for p in ("/", "/health", "/drop", "/pee"):
                        code = subprocess.getoutput(
                            f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 15 https://hitme.dev{p}"
                        )
                        lines.append(f"{p} {code}\n")
                    (ack / "qa_paths.txt").write_text("".join(lines), encoding="utf-8")
                last_hb = t

        t = time.time()
        if box == "daddy" and (t - last_hb) >= HB_EVERY:
            hb = ack / "cb2_heartbeat.md"
            hb.write_text(
                f"# cb2 heartbeat — linux-loop (NOT Spark)\n"
                f"time: {now()}\n"
                f"host: {host}\n"
                f"machine: cb2\n"
                f"process: box_slave_loop.py\n"
                f"spark: Gemini Lester6 dev — ack in lester6_to_daddy.md\n"
                f"job: {job.splitlines()[0][:80]}\n",
                encoding="utf-8",
            )
            last_hb = t

        state_f.write_text(
            json.dumps(
                {
                    "to_hash": prev,
                    "aws_hash": prev_aws,
                    "beacon_hash": prev_beacon,
                    "brian_hash": prev_brian,
                    "brian_post_hash": prev_brian_post,
                    "time": now(),
                    "last_hb": last_hb,
                }
            )
            + "\n"
        )
        time.sleep(INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
