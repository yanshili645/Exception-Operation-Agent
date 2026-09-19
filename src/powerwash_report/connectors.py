from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .common import first, parse_dt


def _employee_name(raw: dict) -> str:
    """Read Deputy employee metadata when EmployeeInfo is an object or list."""
    metadata = raw.get("_DPMetaData", {})
    metadata_items = metadata if isinstance(metadata, list) else [metadata]
    for item in metadata_items:
        if not isinstance(item, dict):
            continue
        employee_info = item.get("EmployeeInfo", {})
        employees = employee_info if isinstance(employee_info, list) else [employee_info]
        for employee in employees:
            if isinstance(employee, dict):
                display_name = first(employee, "DisplayName", "displayName", default="")
                if display_name:
                    return str(display_name)
    return ""


def _json_request(url: str, *, headers: dict, method: str = "GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def load_file_bundle(input_dir: Path) -> dict:
    names = {
        "jobs": "servicem8_jobs.json",
        "activities": "servicem8_activities.json",
        "rosters": "deputy_rosters.json",
        "timesheets": "deputy_timesheets.json",
    }
    result = {}
    for key, filename in names.items():
        path = input_dir / filename
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, list):
            raise ValueError(f"{path} must contain a JSON array")
        result[key] = value
    return result


class ServiceM8Client:
    BASE = "https://api.servicem8.com/api_1.0"

    def __init__(self, api_key: str, timezone_name: str):
        self.headers = {"X-API-Key": api_key, "Accept": "application/json"}
        self.timezone_name = timezone_name

    def _get(self, resource: str, filter_expression: str | None = None):
        url = f"{self.BASE}/{resource}.json"
        if filter_expression:
            url += "?" + urllib.parse.urlencode({"$filter": filter_expression})
        return _json_request(url, headers=self.headers)

    def fetch(self, report_date: date) -> dict:
        # Pull compact reference data and filter by local date in normalization.
        jobs = self._get("job")
        activities = self._get("jobadminactivity")
        allocations = self._get("joballocation")
        companies = self._get("company")
        company_names = {
            str(first(c, "uuid", "company_uuid")): first(c, "name", "company_name", default="")
            for c in companies
        }
        normalized_activities = [self._normalize_activity(a) for a in activities]
        activities_by_job: dict[str, list] = {}
        for activity in normalized_activities:
            activities_by_job.setdefault(activity["job_uuid"], []).append(activity)
        allocations_by_job: dict[str, list] = {}
        for allocation in allocations:
            job_uuid = str(first(allocation, "job_uuid", "related_object_uuid", default=""))
            allocations_by_job.setdefault(job_uuid, []).append(allocation)
        normalized_jobs = []
        for raw in jobs:
            job = self._normalize_job(raw, company_names)
            acts = activities_by_job.get(job["job_uuid"], [])
            allocs = allocations_by_job.get(job["job_uuid"], [])
            job["staff_uuids"] = sorted({
                str(first(x, "staff_uuid", "allocated_to_staff_uuid", default=""))
                for x in allocs + acts
                if first(x, "staff_uuid", "allocated_to_staff_uuid")
            })
            if acts:
                starts = [parse_dt(a.get("actual_start"), self.timezone_name) for a in acts]
                ends = [parse_dt(a.get("actual_end"), self.timezone_name) for a in acts]
                starts = [x for x in starts if x]
                ends = [x for x in ends if x]
                job["check_in"] = min(starts).isoformat() if starts else None
                job["check_out"] = max(ends).isoformat() if ends else None
            scheduled = parse_dt(job.get("scheduled_start"), self.timezone_name)
            actual = parse_dt(job.get("check_in"), self.timezone_name)
            if (scheduled and scheduled.date() == report_date) or (actual and actual.date() == report_date):
                normalized_jobs.append(job)
        return {"jobs": normalized_jobs, "activities": normalized_activities}

    def _normalize_job(self, raw: dict, company_names: dict) -> dict:
        company_uuid = str(first(raw, "company_uuid", "company_id", default=""))
        return {
            "job_uuid": str(first(raw, "uuid", "job_uuid", default="")),
            "job_number": str(first(raw, "generated_job_id", "job_number", "uuid", default="")),
            "customer": first(raw, "customer", "company_name", default=company_names.get(company_uuid, "Unknown customer")),
            "status": str(first(raw, "status", "job_status", default="")).lower(),
            "address": first(raw, "job_address", "address", default=""),
            "suburb": first(raw, "job_address_suburb", "suburb", default=""),
            "postcode": str(first(raw, "job_address_postcode", "postcode", default="")),
            "scheduled_start": first(raw, "scheduled_start", "start_date", "date", default=None),
            "scheduled_until": first(raw, "scheduled_until", "completion_date", "end_date", default=None),
            "planned_minutes": int(float(first(raw, "planned_minutes", "duration_minutes", default=0) or 0)),
            "completed_at": first(raw, "completed_at", "completion_date", default=None),
            "truck": first(raw, "truck", "assigned_truck", default=""),
            "notes": first(raw, "notes", "job_description", default=""),
        }

    def _normalize_activity(self, raw: dict) -> dict:
        return {
            "activity_uuid": str(first(raw, "uuid", "activity_uuid", default="")),
            "job_uuid": str(first(raw, "job_uuid", "related_object_uuid", default="")),
            "staff_uuid": str(first(raw, "staff_uuid", "allocated_to_staff_uuid", default="")),
            "actual_start": first(raw, "actual_start", "start_date", "start_time", default=None),
            "actual_end": first(raw, "actual_end", "end_date", "completion_date", default=None),
        }


