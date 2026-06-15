from app.models import Booking

ATTENDANCE_CONFIRMED = "confirmed"
ATTENDANCE_CANNOT_ATTEND = "cannot_attend"
ATTENDANCE_REASON_PROVIDED = "reason_provided"
MAX_ATTENDANCE_REASON_LEN = 1000


def has_attendance_response(booking: Booking) -> bool:
    return bool(booking.attendance_status)


def attendance_list_indicator(booking: Booking) -> str:
    if booking.attendance_status == ATTENDANCE_CONFIRMED:
        return "✅ "
    if booking.attendance_status in (ATTENDANCE_CANNOT_ATTEND, ATTENDANCE_REASON_PROVIDED):
        return "⚠️ "
    return ""


def attendance_admin_label_indicator(booking: Booking) -> str:
    if booking.attendance_status == ATTENDANCE_CONFIRMED:
        return "✅"
    if booking.attendance_status == ATTENDANCE_REASON_PROVIDED:
        return "💬"
    if booking.attendance_status == ATTENDANCE_CANNOT_ATTEND:
        return "⚠️"
    return "❔"
