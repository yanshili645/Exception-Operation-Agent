from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from .common import address_key, minutes_between, normal_text, parse_dt


SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


@dataclass
class ExceptionRecord:
    report_date: str
    code: str
    severity: str
    category: str
    job_number: str = ""
    customer: str = ""
    truck: str = ""
    employee: str = ""
    planned: str = ""
    actual: str = ""
    variance: str = ""
    evidence: str = ""
    owner: str = ""
    recommended_action: str = ""
    source: str = ""
    status: str = "Open"
    resolution: str = ""


def load_staff_mapping(path: Path) -> dict[str, str]:
    result = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("active", "true")).lower() == "true":
                result[str(row["servicem8_staff_uuid"])] = str(row["deputy_employee_id"])
    return result


def _add(records: list[ExceptionRecord], report_date: date, **values):
    records.append(ExceptionRecord(report_date=report_date.isoformat(), **values))


def _site_match(customer: str, candidates: list[str]) -> str | None:
    normalized = normal_text(customer)
    for candidate in candidates:
        if normal_text(candidate) in normalized or normalized in normal_text(candidate):
            return candidate
    return None


def evaluate(bundle: dict, report_date: date, rules: dict, staff_mapping: dict[str, str]) -> list[dict]:
    records: list[ExceptionRecord] = []
    tz_name = rules["timezone"]
    jobs = bundle.get("jobs", [])
    rosters = bundle.get("rosters", [])
    timesheets = bundle.get("timesheets", [])

    rosters_by_employee = defaultdict(list)
    timesheets_by_employee = defaultdict(list)
    for roster in rosters:
        rosters_by_employee[str(roster.get("employee_id", ""))].append(roster)
    for timesheet in timesheets:
        timesheets_by_employee[str(timesheet.get("employee_id", ""))].append(timesheet)

    depot_key = address_key(rules["depot_address"])
    customer_jobs = [j for j in jobs if depot_key not in address_key(j.get("address", ""))]

    by_truck = defaultdict(list)
    by_address = defaultdict(list)
    for job in customer_jobs:
        by_truck[job.get("truck", "")].append(job)
        if address_key(job.get("address", "")):
            by_address[address_key(job.get("address", ""))].append(job)

    first_by_truck = {}
    for truck, truck_jobs in by_truck.items():
        ordered = sorted(truck_jobs, key=lambda j: parse_dt(j.get("check_in") or j.get("scheduled_start"), tz_name) or parse_dt("2999-01-01", tz_name))
        if ordered:
            first_by_truck[truck] = ordered[0]

    completed_statuses = {"completed", "complete", "paid", "successful"}
    cancelled_statuses = {"cancelled", "canceled", "deleted", "void"}

    for job in customer_jobs:
        number = str(job.get("job_number", job.get("job_uuid", "")))
        customer = str(job.get("customer", "Unknown customer"))
        truck = str(job.get("truck", ""))
        status = normal_text(job.get("status", ""))
        scheduled = parse_dt(job.get("scheduled_start"), tz_name)
        check_in = parse_dt(job.get("check_in"), tz_name)
        check_out = parse_dt(job.get("check_out"), tz_name)
        planned_minutes = int(job.get("planned_minutes", 0) or 0)
        actual_minutes = minutes_between(check_out, check_in)
        base = {"job_number": number, "customer": customer, "truck": truck}

        if status not in completed_statuses | cancelled_statuses:
            _add(records, report_date, code="JOB-01", severity="Critical", category="Job completion",
                 planned="Completed by end of day", actual=status or "No status", evidence=f"ServiceM8 job {number}",
                 owner="Planner", recommended_action="Confirm cause, contact customer and reschedule.", source="ServiceM8", **base)

        staff = [str(x) for x in job.get("staff_uuids", []) if str(x)]
        if not truck or not staff:
            missing = "truck and staff" if not truck and not staff else ("truck" if not truck else "staff")
            _add(records, report_date, code="JOB-02", severity="Critical", category="Allocation",
                 planned="Truck and operational staff assigned", actual=f"Missing {missing}", evidence=f"ServiceM8 job {number}",
                 owner="Dispatcher", recommended_action="Assign resources and investigate the planning failure.", source="ServiceM8", **base)

        delay = minutes_between(check_in, scheduled)
        if delay is not None and delay >= rules["late_job_medium_minutes"]:
            if delay >= rules["late_job_critical_minutes"]:
                severity = "Critical"
            elif delay >= rules["late_job_high_minutes"]:
                severity = "High"
            else:
                severity = "Medium"
            if _site_match(customer, rules["priority_first_sites"]):
                severity = "High" if severity == "Medium" else severity
            _add(records, report_date, code="JOB-03", severity=severity, category="Late arrival",
                 planned=scheduled.strftime("%H:%M") if scheduled else "", actual=check_in.strftime("%H:%M") if check_in else "Missing",
                 variance=f"{delay} min late", evidence=f"ServiceM8 job {number} timestamps", owner="Dispatcher",
                 recommended_action="Check the preceding job, travel and customer-access causes.", source="ServiceM8", **base)

        priority_site = _site_match(customer, rules["priority_first_sites"])
        if priority_site and first_by_truck.get(truck) is not job:
            first_number = first_by_truck.get(truck, {}).get("job_number", "Unknown")
            _add(records, report_date, code="JOB-04", severity="High", category="Priority sequence",
                 planned=f"{priority_site} first customer stop", actual=f"First job {first_number}", evidence=f"Truck {truck} sequence",
                 owner="Planner", recommended_action="Review route sequencing and document any approved exception.", source="ServiceM8", **base)

        noon_site = _site_match(customer, rules["after_noon_sites"])
        if noon_site and check_in and check_in.hour < 12:
            _add(records, report_date, code="JOB-09", severity="High", category="Restricted start",
                 planned="Start at or after 12:00", actual=check_in.strftime("%H:%M"), evidence=f"ServiceM8 job {number} check-in",
                 owner="Planner", recommended_action="Review sequencing and confirm whether the customer approved the early start.", source="ServiceM8", **base)

        if planned_minutes > 0 and actual_minutes is not None:
            overrun = actual_minutes - planned_minutes
            percent = (overrun / planned_minutes) * 100
            if overrun >= rules["duration_overrun_minimum_minutes"] and percent > rules["duration_overrun_percent"]:
                _add(records, report_date, code="JOB-05", severity="Medium", category="Duration overrun",
                     planned=f"{planned_minutes} min", actual=f"{actual_minutes} min", variance=f"+{overrun} min ({percent:.0f}%)",
                     evidence=f"ServiceM8 job {number} activity", owner="Operations Manager",
                     recommended_action="Validate the standard duration and record the overrun reason.", source="ServiceM8", **base)

        if status in completed_statuses and (not check_in or not check_out):
            _add(records, report_date, code="JOB-06", severity="Medium", category="Missing activity evidence",
                 planned="Check-in and check-out recorded", actual="Activity evidence incomplete", evidence=f"ServiceM8 job {number}",
                 owner="ServiceM8 Admin", recommended_action="Correct the activity process or missing record.", source="ServiceM8", **base)

        for staff_uuid in staff:
            deputy_id = staff_mapping.get(staff_uuid)
            if not deputy_id:
                _add(records, report_date, code="DAT-02", severity="High", category="Staff mapping",
                     employee=staff_uuid, planned="Active ServiceM8-to-Deputy mapping", actual="No mapping",
                     evidence=f"ServiceM8 job {number}; staff {staff_uuid}", owner="System Admin",
                     recommended_action="Create and verify the staff identity mapping.", source="Cross-system", **base)
            elif not rosters_by_employee.get(deputy_id):
                _add(records, report_date, code="XYS-01", severity="High", category="Roster mismatch",
                     employee=deputy_id, planned="Deputy roster for allocated staff", actual="No roster",
                     evidence=f"ServiceM8 job {number}; Deputy employee {deputy_id}", owner="Planner",
                     recommended_action="Correct the roster or ServiceM8 allocation.", source="Cross-system", **base)
            else:
                ts = timesheets_by_employee.get(deputy_id, [])
                if check_in and ts:
                    covered = any(
                        parse_dt(t.get("start"), tz_name) and parse_dt(t.get("end"), tz_name)
                        and parse_dt(t.get("start"), tz_name) <= check_in <= parse_dt(t.get("end"), tz_name)
                        for t in ts
                    )
                    if not covered:
                        _add(records, report_date, code="XYS-03", severity="High", category="Activity outside timesheet",
                             employee=deputy_id, planned="Job activity within clocked interval", actual=check_in.strftime("%H:%M"),
                             evidence=f"ServiceM8 job {number}; Deputy employee {deputy_id}", owner="Operations Manager",
                             recommended_action="Verify clock records and job timestamps.", source="Cross-system", **base)

        missing_fields = []
        for field in ("address", "postcode", "scheduled_start"):
            if not job.get(field):
                missing_fields.append(field)
        if planned_minutes <= 0:
            missing_fields.append("planned duration")
        if missing_fields:
            _add(records, report_date, code="DAT-01", severity="Medium", category="Job data quality",
                 planned="Required planning fields populated", actual="Missing " + ", ".join(missing_fields),
                 evidence=f"ServiceM8 job {number}", owner="ServiceM8 Admin",
                 recommended_action="Complete the required ServiceM8 fields.", source="ServiceM8", **base)

    for address, address_jobs in by_address.items():
        trucks = sorted({str(j.get("truck", "")) for j in address_jobs if j.get("truck")})
        if len(address_jobs) > 1 and len(trucks) > 1:
            for job in address_jobs:
                _add(records, report_date, code="JOB-07", severity="High", category="Same-site split",
                     job_number=str(job.get("job_number", "")), customer=str(job.get("customer", "")), truck=str(job.get("truck", "")),
                     planned="One truck per site", actual=", ".join(trucks), evidence=f"Address: {job.get('address', address)}",
                     owner="Planner", recommended_action="Consolidate the site allocation or document the operational reason.", source="ServiceM8")

    allocated_deputy = {staff_mapping.get(str(s)) for job in customer_jobs for s in job.get("staff_uuids", [])}
    allocated_deputy.discard(None)
    for roster in rosters:
        employee_id = str(roster.get("employee_id", ""))
        employee = roster.get("employee_name") or employee_id
        roster_start = parse_dt(roster.get("start"), tz_name)
        roster_end = parse_dt(roster.get("end"), tz_name)
        employee_timesheets = timesheets_by_employee.get(employee_id, [])
        timesheet = employee_timesheets[0] if employee_timesheets else None
        if not timesheet:
            _add(records, report_date, code="DEP-01", severity="Critical", category="No-show or missing timesheet",
                 employee=employee, planned=roster_start.strftime("%H:%M") if roster_start else "Rostered",
                 actual="No clock-on/timesheet", evidence=f"Deputy roster {roster.get('roster_id', '')}", owner="Operations Manager",
                 recommended_action="Confirm attendance and arrange coverage if required.", source="Deputy")
            continue

        actual_start = parse_dt(timesheet.get("start"), tz_name)
        actual_end = parse_dt(timesheet.get("end"), tz_name)
        late = minutes_between(actual_start, roster_start)
        if late is not None and late >= rules["late_clock_medium_minutes"]:
            severity = "High" if late >= rules["late_clock_high_minutes"] else "Medium"
            code = "DEP-03" if severity == "High" else "DEP-02"
            _add(records, report_date, code=code, severity=severity, category="Late clock-on", employee=employee,
                 planned=roster_start.strftime("%H:%M") if roster_start else "", actual=actual_start.strftime("%H:%M") if actual_start else "",
                 variance=f"{late} min late", evidence=f"Deputy roster {roster.get('roster_id', '')}; timesheet {timesheet.get('timesheet_id', '')}",
                 owner="Operations Manager" if severity == "High" else "Team Leader",
                 recommended_action="Record the reason and assess operational impact.", source="Deputy")

        scheduled_hours = float(roster.get("scheduled_hours", 0) or 0)
        actual_hours = float(timesheet.get("actual_hours", 0) or 0)
        overtime_minutes = round((actual_hours - scheduled_hours) * 60)
        if overtime_minutes > rules["overtime_minutes"]:
            severity = "Critical" if actual_hours > rules["maximum_paid_day_hours"] else "High"
            _add(records, report_date, code="DEP-04", severity=severity, category="Hours variance", employee=employee,
                 planned=f"{scheduled_hours:.2f} h", actual=f"{actual_hours:.2f} h", variance=f"+{overtime_minutes} min",
                 evidence=f"Deputy roster {roster.get('roster_id', '')}; timesheet {timesheet.get('timesheet_id', '')}",
                 owner="Operations Manager", recommended_action="Validate the cause before approving the timesheet.", source="Deputy")

        break_minutes = int(timesheet.get("break_minutes", 0) or 0)
        if actual_hours >= 6 and break_minutes < rules["minimum_meal_break_minutes"]:
            _add(records, report_date, code="DEP-05", severity="High", category="Meal break", employee=employee,
                 planned=f"At least {rules['minimum_meal_break_minutes']} min", actual=f"{break_minutes} min",
                 evidence=f"Deputy timesheet {timesheet.get('timesheet_id', '')}", owner="Operations Manager",
                 recommended_action="Confirm the actual break and correct the timesheet if necessary.", source="Deputy")

        if not timesheet.get("time_approved", False):
            _add(records, report_date, code="DEP-06", severity="Medium", category="Timesheet approval", employee=employee,
                 planned="Time approved", actual="Not approved", evidence=f"Deputy timesheet {timesheet.get('timesheet_id', '')}",
                 owner="Payroll/Admin", recommended_action="Review and approve or query the timesheet.", source="Deputy")

        if employee_id not in allocated_deputy and actual_hours > 0:
            _add(records, report_date, code="XYS-02", severity="Medium", category="Unmatched worked time", employee=employee,
                 planned="Worked shift linked to ServiceM8 activity", actual=f"{actual_hours:.2f} h with no allocation",
                 evidence=f"Deputy timesheet {timesheet.get('timesheet_id', '')}", owner="Operations Manager",
                 recommended_action="Identify non-job work or correct the ServiceM8 allocation.", source="Cross-system")

    rows = [asdict(r) for r in records]
    rows.sort(key=lambda x: (SEVERITY_ORDER[x["severity"]], x["code"], x["job_number"], x["employee"]))
    return rows