class DeputyClient:
    def __init__(self, install_url: str, token: str, timezone_name: str):
        self.base = install_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.timezone_name = timezone_name

    def _query(self, resource: str, payload: dict):
        url = f"{self.base}/api/v1/resource/{resource}/QUERY"
        return _json_request(url, headers=self.headers, method="POST", payload=payload)

    def fetch(self, report_date: date) -> dict:
        tz = ZoneInfo(self.timezone_name)
        start = datetime.combine(report_date, datetime.min.time(), tzinfo=tz)
        end = start + timedelta(days=1)
        roster_payload = {"search": {"s1": {"field": "Date", "data": report_date.isoformat(), "type": "eq"}}}
        timesheet_payload = {
            "search": {
                "s1": {"field": "StartTime", "data": int(start.timestamp()), "type": "gt"},
                "s2": {"field": "StartTime", "data": int(end.timestamp()), "type": "lt"},
            }
        }
        rosters = [self._normalize_roster(x) for x in self._query("Roster", roster_payload)]
        timesheets = [self._normalize_timesheet(x) for x in self._query("Timesheet", timesheet_payload)]
        return {"rosters": rosters, "timesheets": timesheets}

    def _normalize_roster(self, raw: dict) -> dict:
        return {
            "roster_id": str(first(raw, "Id", "id", default="")),
            "employee_id": str(first(raw, "Employee", "employee_id", default="")),
            "employee_name": _employee_name(raw),
            "start": first(raw, "StartTimeLocalized", "StartTime", "start", default=None),
            "end": first(raw, "EndTimeLocalized", "EndTime", "end", default=None),
            "scheduled_hours": float(first(raw, "TotalTime", "scheduled_hours", default=0) or 0),
            "published": bool(first(raw, "Published", "published", default=False)),
            "open": bool(first(raw, "Open", "open", default=False)),
            "location": str(first(raw, "OperationalUnit", "location", default="")),
        }

    def _normalize_timesheet(self, raw: dict) -> dict:
        break_minutes = 0
        for slot in raw.get("Slots", []) or []:
            if slot.get("strType") == "B":
                start = slot.get("intUnixStart")
                end = slot.get("intUnixEnd")
                if start and end:
                    break_minutes += max(0, round((end - start) / 60))
        return {
            "timesheet_id": str(first(raw, "Id", "id", default="")),
            "roster_id": str(first(raw, "Roster", "roster_id", default="")),
            "employee_id": str(first(raw, "Employee", "employee_id", default="")),
            "employee_name": _employee_name(raw),
            "start": first(raw, "StartTimeLocalized", "StartTime", "start", default=None),
            "end": first(raw, "EndTimeLocalized", "EndTime", "end", default=None),
            "actual_hours": float(first(raw, "TotalTime", "actual_hours", default=0) or 0),
            "break_minutes": break_minutes,
            "time_approved": bool(first(raw, "TimeApproved", "time_approved", default=False)),
            "pay_approved": bool(first(raw, "PayRuleApproved", "pay_approved", default=False)),
            "cost": float(first(raw, "Cost", "cost", default=0) or 0),
            "employee_comment": first(raw, "EmployeeComment", "employee_comment", default=""),
            "supervisor_comment": first(raw, "SupervisorComment", "supervisor_comment", default=""),
        }

