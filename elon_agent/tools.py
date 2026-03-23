from typing import Dict

# In-memory database for court schedules, mapping date to a dictionary of time slots and party names
COURT_SCHEDULE: Dict[str, Dict[str, str]] = {}


from datetime import datetime

# --- Dummy global data ---
COURT_SCHEDULE = {
    "2025-11-10": {"08:00": "unknown", "09:00": "unknown", "10:00": "unknown"},
    "2025-11-11": {"08:00": "unknown", "09:00": "unknown", "10:00": "busy", "11:00": "available"},
    "2025-11-12": {"08:00": "unknown", "09:00": "unknown", "10:00": "unknown"},
}

def generate_court_schedule():
    """Dummy: Pretend to generate a fixed 3-day schedule."""
    print("Dummy schedule initialized with fixed test dates and times.")

# Initialize dummy schedule
generate_court_schedule()


def list_court_availabilities(date: str) -> dict:
    """
    List available and booked time slots for a given date.
    """
    if date not in COURT_SCHEDULE:
        return {
            "status": "error",
            "message": f"No schedule found for {date}. Try another one please.",
            "schedule": {},
        }

    daily_schedule = COURT_SCHEDULE[date]
    available_slots = [t for t, v in daily_schedule.items() if v == "unknown"]
    booked_slots = {t: v for t, v in daily_schedule.items() if v != "unknown"}

    return {
        "status": "success",
        "message": f"Schedule for {date}.",
        "available_slots": available_slots,
        "booked_slots": booked_slots,
    }


def book_badminton_court(date: str, start_time: str, end_time: str, reservation_name: str) -> dict:
    """
    Dummy version: allows booking only for available slots on the given dates.
    """
    if date not in COURT_SCHEDULE:
        return {"status": "error", "message": f"No schedule for {date}."}

    # For simplicity, ignore end_time; only single-hour slots allowed
    if start_time not in COURT_SCHEDULE[date]:
        return {"status": "error", "message": f"Invalid time. Try 08:00, 09:00, or 10:00."}

    if COURT_SCHEDULE[date][start_time] != "unknown":
        return {
            "status": "error",
            "message": f"Slot {start_time} on {date} already booked by {COURT_SCHEDULE[date][start_time]}.",
        }

    COURT_SCHEDULE[date][start_time] = reservation_name

    return {
        "status": "success",
        "message": f"Booked {date} at {start_time} for {reservation_name}.",
    }