def summarize(exceptions: list[dict], bundle: dict, report_date: date) -> dict:
    counts = {severity: sum(1 for row in exceptions if row["severity"] == severity) for severity in SEVERITY_ORDER}
    jobs = bundle.get("jobs", [])
    completed = sum(1 for j in jobs if normal_text(j.get("status")) in {"completed", "complete", "paid", "successful"})
    rosters = bundle.get("rosters", [])
    timesheets = bundle.get("timesheets", [])
    scheduled_hours = sum(float(r.get("scheduled_hours", 0) or 0) for r in rosters)
    actual_hours = sum(float(t.get("actual_hours", 0) or 0) for t in timesheets)
    overall = "Red" if counts["Critical"] else ("Amber" if counts["High"] else "Green")
    return {
        "report_date": report_date.isoformat(),
        "overall_status": overall,
        "jobs_scheduled": len(jobs),
        "jobs_completed": completed,
        "jobs_incomplete": len(jobs) - completed,
        "staff_rostered": len(rosters),
        "timesheets_received": len(timesheets),
        "scheduled_hours": round(scheduled_hours, 2),
        "actual_hours": round(actual_hours, 2),
        "labour_variance_hours": round(actual_hours - scheduled_hours, 2),
        "exception_counts": counts,
        "total_exceptions": len(exceptions),
    }

