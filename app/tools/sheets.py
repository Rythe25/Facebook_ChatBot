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
def save_booking(name: str, phone: str, order: str,
                 preferred_time: str, notes: str = "") -> str:
    """Save a customer's order or table reservation to the restaurant's records.
    Call this ONLY after you have the customer's name, phone, what they want
    (dishes to order or a table reservation), and their preferred date/time.

    Args:
        name: customer's full name
        phone: customer's phone number
        order: the dishes ordered or the table reservation (e.g. "Beef Noodle x2" or "table for 4")
        preferred_time: preferred date and/or time
        notes: any extra details (delivery address, spice level, special requests)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _worksheet.append_row([timestamp, name, phone, order, preferred_time, notes])
    return f"Saved for {name} ({order}, {preferred_time})."