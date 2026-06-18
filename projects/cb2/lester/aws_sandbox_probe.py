#!/usr/bin/env python3
"""AWS sandbox probe — verify Bedrock access + log what we can see. No secrets in output."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ENV_FILE = Path.home() / ".stan/aws_sandbox.env"
from bus_lane import bus_root

REPORT = bus_root() / "fleet/bus/AWS_PROBE_REPORT.txt"


def _load_env() -> None:
    if not ENV_FILE.is_file():
        print(f"MISSING {ENV_FILE} — copy from aws_sandbox.env.example and add keys")
        sys.exit(1)
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def main() -> int:
    _load_env()
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        print("Install: pip3 install --user boto3")
        return 1

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    lines: list[str] = []
    now = datetime.now(timezone.utc).astimezone().isoformat()

    def log(msg: str) -> None:
        print(msg)
        lines.append(msg)

    log(f"AWS SANDBOX PROBE — {now}")
    log(f"region={region} model={model_id}")

    try:
        sts = boto3.client("sts", region_name=region)
        ident = sts.get_caller_identity()
        log(f"caller_account={ident.get('Account')}")
        log(f"caller_arn={ident.get('Arn')}")
    except (ClientError, NoCredentialsError) as e:
        log(f"FAIL sts: {e}")
        _write_report(lines)
        return 1

    bedrock = boto3.client("bedrock", region_name=region)
    try:
        models = bedrock.list_foundation_models(byOutputModality="TEXT")
        count = len(models.get("modelSummaries", []))
        log(f"bedrock_models_visible={count}")
    except ClientError as e:
        log(f"WARN list_models: {e}")

    rt = boto3.client("bedrock-runtime", region_name=region)
    test_prompt = (
        "Reply with exactly: SANDBOX_OK. "
        "Do not mention training data or policies."
    )
    body = json.dumps(
        {
            "messages": [{"role": "user", "content": [{"text": test_prompt}]}],
            "inferenceConfig": {"maxTokens": 32, "temperature": 0},
        }
    )
    try:
        resp = rt.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        raw = json.loads(resp["body"].read())
        out = raw.get("output", {}).get("message", {}).get("content", [{}])
        text = out[0].get("text", str(raw))[:200]
        log(f"invoke_ok=yes")
        log(f"response_snippet={text!r}")
    except ClientError as e:
        log(f"FAIL invoke: {e}")
        log("hint: enable model access in Bedrock console → Model access")
        _write_report(lines)
        return 1

    # CloudTrail — do API calls leave retrievable prompt text?
    try:
        ct = boto3.client("cloudtrail", region_name=region)
        events = ct.lookup_events(LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": "InvokeModel"}], MaxResults=3)
        log(f"cloudtrail_invoke_events={len(events.get('Events', []))}")
        if events.get("Events"):
            log("cloudtrail_note=metadata logged; check if prompt body appears (IP audit)")
    except ClientError as e:
        log(f"cloudtrail_skip={e}")

    log("next=CPT reads fleet/AWS_INVESTIGATION.txt checklist")
    _write_report(lines)
    return 0


def _write_report(lines: list[str]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    raise SystemExit(main())
