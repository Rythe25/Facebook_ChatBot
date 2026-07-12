"""Save a customer's booking into Google Sheets."""
from datetime import datetime

import gspread
from langchain_core.tools import tool
from app.config import settings

# Connect ONCE at import; reuse the worksheet on every call.
_worksheet = (
    gspread.service_account(filename=settings.google_sheets_credentials_path)
    .open_by_key(settings.google_sheets_id)
    .sheet1
)


@tool
def save_booking(name: str, phone: str, service: str,
                 preferred_time: str, notes: str = "") -> str:
    """Save a customer's grooming booking to the salon's records.
    Call this ONLY after you have the customer's name, phone, the service,
    and their preferred date/time.

    Args:
        name: customer's full name
        phone: customer's phone number
        service: the grooming service requested
        preferred_time: preferred date and/or time
        notes: any extra details (breed, size, special requests)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _worksheet.append_row([timestamp, name, phone, service, preferred_time, notes])
    return f"Booking saved for {name} ({service}, {preferred_time})."