"""Save a customer's confirmed order or reservation into Google Sheets."""
import logging
from datetime import datetime

import gspread
from langchain_core.tools import tool
from app.config import settings

logger = logging.getLogger(__name__)

# Spreadsheet "Local Noodle", first tab. Columns:
# Timestamp | Name | Phone | Order type | Order | Preferred time | Notes
_worksheet = (
    gspread.service_account(filename=settings.google_sheets_credentials_path)
    .open_by_key(settings.google_sheets_id)
    .sheet1
)


@tool
def save_booking(name: str, phone: str, order: str, preferred_time: str,
                 order_type: str = "Dine-in", notes: str = "") -> str:
    """Save a customer's CONFIRMED order or table reservation.
    Call this ONLY after the customer has confirmed AND you have their name,
    phone, what they want, and their preferred date/time. Never call it while
    details are still being collected.

    Args:
        name: customer's full name
        phone: customer's phone number
        order: the dishes ordered or the table reservation (e.g. "Beef Noodle x2" or "table for 4")
        preferred_time: preferred date and/or time
        order_type: one of "Dine-in", "Takeaway", or "Delivery"
        notes: any extra details (delivery address, spice level, special requests)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _worksheet.append_row(
        [timestamp, name, phone, order_type, order, preferred_time, notes]
    )
    logger.info("Saved %s booking for %s.", order_type, name)
    return f"Saved for {name} ({order_type}: {order}, {preferred_time})."