from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_service_location = State()
    choosing_date = State()
    choosing_time_period = State()
    choosing_time = State()
    confirming_telegram_name = State()
    entering_name = State()
    choosing_phone_method = State()
    entering_phone_manual = State()
    entering_phone = State()
    entering_location = State()
    entering_comment = State()
    confirming = State()


class ClientBookingEditStates(StatesGroup):
    reschedule_choosing_date = State()
    reschedule_choosing_time_period = State()
    reschedule_choosing_time = State()
    reschedule_confirm = State()
    changing_service_location = State()
    changing_client_address = State()
    changing_comment = State()


class AdminServiceStates(StatesGroup):
    name = State()
    description = State()
    choosing_type = State()
    duration = State()
    duration_manual = State()
    buffer = State()
    buffer_manual = State()
    price = State()
    editing_field = State()
    searching = State()


class OrderStates(StatesGroup):
    entering_details = State()
    confirming = State()
    editing_note = State()


class AdminServiceMediaStates(StatesGroup):
    uploading_photo = State()
    uploading_video = State()


class AdminServiceLocationStates(StatesGroup):
    entering_location_title = State()
    entering_location_address = State()
    entering_location_description = State()
    editing_location_title = State()
    editing_location_address = State()
    editing_location_description = State()


class AdminWorkingHoursStates(StatesGroup):
    manual_time = State()


class WorkingBreakStates(StatesGroup):
    choosing_weekday = State()
    entering_start = State()
    entering_end = State()
    entering_title = State()
    editing_start = State()
    editing_end = State()
    editing_title = State()


class AdminUnavailableStates(StatesGroup):
    manual_date = State()
    manual_time = State()


class AdminMessageStates(StatesGroup):
    entering_message = State()


class AdminClientSearchStates(StatesGroup):
    entering_query = State()


class AdminSettingsStates(StatesGroup):
    entering_value = State()
    entering_reminder_minutes = State()
    entering_contact = State()


class AdminStartScreenStates(StatesGroup):
    entering_ru_text = State()
    entering_en_text = State()
    uploading_photo_ru = State()
    uploading_photo_en = State()


class AdminConfirmationTextStates(StatesGroup):
    entering_value = State()


class ClientSupportStates(StatesGroup):
    choosing_booking = State()
    entering_message = State()


class AdminSupportStates(StatesGroup):
    entering_reply = State()


class AttendanceStates(StatesGroup):
    entering_reason = State()
