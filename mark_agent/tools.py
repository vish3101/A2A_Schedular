import os
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from crewai.tools import BaseTool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

MARK_CALENDAR_ID = "primary"  # or explicit email if you want


def format_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p")


def get_calendar_service():
    creds = None

    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Missing credentials.json at {CREDENTIALS_FILE}")

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def get_availability(
    date_str: str,
    work_start_hour: int = 9,
    work_end_hour: int = 18,
) -> dict[str, str]:
    if not date_str:
        return {"status": "error", "message": "No date provided."}

    try:
        tz = ZoneInfo("Asia/Kolkata")
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}

    day_start = datetime.combine(target_date, time(work_start_hour, 0), tzinfo=tz)
    day_end = datetime.combine(target_date, time(work_end_hour, 0), tzinfo=tz)

    try:
        service = get_calendar_service()

        events_result = (
            service.events()
            .list(
                calendarId=MARK_CALENDAR_ID,
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        items = events_result.get("items", [])
        busy_periods = []

        for event in items:
            start_raw = event["start"].get("dateTime")
            end_raw = event["end"].get("dateTime")

            if not start_raw or not end_raw:
                return {
                    "status": "completed",
                    "message": f"On {date_str}, Mark is busy all day."
                }

            start_dt = datetime.fromisoformat(start_raw)
            end_dt = datetime.fromisoformat(end_raw)

            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=tz)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=tz)

            start_dt = max(start_dt, day_start)
            end_dt = min(end_dt, day_end)

            if start_dt < end_dt:
                busy_periods.append((start_dt, end_dt))

        busy_periods.sort(key=lambda x: x[0])

        merged = []
        for start_dt, end_dt in busy_periods:
            if not merged or start_dt > merged[-1][1]:
                merged.append([start_dt, end_dt])
            else:
                merged[-1][1] = max(merged[-1][1], end_dt)

        free_slots = []
        cursor = day_start

        for start_dt, end_dt in merged:
            if cursor < start_dt:
                free_slots.append((cursor, start_dt))
            cursor = max(cursor, end_dt)

        if cursor < day_end:
            free_slots.append((cursor, day_end))

        if not merged:
            return {
                "status": "completed",
                "message": (
                    f"On {date_str}, Mark is available all day "
                    f"from {format_time(day_start)} to {format_time(day_end)}."
                )
            }

        if not free_slots:
            busy_text = ", ".join(
                f"{format_time(start)} to {format_time(end)}"
                for start, end in merged
            )
            return {
                "status": "completed",
                "message": f"On {date_str}, Mark is busy all day. Busy slots: {busy_text}."
            }

        free_text = ", ".join(
            f"{format_time(start)} to {format_time(end)}"
            for start, end in free_slots
        )
        busy_text = ", ".join(
            f"{format_time(start)} to {format_time(end)}"
            for start, end in merged
        )

        return {
            "status": "completed",
            "message": (
                f"On {date_str}, Mark is available during: {free_text}. "
                f"Busy slots: {busy_text}."
            )
        }

    except Exception as e:
        return {"status": "error", "message": f"Calendar error: {str(e)}"}


class AvailabilityTool(BaseTool):
    name: str = "Calendar Availability Checker"
    description: str = (
        "Checks Mark's availability for a given date in YYYY-MM-DD format "
        "and returns free and busy timings."
    )

    def _run(self, date: str) -> str:
        return get_availability(date)["message"]