#!/usr/bin/env python3
"""
AWS lane — Bedrock talk + batch. NOT captain. NOT Echo Dot (separate Alexa API).

  python3 ~/.stan/aws_lane.py greet      # status + one-liner hello on bus
  python3 ~/.stan/aws_lane.py talk "…"  # chat → drop_pile/from_aws/
  python3 ~/.stan/aws_lane.py probe     # same as aws_sandbox_probe.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir, STAN, LOGS

ENV = STAN / "aws_sandbox.env"
BUS = bus_root()
CHAT_DIR = BUS / "drop_pile/from_aws"
STATUS = BUS / "fleet/bus/AWS_STATUS.txt"
PROBE = BUS / "fleet/bus/AWS_PROBE_REPORT.txt"
LOG = LOGS / "aws_lane.log"


def _load_env() -> None:
    if not ENV.is_file():
        raise SystemExit(f"missing {ENV}")
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def _bedrock_chat(prompt: str) -> str:
    import boto3
    from botocore.exceptions import ClientError

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    model = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    rt = boto3.client("bedrock-runtime", region_name=region)
    body = json.dumps(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            "inferenceConfig": {"maxTokens": 512, "temperature": 0.6},
        }
    )
    try:
        resp = rt.invoke_model(
            modelId=model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        raw = json.loads(resp["body"].read())
        parts = raw.get("output", {}).get("message", {}).get("content", [{}])
        return (parts[0].get("text") or "").strip()[:4000]
    except ClientError as e:
        return f"[bedrock error: {e}]"


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n")


def _status(ok: bool, detail: str) -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    safe_mkdir(STATUS.parent)
    STATUS.write_text(
        f"AWS_STATUS — {now}\nok={ok}\n{detail}\n"
        "lane=talk+batch only · not captain · not Echo Dot\n"
        "law=fleet/AWS_CHAT_LAW.txt\n",
        encoding="utf-8",
    )


def cmd_greet() -> None:
    _load_env()
    sys_prompt = (
        "You are AWS talk lane for Brian's ranch. Short. Soul not corporate. "
        "You do NOT captain the fleet. Assignments go to CPT. One paragraph max."
    )
    reply = _bedrock_chat(sys_prompt + " Say AWS_LANE_OK and one friendly line.")
    _status(True, reply[:500])
    print(reply)


def cmd_talk(msg: str) -> None:
    if not msg.strip():
        print("usage: aws_lane.py talk \"message\"")
        return
    _load_env()
    wrapped = (
        "Talk lane only — not fleet orders. Brian riff:\n" + msg.strip()
    )
    reply = _bedrock_chat(wrapped)
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_mkdir(CHAT_DIR)
    path = CHAT_DIR / f"talk_{now}.md"
    path.write_text(
        f"# AWS talk — {now}\n\n**Brian:** {msg.strip()}\n\n**AWS:** {reply}\n",
        encoding="utf-8",
    )
    _log(f"talk {len(msg)} chars → {path.name}")
    print(reply)
    print(f"\n→ {path}")


def cmd_probe() -> None:
    import subprocess
    subprocess.run([sys.executable, str(STAN / "aws_sandbox_probe.py")], check=False)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: aws_lane.py greet|talk|probe")
        raise SystemExit(1)
    cmd = sys.argv[1].lower()
    if cmd == "greet":
        cmd_greet()
    elif cmd == "talk":
        cmd_talk(" ".join(sys.argv[2:]))
    elif cmd == "probe":
        cmd_probe()
    else:
        raise SystemExit(f"unknown: {cmd}")


if __name__ == "__main__":
    main()
