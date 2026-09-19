from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .ai_summary import generate_ai_narrative
from .connectors import DeputyClient, ServiceM8Client, load_file_bundle
from .engine import evaluate, load_staff_mapping, summarize
from .reporting import write_outputs


def parse_args():
    parser = argparse.ArgumentParser(description="PowerWash daily operations exception report")
    parser.add_argument("--mode", choices=("demo", "files", "live"), default="demo")
    parser.add_argument("--date", help="Operational date in YYYY-MM-DD; defaults to yesterday in Auckland")
    parser.add_argument("--input-dir", type=Path, default=Path("data/demo"))
    parser.add_argument("--output", type=Path, default=Path("outputs/latest"))
    parser.add_argument("--rules", type=Path, default=Path("config/rules.json"))
    parser.add_argument("--staff-mapping", type=Path, default=Path("config/staff_mapping.csv"))
    return parser.parse_args()


def main():
    args = parse_args()
    rules = json.loads(args.rules.read_text(encoding="utf-8"))
    tz_name = os.getenv("POWERWASH_TIMEZONE", rules.get("timezone", "Pacific/Auckland"))
    rules["timezone"] = tz_name
    report_date = date.fromisoformat(args.date) if args.date else (datetime.now(ZoneInfo(tz_name)).date() - timedelta(days=1))

    if args.mode in {"demo", "files"}:
        bundle = load_file_bundle(args.input_dir)
    else:
        sm8_key = os.environ.get("SERVICEM8_API_KEY", "").strip()
        deputy_url = os.environ.get("DEPUTY_INSTALL_URL", "").strip()
        deputy_token = os.environ.get("DEPUTY_ACCESS_TOKEN", "").strip()
        missing = [name for name, value in {
            "SERVICEM8_API_KEY": sm8_key,
            "DEPUTY_INSTALL_URL": deputy_url,
            "DEPUTY_ACCESS_TOKEN": deputy_token,
        }.items() if not value]
        if missing:
            raise SystemExit("Missing live credentials: " + ", ".join(missing))
        bundle = {
            **ServiceM8Client(sm8_key, tz_name).fetch(report_date),
            **DeputyClient(deputy_url, deputy_token, tz_name).fetch(report_date),
        }

    mapping = load_staff_mapping(args.staff_mapping)
    exceptions = evaluate(bundle, report_date, rules, mapping)
    summary = summarize(exceptions, bundle, report_date)
    narrative = generate_ai_narrative(summary, exceptions)
    source_meta = {
        "mode": args.mode,
        "report_date": report_date.isoformat(),
        "jobs": len(bundle.get("jobs", [])),
        "activities": len(bundle.get("activities", [])),
        "rosters": len(bundle.get("rosters", [])),
        "timesheets": len(bundle.get("timesheets", [])),
        "read_only": True,
    }
    write_outputs(args.output, summary, narrative, exceptions, source_meta)
    print(json.dumps({"output": str(args.output), **summary}, indent=2))


if __name__ == "__main__":
    main()

