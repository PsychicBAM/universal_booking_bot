from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_service_location = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()
    entering_location = State()
    entering_comment = State()
    confirming = State()


class ClientBookingEditStates(StatesGroup):
    reschedule_choosing_date = State()
    reschedule_choosing_time = State()
    reschedule_confirm = State()
    changing_service_location = State()
    changing_client_address = State()
    changing_comment = State()


class AdminServiceStates(StatesGroup):
    name = State()
    description = State()
    duration = State()
    duration_manual = State()
    buffer = State()
    buffer_manual = State()
    price = State()
    editing_field = State()


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


class AdminUnavailableStates(StatesGroup):
    manual_date = State()
    manual_time = State()


class AdminMessageStates(StatesGroup):
    entering_message = State()


class AdminSettingsStates(StatesGroup):
    entering_value = State()
    entering_reminder_minutes = State()
    entering_contact = State()
