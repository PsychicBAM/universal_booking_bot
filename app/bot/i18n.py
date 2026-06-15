from __future__ import annotations

from app.config import get_settings

# Extend with "ar": {...} when Arabic translations are ready.
TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "welcome": "👋 Welcome to the booking bot!",
        "welcome_sub": "Book an appointment, view your bookings, or contact the admin.",
        "support_line": "\nSupport: @{username}",
        "book_appointment": "📅 Book appointment",
        "my_bookings": "📋 My bookings",
        "contact_admin": "📞 Contact admin",
        "language": "🌐 Language",
        "admin_menu": "⚙️ Admin menu",
        "back_main": "🔙 Back to main menu",
        "back": "◀️ Back",
        "cancel": "❌ Cancel",
        "choose_service": "Choose a service:",
        "choose_date": "Choose a date:",
        "searching_dates": "⏳ Searching available dates...",
        "dates_load_timeout": "Could not load available dates quickly. Please try again.",
        "choose_time": "Choose a time:",
        "enter_name": "Enter your name:",
        "enter_phone": "Enter your phone number:",
        "selected": "Selected: {dt}",
        "confirm_booking": "Confirm booking:",
        "label_service": "Service",
        "label_datetime": "Date & time",
        "label_name": "Name",
        "label_phone": "Phone",
        "booking_confirmed": "✅ Booking confirmed!",
        "booking_created_pending": "✅ Booking created (pending admin confirmation)!",
        "booking_confirmed_client": "✅ Your booking is confirmed!",
        "slot_unavailable": "❌ This time slot is already booked. Please choose another time.",
        "booking_creating": "⏳ Creating booking...",
        "booking_request_in_progress": "Request is already being processed.",
        "session_expired": "This booking session expired. Please start again.",
        "error_generic": "❌ Something went wrong. Please try again.",
        "cancel_too_late": "❌ Cancellation is no longer allowed for this booking.",
        "media_send_failed": "⚠️ Could not load media. The service card is still available.",
        "preview_not_available": "No media uploaded for this service yet.",
        "message_send_failed": "❌ Could not deliver the message to the client.",
        "unsupported_language": "Unsupported language.",
        "no_services": "No services available yet. Please try again later.",
        "no_dates": "No available dates for this service.",
        "no_slots": "No available time slots",
        "no_bookings": "You have no active bookings.",
        "no_bookings_yet": "You have no bookings yet.",
        "your_bookings": "Your bookings:",
        "main_menu": "Main menu:",
        "cancelled": "Cancelled.",
        "booking_cancelled": "Booking cancelled.",
        "contact_admin_msg": "Contact admin: @{username}",
        "contact_not_configured": "Admin contact is not configured yet.",
        "support_menu_title": "🆘 Support",
        "support_menu_text": "Choose what you need help with:",
        "support_new_request": "📝 New request",
        "support_my_requests": "📋 My requests",
        "support_topic_booking": "📅 Booking question",
        "support_topic_reschedule": "🔁 Reschedule booking",
        "support_topic_cancel": "❌ Cancel booking",
        "support_topic_payment": "💳 Payment",
        "support_topic_other": "💬 Other",
        "support_choose_topic": "Choose request topic:",
        "support_choose_booking": "Choose the booking this request is about:",
        "support_skip_booking": "Skip booking selection",
        "support_message_prompt": (
            "Write a message to the admin.\n"
            "You can include details: preferred time, payment question, or what should be changed in the booking."
        ),
        "support_request_sent": "✅ Your message has been sent to the admin. We will reply to you here in the bot.",
        "support_admin_new_request": (
            "📩 New support request\n"
            "Topic: {topic}\n"
            "Client: {client_name}\n"
            "Telegram ID: {telegram_id}\n"
            "Username: {username}\n\n"
            "Message:\n{text}"
        ),
        "support_booking_line": "Booking: #{booking_id} {date_time}",
        "support_my_requests_empty": "You have no support requests yet.",
        "support_request_detail": "Request #{request_id}",
        "support_detail_topic": "Topic",
        "support_detail_status": "Status",
        "support_detail_message": "Your message",
        "support_detail_admin_reply": "Admin reply",
        "support_status_open": "open",
        "support_status_replied": "replied",
        "support_status_closed": "closed",
        "support_back_to_menu": "🔙 Back",
        "support_back_to_requests": "🔙 Back to requests",
        "support_back_btn": "🔙 Back",
        "support_username_not_provided": "not provided",
        "support_reply_button": "↩️ Reply",
        "support_close_button": "✅ Close",
        "support_open_profile_button": "👤 Open Telegram profile",
        "support_reply_prompt": "Enter your reply to the client.",
        "support_reply_sent": "✅ Reply sent to client.",
        "support_admin_reply": "📩 Admin reply:\n{text}",
        "support_closed": "✅ Message closed.",
        "support_empty_error": "❌ Message cannot be empty.",
        "support_too_long": "❌ Message is too long. Maximum 3000 characters.",
        "support_no_admin": "❌ Admin is not configured yet. Please try again later.",
        "support_send_failed": "❌ Could not send your message. Please try again later.",
        "support_reply_failed": "❌ Could not send reply to the client. The client may have blocked the bot.",
        "language_choose": "Choose language:",
        "language_set": "Language updated.",
        "access_denied": "Access denied.",
        "confirm_btn": "✅ Confirm",
        "not_found": "Not found",
        "admin_panel": "Admin panel:",
        "admin_services": "🛠 Services",
        "admin_working_hours": "🕘 Working hours",
        "admin_unavailable": "🚫 Unavailable dates",
        "admin_bookings": "📒 Bookings",
        "admin_calendar": "📆 Calendar settings",
        "admin_settings": "⚙️ Bot settings",
        "services_management": "Services management:",
        "services_list": "Services:",
        "add_service": "➕ Add service",
        "enter_service_name": "Enter service name:",
        "enter_description": "Enter description (or send - to skip):",
        "enter_duration": "Enter duration in minutes (e.g. 60):",
        "svc_duration_title": "⏱ Service duration",
        "svc_duration_choose": "Choose duration:",
        "svc_duration_manual": "✏️ Enter manually",
        "enter_duration_manual": "Enter duration in minutes, for example 60",
        "svc_duration_invalid": "❌ Enter a number from 5 to 1440 minutes.",
        "duration_selected": "Duration: {duration}",
        "svc_buffer_title": "🚗 Travel or break time",
        "svc_buffer_choose": (
            "How much time should be left after this service before the next booking?\n"
            "For example, if the service ends at 10:00 and buffer is 30 minutes, "
            "the next booking will be available from 10:30."
        ),
        "buffer_explanation": (
            "Buffer is time after a service for travel, rest, or preparation.\n"
            "Clients will not be able to book immediately after this service."
        ),
        "no_buffer": "No buffer",
        "buffer_after_service": "Buffer after service: {buffer}",
        "buffer_saved": "Buffer after service: {buffer}",
        "edit_buffer": "🚗 Buffer",
        "svc_buffer_manual": "✏️ Enter manually",
        "enter_buffer_manual": "Enter buffer time in minutes (0 for none), for example 30",
        "invalid_buffer_minutes": "❌ Enter a number from 0 to 1440 minutes.",
        "buffer_client_note": "Travel/preparation time is included in schedule",
        "service_requires_location": "📍 Client address: {status}",
        "service_comment_setting": "💬 Client comment: {status}",
        "toggle_location_request": "📍 Client address",
        "client_comment_toggle": "💬 Client comment",
        "client_comment_enabled": "✅ Client comment request enabled for this service.",
        "client_comment_disabled": "❌ Client comment request disabled for this service.",
        "location_request_enabled": "✅ Client address request enabled for this service.",
        "location_request_disabled": "❌ Client address request disabled for this service.",
        "service_media": "🖼 Media",
        "service_media_title": "🖼 Service media",
        "add_photo": "➕ Add photo",
        "add_video": "➕ Add video",
        "choose_cover": "⭐ Choose cover",
        "delete_media": "🗑 Delete media",
        "preview_media": "👁 Preview",
        "show_to_clients": "✅ Show to clients",
        "hide_from_clients": "❌ Hide from clients",
        "media_enabled": "enabled",
        "media_disabled": "disabled",
        "photos_count": "🖼 Photos: {count}",
        "videos_count": "🎬 Videos: {count}",
        "client_media_display": "👁 Client display: {status}",
        "cover_selected": "Cover: yes",
        "cover_not_selected": "Cover: no",
        "no_media": "No media yet.",
        "max_media_reached": "❌ Maximum allowed: 5 photos and 1 video.",
        "view_photos": "🖼 View photos",
        "view_video": "🎬 View video",
        "media_photo_n": "Photo {n}",
        "media_video_n": "Video {n}",
        "upload_photo_prompt": "Send a photo for this service.",
        "upload_video_prompt": "Send a video for this service.",
        "media_added": "✅ Media added.",
        "media_deleted": "✅ Media deleted.",
        "cover_set": "✅ Cover photo updated.",
        "media_display_enabled": "✅ Media display enabled for clients.",
        "media_display_disabled": "❌ Media display disabled for clients.",
        "no_photos_for_cover": "Add photos first to choose a cover.",
        "enter_location": (
            "📍 Enter address or meeting location\n"
            "Example:\n"
            "London, Baker Street 10"
        ),
        "enter_comment": (
            "Any comment for the booking?\n"
            "For example: entrance, floor, door code, or special request.\n"
            "You can press “Skip”."
        ),
        "ask_comment_prompt": "Any comment for the booking?",
        "comment_optional_hint": "You can press “Skip” if you have nothing to add.",
        "comment_not_provided": "not provided",
        "service_comment_label": "💬 Comment: {comment}",
        "skip": "⏭ Skip",
        "location_label": "📍 Location: {location}",
        "client_address_label": "🏠 Client address: {location}",
        "service_location_label": "📍 Service location: {title}",
        "address_label": "Address: {address}",
        "service_locations_count": "📍 Service locations: {count}",
        "service_locations_btn": "📍 Locations",
        "service_locations": "📍 Service locations",
        "service_locations_intro": (
            "Here you can add addresses or places where this service is provided.\n"
            "The client will choose one location when booking."
        ),
        "add_location": "➕ Add location",
        "location_name_prompt": (
            "Enter location name, for example:\n"
            "Office on Arbat"
        ),
        "location_address_prompt": (
            "Enter address or place description.\n"
            "Example:\n"
            "Moscow, Arbat 10, office 5\n"
            "You can press “Skip”."
        ),
        "location_description_prompt": (
            "Add a note for this location?\n"
            "Example: entrance from courtyard, 3rd floor, Zoom link will be sent later.\n"
            "You can press “Skip”."
        ),
        "location_saved": "✅ Location saved.",
        "location_detail": "📍 Service location",
        "location_name_label": "Name: {title}",
        "location_address_label": "Address: {address}",
        "location_description_label": "Description: {description}",
        "location_status_label": "Status: {status}",
        "location_active": "active",
        "location_hidden_status": "hidden",
        "edit_location_name": "✏️ Edit name",
        "edit_location_address": "✏️ Edit address",
        "edit_location_description": "✏️ Edit description",
        "hide_location": "❌ Hide",
        "show_location": "✅ Show",
        "delete_location": "🗑 Delete",
        "back_to_locations": "🔙 Back to locations",
        "back_to_service": "🔙 Back to service",
        "location_hidden": "✅ Location hidden.",
        "location_restored": "✅ Location shown.",
        "location_deleted": "✅ Location deleted.",
        "location_hidden_has_bookings": (
            "✅ Location hidden. Existing bookings keep the saved location details."
        ),
        "location_delete_confirm": "⚠️ Delete this location?",
        "location_delete_confirm_yes": "✅ Yes, delete",
        "location_delete_confirm_no": "❌ Cancel",
        "choose_service_location": "📍 Choose service location",
        "no_locations": (
            "No locations added yet. If no locations are added, the client will not choose a location."
        ),
        "comment_label": "💬 Comment: {comment}",
        "not_provided": "not provided",
        "new_booking_admin": "📩 New booking",
        "enter_price": "Enter price (0 for free):",
        "enter_number": "Enter a number.",
        "service_created": "✅ Service created: {name}",
        "service_deleted": "✅ Service deleted.",
        "service_archived": "✅ Service archived.",
        "service_has_bookings_archived": "✅ Service archived. Existing bookings are preserved.",
        "service_delete_confirm": (
            "⚠️ Delete service?\n\n"
            "If this service already has bookings, it will be hidden from new clients, "
            "but old bookings will be preserved."
        ),
        "service_delete_confirm_yes": "✅ Yes, delete/archive",
        "service_delete_confirm_no": "❌ Cancel",
        "service_delete_cancelled": "Deletion cancelled.",
        "service_archived_label": "Archived",
        "services_active_title": "Active services:",
        "services_no_active": "No active services.",
        "services_disabled_button": "🔴 Disabled services",
        "services_disabled_title": "🔴 Disabled services",
        "services_disabled_intro": "These services are hidden from clients but not deleted.",
        "services_no_disabled": "No disabled services.",
        "back_to_disabled_services": "🔙 Back to disabled services",
        "move_to_archive": "📦 Move to archive",
        "archived_services": "📦 Archived services",
        "archive_empty": "Archive is empty.",
        "archived_service_detail": (
            "📦 Archived service\n\n"
            "Name: {name}\n"
            "Duration: {duration} min.\n"
            "Price: {price}\n"
            "Old bookings: {bookings_count}"
        ),
        "restore_service": "♻️ Restore service",
        "service_restored": "✅ Service restored.",
        "delete_permanently": "🗑 Delete permanently",
        "delete_permanently_confirm": (
            "⚠️ Delete service permanently?\n"
            "This action cannot be undone."
        ),
        "delete_permanently_confirm_yes": "✅ Yes, delete permanently",
        "delete_permanently_confirm_no": "❌ Cancel",
        "delete_permanently_success": "✅ Service permanently deleted.",
        "delete_permanently_blocked_has_bookings": (
            "❌ Cannot delete permanently because this service has old bookings.\n"
            "The service will remain in archive to preserve booking history."
        ),
        "back_to_archive": "🔙 Back to archive",
        "back_to_services": "🔙 Back to services",
        "back_to_admin_panel": "🔙 Back to admin panel",
        "archived_services_intro": (
            "These services are hidden from clients.\n"
            "Old bookings are preserved."
        ),
        "service_not_found": "Service not found.",
        "updated": "Updated.",
        "edit_name": "✏️ Edit name",
        "edit_description": "✏️ Edit description",
        "edit_duration": "⏱ Duration",
        "edit_price": "💰 Price",
        "enable_service": "🟢 Enable",
        "disable_service": "🔴 Disable",
        "service_list_disabled": "🔴 {name} (disabled)",
        "service_disabled_success": 'Service disabled and moved to "Disabled services".',
        "service_enabled_success": "Service enabled and available in active services again.",
        "service_unavailable_booking": "This service is currently unavailable for booking.",
        "delete_service": "🗑 Delete",
        "enter_new_name": "Enter new name:",
        "enter_new_description": "Enter new description:",
        "enter_new_duration": "Enter new duration (minutes):",
        "enter_new_price": "Enter new price:",
        "enter_value": "Enter value:",
        "duration_label": "Duration: {duration}",
        "price_label": "Price: {price}",
        "price_free": "Free",
        "active_label": "Active: {value}",
        "yes": "yes",
        "no": "no",
        "working_hours_current": "Current working hours:",
        "working_hours_set": "Set hours for {day}\nEnter start time (HH:MM):",
        "working_hours_updated": "Working hours updated for {day}.",
        "invalid_time": "Invalid time. Use HH:MM",
        "invalid_time_short": "Invalid time.",
        "enter_end_time": "Enter end time (HH:MM):",
        "unavailable_dates_title": "Unavailable dates:",
        "unavailable_none": "(none)",
        "unavailable_hint": (
            "\n\nSend a date (DD.MM.YYYY) to mark unavailable, or send range as:\n"
            "DATE START-END for time block"
        ),
        "invalid_date": "Invalid date.",
        "invalid_date_format": "Invalid date. Use DD.MM.YYYY",
        "invalid_time_range": "Invalid time range.",
        "blocked_range": "Blocked {date} {start}-{end}",
        "date_marked_unavailable": "Date {date} marked unavailable.",
        "unav_title": "🚫 Unavailable dates",
        "unav_intro": (
            "Here you can block full days or specific time ranges.\n"
            "Clients will not be able to book these dates and times."
        ),
        "unav_tomorrow": "⚡ Tomorrow unavailable",
        "unav_next7": "⚡ Next 7 days unavailable",
        "unav_block_day": "📅 Block specific day",
        "unav_block_time": "🕘 Block time on specific day",
        "unav_list": "📋 Unavailable list",
        "unav_tomorrow_confirm_text": (
            "🚫 Make tomorrow unavailable?\n"
            "Clients will not be able to book tomorrow."
        ),
        "unav_tomorrow_confirm_yes": "✅ Yes, block tomorrow",
        "unav_next7_confirm_text": (
            "🚫 Make the next 7 days unavailable?\n"
            "Clients will not be able to book the next 7 days.\n"
            "Your normal weekly schedule will not be changed."
        ),
        "unav_next7_confirm_yes": "✅ Yes, block 7 days",
        "unav_confirm_yes": "✅ Yes",
        "unav_confirm_no": "❌ Cancel",
        "unav_tomorrow_done": "✅ Tomorrow is now unavailable for booking.",
        "unav_next7_done": "✅ Next 7 days are now unavailable for booking.",
        "unav_day_done": "✅ Day is now unavailable for booking.",
        "unav_time_done": "✅ Time range is now unavailable for booking.",
        "unav_date_today": "Today",
        "unav_date_tomorrow": "Tomorrow",
        "unav_date_after_tomorrow": "Day after tomorrow",
        "unav_date_plus": "+{days} days",
        "unav_enter_date_manual": "✏️ Enter date manually",
        "unav_enter_date_prompt": "Enter date in DD.MM.YYYY format\nExample: 25.06.2026",
        "unav_invalid_date": "❌ Invalid date. Use DD.MM.YYYY and a date that is not in the past.",
        "unav_day_confirm_text": "🚫 Block this day for booking?\n{date}",
        "unav_day_confirm_yes": "✅ Yes, block day",
        "unav_full_day": "Full day",
        "unav_enter_time_manual": "✏️ Enter manually",
        "unav_enter_time_prompt": "Enter time in format:\n14:00-16:00",
        "unav_invalid_time": "❌ Invalid format. Example: 14:00-16:00",
        "unav_items_title": "📋 Unavailable time",
        "unav_items_empty": "No unavailable dates yet.",
        "unav_item_full_day": "🚫 {date} — full day",
        "unav_item_time": "🚫 {date} — {start}–{end}",
        "unav_item_full_day_btn": "🗑 {date} — full day",
        "unav_item_time_btn": "🗑 {date} — {start}–{end}",
        "unav_delete_confirm_text": "Delete this unavailable time?",
        "unav_delete_yes": "✅ Yes, delete",
        "unav_delete_done": "✅ Unavailable time deleted.",
        "upcoming_bookings": "Upcoming bookings:",
        "no_bookings_admin": "No bookings",
        "booking_confirmed_admin": "✅ Confirmed",
        "booking_cancelled_admin": "Booking #{id} cancelled.",
        "booking_already_cancelled_or_missing": "This booking is already cancelled or not found.",
        "confirm_booking_btn": "✅ Confirm booking",
        "cancel_booking_btn": "❌ Cancel booking",
        "my_booking_detail_title": "📋 Your booking",
        "my_booking_service_location": "Service location",
        "my_booking_client_address": "Client address",
        "my_booking_comment": "Comment",
        "reschedule_booking_btn": "🔁 Reschedule",
        "change_location_btn": "📍 Change location",
        "change_address_btn": "🏠 Change client address",
        "change_comment_btn": "💬 Change comment",
        "back_to_my_bookings": "🔙 Back to my bookings",
        "confirm_reschedule": (
            "Confirm reschedule?\n"
            "Old: {old_datetime}\n"
            "New: {new_datetime}"
        ),
        "confirm_reschedule_btn": "✅ Confirm reschedule",
        "booking_rescheduled": "✅ Booking rescheduled.",
        "service_location_changed": "✅ Service location changed.",
        "address_changed": "✅ Address changed.",
        "comment_changed": "✅ Comment changed.",
        "reschedule_too_late": (
            "❌ This booking can no longer be rescheduled. Please contact the admin."
        ),
        "booking_not_editable": "This booking can no longer be edited.",
        "booking_changed_admin": (
            "🔁 Booking changed by client\n"
            "Service: {service}\n"
            "Client: {client_name}\n"
            "Phone: {phone}\n"
            "Old: {old_value}\n"
            "New: {new_value}"
        ),
        "enter_new_address": "Enter new address or meeting location",
        "enter_new_comment": (
            "Enter a new comment or press “Skip” to clear it."
        ),
        "message_client_btn": "✉️ Message client",
        "enter_message_client": "Enter message for client:",
        "message_sent": "Message sent.",
        "message_from_admin": "📩 Message from admin:\n{text}",
        "calendar_settings_title": "Google Calendar settings:",
        "calendar_settings_body": (
            "Enabled (env): {env_enabled}\n"
            "Enabled (DB): {db_enabled}\n"
            "Calendar ID: {calendar_id}\n"
            "Refresh token stored: {token_stored}\n\n"
            "Configure GOOGLE_* vars in .env. Store refresh token via bot setting key "
            "'google_refresh_token' or in calendar_settings table."
        ),
        "settings_calendar_btn": "📅 Google Calendar",
        "settings_calendar_title": "📅 Google Calendar",
        "settings_calendar_body": (
            "Status: {status}\n"
            "Calendar ID: {calendar_id}\n"
            "Event sync: {sync}\n"
            "Env (.env): {env_status}"
        ),
        "settings_calendar_toggle_on": "✅ Disable Google Calendar",
        "settings_calendar_toggle_off": "❌ Enable Google Calendar",
        "settings_calendar_toggle_env_off": "❌ Disabled in .env",
        "settings_calendar_test_btn": "📋 Test connection",
        "settings_calendar_env_note": "Set GOOGLE_CALENDAR_ENABLED=true in .env to allow sync.",
        "calendar_test_checking": "Checking Google Calendar connection...",
        "calendar_test_disabled_env": "Google Calendar is disabled in .env (GOOGLE_CALENDAR_ENABLED=false).",
        "calendar_test_disabled_db": "Google Calendar sync is disabled in bot settings.",
        "calendar_test_missing_credentials": "Missing credentials: {missing}",
        "calendar_test_client_build_failed": "Could not build Google Calendar client. Check packages and credentials.",
        "calendar_test_success": "✅ Connection OK. Calendar: {detail}",
        "calendar_test_failed": "❌ Connection failed: {detail}",
        "calendar_test_invalid_token": "❌ Invalid or expired refresh token. Re-authorize OAuth.",
        "calendar_test_permission_denied": "❌ Permission denied. Check OAuth scopes and calendar access.",
        "calendar_test_invalid_calendar_id": "❌ Calendar not found: {detail}",
        "calendar_enabled_msg": "✅ Google Calendar sync enabled.",
        "calendar_disabled_msg": "❌ Google Calendar sync disabled.",
        "calendar_event_title": "Booking: {service_name}",
        "calendar_label_client": "Client: {value}",
        "calendar_label_phone": "Phone: {value}",
        "calendar_label_service": "Service: {value}",
        "calendar_label_datetime": "Date/time: {value}",
        "calendar_label_address": "Address: {value}",
        "calendar_label_service_location": "Service location: {title}",
        "calendar_label_service_location_address": "Location address: {value}",
        "calendar_label_comment": "Comment: {value}",
        "calendar_label_booking_id": "Booking ID: {value}",
        "bot_settings_title": "Bot settings — send in format:",
        "bot_settings_format": "KEY=VALUE",
        "bot_settings_keys": (
            "Available keys:\n"
            "auto_confirm\n"
            "contact_admin_username\n"
            "reminders_enabled\n"
            "client_reminder_1_minutes\n"
            "client_reminder_2_minutes\n"
            "admin_reminder_minutes\n"
            "reminder_test_mode\n"
            "test_client_reminder_minutes\n"
            "test_admin_reminder_minutes"
        ),
        "bot_settings_auto_confirm": "auto_confirm=true — bookings confirmed immediately",
        "settings_saved": "✅ Setting {key} saved.",
        "invalid_format": "Use KEY=VALUE format",
        "status_pending": "pending",
        "status_confirmed": "confirmed",
        "status_cancelled": "cancelled",
        "status_completed": "completed",
        "booking_status_line": "Status: {status}",
        "reminder_client": (
            "🔔 Appointment reminder\n"
            "Service: {service_name}\n"
            "Date and time: {date_time}\n"
            "We are waiting for you!"
        ),
        "reminder_admin": (
            "🔔 Upcoming client booking\n"
            "Service: {service_name}\n"
            "Date and time: {date_time}\n"
            "Client: {client_name}\n"
            "Phone: {client_phone}"
            "{location_block}{comment_block}"
        ),
        "reminder_admin_location": "\n📍 Client address: {location}",
        "reminder_admin_service_location": "\n📍 Service location: {title}",
        "reminder_admin_service_location_address": "\nAddress: {address}",
        "reminder_admin_comment": "\n💬 Comment: {comment}",
        "phone_not_provided": "—",
        "settings_menu_title": "⚙️ Bot settings",
        "settings_menu_body": (
            "Current settings:\n"
            "✅ Auto-confirm: {auto_confirm}\n"
            "🔔 Reminders: {reminders}\n"
            "🌐 Language: {language}\n"
            "📞 Admin contact: {contact}"
        ),
        "label_enabled": "enabled",
        "label_disabled": "disabled",
        "lang_name_ru": "Russian",
        "lang_name_en": "English",
        "settings_auto_confirm_btn_on": "✅ Auto-confirm",
        "settings_auto_confirm_btn_off": "❌ Auto-confirm",
        "settings_reminders_btn": "🔔 Reminders",
        "settings_language_btn": "🌐 Language",
        "settings_enabled_languages_btn": "🌐 Available languages",
        "settings_enabled_languages_title": "🌐 Available languages",
        "settings_enabled_languages_body": (
            "Current: {current}\n\n"
            "Choose which languages are available to users."
        ),
        "enabled_languages_mode_ru": "Russian",
        "enabled_languages_mode_en": "English",
        "enabled_languages_mode_both": "Russian + English",
        "enabled_languages_btn_ru": "🇷🇺 Russian only",
        "enabled_languages_btn_en": "🇬🇧 English only",
        "enabled_languages_btn_both": "🇷🇺🇬🇧 Russian + English",
        "enabled_languages_saved": "✅ Available languages updated.",
        "language_switching_disabled": "Language switching is disabled. This bot is available only in English.",
        "settings_contact_btn": "📞 Admin contact",
        "start_screen_btn": "👋 Start screen",
        "start_screen_menu_title": "👋 Start screen",
        "start_screen_menu_body": (
            "Text RU: {text_ru}\n"
            "Text EN: {text_en}\n"
            "Photo RU: {photo_ru}\n"
            "Photo EN: {photo_en}"
        ),
        "start_screen_menu_body_single": "Text: {text}\nPhoto: {photo}",
        "start_screen_edit_text_btn": "✏️ Edit text",
        "start_screen_upload_photo_btn": "🖼 Upload photo",
        "start_screen_toggle_photo_on": "❌ Disable photo",
        "start_screen_toggle_photo_off": "✅ Enable photo",
        "start_screen_preview_btn": "👁 Preview",
        "start_screen_text_custom": "custom",
        "start_screen_text_default": "default",
        "start_screen_photo_set": "set",
        "start_screen_photo_not_set": "not set",
        "start_screen_edit_ru_btn": "✏️ Edit RU text",
        "start_screen_edit_en_btn": "✏️ Edit EN text",
        "start_screen_upload_ru_btn": "🖼 Upload RU photo",
        "start_screen_upload_en_btn": "🖼 Upload EN photo",
        "start_screen_toggle_ru_on": "❌ Disable RU photo",
        "start_screen_toggle_ru_off": "✅ Enable RU photo",
        "start_screen_toggle_en_on": "❌ Disable EN photo",
        "start_screen_toggle_en_off": "✅ Enable EN photo",
        "start_screen_preview_ru_btn": "👁 Preview RU",
        "start_screen_preview_en_btn": "👁 Preview EN",
        "start_screen_reset_btn": "♻️ Reset to default",
        "start_screen_back_settings_btn": "🔙 Back to settings",
        "start_screen_prompt_ru": "Send new /start text in Russian.",
        "start_screen_prompt_en": "Send new /start text in English.",
        "start_screen_prompt_photo_ru": "Send a photo for the Russian start screen.",
        "start_screen_prompt_photo_en": "Send a photo for the English start screen.",
        "start_screen_not_photo": "❌ Please send a photo.",
        "start_screen_text_too_long": "❌ Text is too long. Maximum 1000 characters.",
        "start_screen_text_empty": "❌ Text cannot be empty.",
        "start_screen_upload_first_ru": "Upload RU photo first.",
        "start_screen_upload_first_en": "Upload EN photo first.",
        "start_screen_reset_confirm": "Reset start screen to default?",
        "start_screen_reset_yes": "✅ Yes, reset",
        "start_screen_reset_no": "❌ Cancel",
        "start_screen_photo_saved_ru": "✅ RU start photo saved.",
        "start_screen_photo_saved_en": "✅ EN start photo saved.",
        "settings_advanced_btn": "⚙️ Advanced settings",
        "settings_back_admin_btn": "🔙 Back to admin panel",
        "settings_back_settings_btn": "🔙 Back to settings",
        "settings_back_reminders_btn": "🔙 Back",
        "settings_back_test_btn": "🔙 Back",
        "auto_confirm_enabled_msg": "✅ Auto-confirm enabled.",
        "auto_confirm_disabled_msg": "❌ Auto-confirm disabled.",
        "settings_reminders_title": "🔔 Reminder settings",
        "settings_reminders_body": (
            "Status: {status}\n"
            "Client: {client1} and {client2} before\n"
            "Admin: {admin} before\n"
            "Test mode: {test_mode}"
        ),
        "settings_reminders_toggle_on": "✅ Disable reminders",
        "settings_reminders_toggle_off": "❌ Enable reminders",
        "settings_reminder_client1_btn": "⏰ First client reminder",
        "settings_reminder_client2_btn": "⏰ Second client reminder",
        "settings_reminder_admin_btn": "👤 Admin reminder",
        "settings_reminder_test_btn": "🧪 Test mode",
        "settings_enter_manual_btn": "✏️ Enter manually",
        "settings_enter_minutes_prompt": "Enter time in minutes, for example 60",
        "settings_invalid_minutes": "Enter a number from 1 to 10080.",
        "settings_time_saved": "✅ Saved.",
        "settings_test_title": "🧪 Reminder test mode",
        "settings_test_body": (
            "This mode is only for testing.\n"
            "For example, create a booking 6–10 minutes ahead to quickly test reminders.\n\n"
            "Status: {status}\n"
            "Client: {client} before\n"
            "Admin: {admin} before"
        ),
        "settings_test_toggle_on": "✅ Disable test mode",
        "settings_test_toggle_off": "❌ Enable test mode",
        "settings_test_client_section": "👤 Client reminder time",
        "settings_test_admin_section": "👨‍💼 Admin reminder time",
        "settings_contact_title": "📞 Admin contact",
        "settings_contact_body": "Current contact: {contact}",
        "settings_contact_not_set": "not set",
        "settings_contact_edit_btn": "✏️ Change contact",
        "settings_contact_clear_btn": "❌ Clear contact",
        "settings_contact_prompt": "Send username like @username:",
        "settings_contact_saved": "✅ Contact saved.",
        "settings_contact_cleared": "✅ Contact cleared.",
        "settings_contact_invalid": "Use @username format.",
        "settings_language_title": "🌐 Language",
        "settings_advanced_title": "⚙️ Advanced settings",
        "settings_advanced_body": (
            "This section is only for developer/manual configuration.\n"
            "Usually you do not need system keys.\n"
            "For normal setup, use buttons:\n"
            "✅ Auto-confirm\n"
            "🔔 Reminders\n"
            "🌐 Language\n"
            "📞 Admin contact"
        ),
        "settings_advanced_keys_title": "System keys:",
        "settings_advanced_enter_btn": "✏️ Enter setting manually",
        "settings_advanced_show_keys_btn": "📋 Show system keys",
        "settings_back_advanced_btn": "🔙 Back to advanced settings",
        "settings_advanced_manual_prompt": (
            "Send setting in format:\n"
            "key=value\n\n"
            "Example:\n"
            "auto_confirm=true"
        ),
        "settings_advanced_keys_list": (
            "auto_confirm — automatically confirm bookings\n"
            "contact_admin_username — admin contact username\n"
            "reminders_enabled — enable or disable reminders\n"
            "client_reminder_1_minutes — first client reminder, in minutes\n"
            "client_reminder_2_minutes — second client reminder, in minutes\n"
            "admin_reminder_minutes — admin reminder, in minutes\n"
            "reminder_test_mode — reminder test mode\n"
            "test_client_reminder_minutes — test client reminder, in minutes\n"
            "test_admin_reminder_minutes — test admin reminder, in minutes"
        ),
        "time_preset_1440": "24 hours",
        "time_preset_720": "12 hours",
        "time_preset_360": "6 hours",
        "time_preset_180": "3 hours",
        "time_preset_120": "2 hours",
        "time_preset_60": "1 hour",
        "time_preset_30": "30 minutes",
        "time_preset_15": "15 minutes",
        "time_preset_10": "10 minutes",
        "time_preset_5": "5 minutes",
        "time_preset_3": "3 minutes",
        "time_preset_1": "1 minute",
        "duration_days": "{n} days",
        "duration_hours": "{n} hours",
        "duration_minutes": "{n} minutes",
        "duration_one_hour": "1 hour",
        "duration_n_hours": "{n} hours",
        "duration_n_minutes": "{n} min",
        "duration_hours_minutes": "{hours} {minutes_part}",
        "weekday_0": "Monday",
        "weekday_1": "Tuesday",
        "weekday_2": "Wednesday",
        "weekday_3": "Thursday",
        "weekday_4": "Friday",
        "weekday_5": "Saturday",
        "weekday_6": "Sunday",
        "weekday_short_0": "Mon",
        "weekday_short_1": "Tue",
        "weekday_short_2": "Wed",
        "weekday_short_3": "Thu",
        "weekday_short_4": "Fri",
        "weekday_short_5": "Sat",
        "weekday_short_6": "Sun",
        "wh_title": "🕘 Working hours",
        "wh_current_schedule": "Current schedule:",
        "wh_day_line_working": "{day}: {start}–{end}",
        "wh_day_line_off": "{day}: day off",
        "wh_day_detail_working": "🕘 {day}\nStatus: working day\nTime: {start}–{end}",
        "wh_day_detail_off": "🕘 {day}\nStatus: day off",
        "wh_toggle_to_off": "❌ Day off",
        "wh_toggle_to_on": "✅ Working day",
        "wh_change_time": "🕘 Change time",
        "wh_back_schedule": "🔙 Back to schedule",
        "wh_choose_time": "Choose working hours:",
        "wh_enter_manual": "✏️ Enter manually",
        "wh_manual_prompt": "Enter working hours in format:\n09:00-18:00",
        "wh_invalid_time_format": "❌ Invalid format. Example: 09:00-18:00",
        "wh_updated": "Schedule updated.",
        "wh_quick_presets": "⚡ Quick presets",
        "wh_week_off": "🚫 Make whole week unavailable",
        "wh_presets_title": "⚡ Quick schedule presets\nChoose a ready-made option:",
        "wh_preset_monfri_9_18": "Mon–Fri 09:00–18:00",
        "wh_preset_monfri_10_19": "Mon–Fri 10:00–19:00",
        "wh_preset_everyday_10_20": "Every day 10:00–20:00",
        "wh_preset_satsun_off": "Sat–Sun days off",
        "wh_preset_everyday_off": "Every day off",
        "wh_preset_applied": "Preset applied.",
        "wh_week_off_confirm_text": (
            "🚫 Make next week unavailable?\n"
            "Clients will not be able to book for the next 7 days.\n"
            "Your normal weekly schedule will not be changed."
        ),
        "wh_week_off_confirm_yes": "✅ Yes, make unavailable",
        "wh_week_off_confirm_no": "❌ Cancel",
        "wh_week_off_done": "Next 7 days marked unavailable.",
        "wh_on": "on",
        "wh_off": "off",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в бот записи!",
        "welcome_sub": "Запишитесь на услугу, посмотрите записи или свяжитесь с администратором.",
        "support_line": "\nПоддержка: @{username}",
        "book_appointment": "📅 Записаться",
        "my_bookings": "📋 Мои записи",
        "contact_admin": "📞 Связаться с админом",
        "language": "🌐 Язык",
        "admin_menu": "⚙️ Админ-меню",
        "back_main": "🔙 Назад в главное меню",
        "back": "◀️ Назад",
        "cancel": "❌ Отмена",
        "choose_service": "Выберите услугу:",
        "choose_date": "Выберите дату:",
        "searching_dates": "⏳ Ищу свободные даты...",
        "dates_load_timeout": "Не удалось быстро загрузить свободные даты. Попробуйте ещё раз.",
        "choose_time": "Выберите время:",
        "enter_name": "Введите ваше имя:",
        "enter_phone": "Введите номер телефона:",
        "selected": "Выбрано: {dt}",
        "confirm_booking": "Подтвердите запись:",
        "label_service": "Услуга",
        "label_datetime": "Дата и время",
        "label_name": "Имя",
        "label_phone": "Телефон",
        "booking_confirmed": "✅ Запись подтверждена!",
        "booking_created_pending": "✅ Запись создана (ожидает подтверждения админа)!",
        "booking_confirmed_client": "✅ Ваша запись подтверждена!",
        "slot_unavailable": "❌ Это время уже занято. Выберите другое время.",
        "booking_creating": "⏳ Создаю запись...",
        "booking_request_in_progress": "Запрос уже обрабатывается.",
        "session_expired": "Сессия записи истекла. Начните заново.",
        "error_generic": "❌ Что-то пошло не так. Попробуйте ещё раз.",
        "cancel_too_late": "❌ Отмена этой записи уже недоступна.",
        "media_send_failed": "⚠️ Не удалось загрузить медиа. Карточка услуги всё равно доступна.",
        "preview_not_available": "Медиа для этой услуги пока не добавлены.",
        "message_send_failed": "❌ Не удалось отправить сообщение клиенту.",
        "unsupported_language": "Язык не поддерживается.",
        "no_services": "Услуги пока недоступны. Попробуйте позже.",
        "no_dates": "Нет доступных дат для этой услуги.",
        "no_slots": "Нет свободных слотов",
        "no_bookings": "У вас нет активных записей.",
        "no_bookings_yet": "У вас пока нет записей.",
        "your_bookings": "Ваши записи:",
        "main_menu": "Главное меню:",
        "cancelled": "Отменено.",
        "booking_cancelled": "Запись отменена.",
        "contact_admin_msg": "Связаться с админом: @{username}",
        "contact_not_configured": "Контакт администратора не настроен.",
        "support_menu_title": "🆘 Поддержка",
        "support_menu_text": "Выберите, с чем нужна помощь:",
        "support_new_request": "📝 Новое обращение",
        "support_my_requests": "📋 Мои обращения",
        "support_topic_booking": "📅 Вопрос по записи",
        "support_topic_reschedule": "🔁 Перенести запись",
        "support_topic_cancel": "❌ Отменить запись",
        "support_topic_payment": "💳 Оплата",
        "support_topic_other": "💬 Другое",
        "support_choose_topic": "Выберите тему обращения:",
        "support_choose_booking": "Выберите запись, по которой нужен вопрос:",
        "support_skip_booking": "Пропустить выбор записи",
        "support_message_prompt": (
            "Напишите сообщение для администратора.\n"
            "Можно указать детали: удобное время, вопрос по оплате, что нужно изменить в записи."
        ),
        "support_request_sent": "✅ Ваше сообщение отправлено администратору. Мы ответим вам здесь в боте.",
        "support_admin_new_request": (
            "📩 Новое обращение\n"
            "Тема: {topic}\n"
            "Клиент: {client_name}\n"
            "Telegram ID: {telegram_id}\n"
            "Username: {username}\n\n"
            "Сообщение:\n{text}"
        ),
        "support_booking_line": "Запись: #{booking_id} {date_time}",
        "support_my_requests_empty": "У вас пока нет обращений.",
        "support_request_detail": "Обращение #{request_id}",
        "support_detail_topic": "Тема",
        "support_detail_status": "Статус",
        "support_detail_message": "Ваше сообщение",
        "support_detail_admin_reply": "Ответ администратора",
        "support_status_open": "открыто",
        "support_status_replied": "отвечено",
        "support_status_closed": "закрыто",
        "support_back_to_menu": "🔙 Назад",
        "support_back_to_requests": "🔙 Назад к обращениям",
        "support_back_btn": "🔙 Назад",
        "support_username_not_provided": "не указан",
        "support_reply_button": "↩️ Ответить",
        "support_close_button": "✅ Закрыть",
        "support_open_profile_button": "👤 Открыть профиль Telegram",
        "support_reply_prompt": "Введите ответ клиенту.",
        "support_reply_sent": "✅ Ответ отправлен клиенту.",
        "support_admin_reply": "📩 Ответ администратора:\n{text}",
        "support_closed": "✅ Сообщение закрыто.",
        "support_empty_error": "❌ Сообщение не может быть пустым.",
        "support_too_long": "❌ Сообщение слишком длинное. Максимум 3000 символов.",
        "support_no_admin": "❌ Администратор пока не настроен. Попробуйте позже.",
        "support_send_failed": "❌ Не удалось отправить сообщение. Попробуйте позже.",
        "support_reply_failed": "❌ Не удалось отправить ответ клиенту. Возможно, клиент заблокировал бота.",
        "language_choose": "Выберите язык:",
        "language_set": "Язык изменён.",
        "access_denied": "Доступ запрещён.",
        "confirm_btn": "✅ Подтвердить",
        "not_found": "Не найдено",
        "admin_panel": "Админ-панель:",
        "admin_services": "🛠 Услуги",
        "admin_working_hours": "🕘 Рабочее время",
        "admin_unavailable": "🚫 Недоступные даты",
        "admin_bookings": "📒 Записи",
        "admin_calendar": "📆 Настройки календаря",
        "admin_settings": "⚙️ Настройки бота",
        "services_management": "Управление услугами:",
        "services_list": "Услуги:",
        "add_service": "➕ Добавить услугу",
        "enter_service_name": "Введите название услуги:",
        "enter_description": "Введите описание (или отправьте - чтобы пропустить):",
        "enter_duration": "Введите длительность в минутах (например, 60):",
        "svc_duration_title": "⏱ Длительность услуги",
        "svc_duration_choose": "Выберите длительность:",
        "svc_duration_manual": "✏️ Ввести вручную",
        "enter_duration_manual": "Введите длительность в минутах, например 60",
        "svc_duration_invalid": "❌ Введите число от 5 до 1440 минут.",
        "duration_selected": "Длительность: {duration}",
        "svc_buffer_title": "🚗 Время на дорогу или перерыв",
        "svc_buffer_choose": (
            "Сколько времени нужно оставить после этой услуги перед следующей записью?\n"
            "Например, если услуга заканчивается в 10:00, а буфер 30 минут, "
            "следующая запись будет доступна с 10:30."
        ),
        "buffer_explanation": (
            "Буфер — это время после услуги для дороги, отдыха или подготовки.\n"
            "Клиенты не смогут записаться сразу после этой услуги."
        ),
        "no_buffer": "Без буфера",
        "buffer_after_service": "Буфер после услуги: {buffer}",
        "buffer_saved": "Буфер после услуги: {buffer}",
        "edit_buffer": "🚗 Буфер",
        "svc_buffer_manual": "✏️ Ввести вручную",
        "enter_buffer_manual": "Введите буфер в минутах (0 — без буфера), например 30",
        "invalid_buffer_minutes": "❌ Введите число от 0 до 1440 минут.",
        "buffer_client_note": "Время на дорогу/подготовку учтено в расписании",
        "service_requires_location": "📍 Адрес клиента: {status}",
        "service_comment_setting": "💬 Комментарий клиента: {status}",
        "toggle_location_request": "📍 Адрес клиента",
        "client_comment_toggle": "💬 Комментарий клиента",
        "client_comment_enabled": "✅ Запрос комментария включен для этой услуги.",
        "client_comment_disabled": "❌ Запрос комментария выключен для этой услуги.",
        "location_request_enabled": "✅ Запрос адреса включен для этой услуги.",
        "location_request_disabled": "❌ Запрос адреса выключен для этой услуги.",
        "service_media": "🖼 Медиа",
        "service_media_title": "🖼 Медиа услуги",
        "add_photo": "➕ Добавить фото",
        "add_video": "➕ Добавить видео",
        "choose_cover": "⭐ Выбрать обложку",
        "delete_media": "🗑 Удалить медиа",
        "preview_media": "👁 Предпросмотр",
        "show_to_clients": "✅ Показывать клиенту",
        "hide_from_clients": "❌ Скрыть от клиента",
        "media_enabled": "включен",
        "media_disabled": "выключен",
        "photos_count": "🖼 Фото: {count}",
        "videos_count": "🎬 Видео: {count}",
        "client_media_display": "👁 Показ клиенту: {status}",
        "cover_selected": "Обложка: есть",
        "cover_not_selected": "Обложка: нет",
        "no_media": "Медиа пока нет.",
        "max_media_reached": "❌ Можно добавить максимум 5 фото и 1 видео.",
        "view_photos": "🖼 Смотреть фото",
        "view_video": "🎬 Смотреть видео",
        "media_photo_n": "Фото {n}",
        "media_video_n": "Видео {n}",
        "upload_photo_prompt": "Отправьте фото для этой услуги.",
        "upload_video_prompt": "Отправьте видео для этой услуги.",
        "media_added": "✅ Медиа добавлено.",
        "media_deleted": "✅ Медиа удалено.",
        "cover_set": "✅ Обложка обновлена.",
        "media_display_enabled": "✅ Показ медиа клиентам включен.",
        "media_display_disabled": "❌ Показ медиа клиентам выключен.",
        "no_photos_for_cover": "Сначала добавьте фото, чтобы выбрать обложку.",
        "enter_location": (
            "📍 Введите адрес или место встречи\n"
            "Например:\n"
            "Москва, ул. Пушкина 10"
        ),
        "enter_comment": (
            "Комментарий к записи?\n"
            "Например: подъезд, этаж, домофон или особые пожелания.\n"
            "Можно нажать «Пропустить»."
        ),
        "ask_comment_prompt": "Комментарий к записи?",
        "comment_optional_hint": "Можно нажать «Пропустить», если добавить нечего.",
        "comment_not_provided": "не указан",
        "service_comment_label": "💬 Комментарий: {comment}",
        "skip": "⏭ Пропустить",
        "location_label": "📍 Адрес: {location}",
        "client_address_label": "🏠 Адрес клиента: {location}",
        "service_location_label": "📍 Место проведения: {title}",
        "address_label": "Адрес: {address}",
        "service_locations_count": "📍 Места проведения: {count}",
        "service_locations_btn": "📍 Места проведения",
        "service_locations": "📍 Места проведения услуги",
        "service_locations_intro": (
            "Здесь можно добавить адреса или места, где проходит услуга.\n"
            "Клиент выберет одно место при записи."
        ),
        "add_location": "➕ Добавить место",
        "location_name_prompt": (
            "Введите название места, например:\n"
            "Офис на Арбате"
        ),
        "location_address_prompt": (
            "Введите адрес или описание места.\n"
            "Например:\n"
            "Москва, ул. Арбат 10, офис 5\n"
            "Можно нажать «Пропустить»."
        ),
        "location_description_prompt": (
            "Добавить комментарий к месту?\n"
            "Например: вход со двора, 3 этаж, Zoom-ссылка будет отправлена позже.\n"
            "Можно нажать «Пропустить»."
        ),
        "location_saved": "✅ Место сохранено.",
        "location_detail": "📍 Место проведения",
        "location_name_label": "Название: {title}",
        "location_address_label": "Адрес: {address}",
        "location_description_label": "Описание: {description}",
        "location_status_label": "Статус: {status}",
        "location_active": "активно",
        "location_hidden_status": "скрыто",
        "edit_location_name": "✏️ Изменить название",
        "edit_location_address": "✏️ Изменить адрес",
        "edit_location_description": "✏️ Изменить описание",
        "hide_location": "❌ Скрыть",
        "show_location": "✅ Показать",
        "delete_location": "🗑 Удалить",
        "back_to_locations": "🔙 Назад к местам",
        "back_to_service": "🔙 Назад к услуге",
        "location_hidden": "✅ Место скрыто.",
        "location_restored": "✅ Место показано.",
        "location_deleted": "✅ Место удалено.",
        "location_hidden_has_bookings": (
            "✅ Место скрыто. Существующие записи сохранят сохранённые данные о месте."
        ),
        "location_delete_confirm": "⚠️ Удалить это место?",
        "location_delete_confirm_yes": "✅ Да, удалить",
        "location_delete_confirm_no": "❌ Отмена",
        "choose_service_location": "📍 Выберите место проведения услуги",
        "no_locations": (
            "Пока нет добавленных мест. Если места не добавлены, клиент не будет выбирать место."
        ),
        "comment_label": "💬 Комментарий: {comment}",
        "not_provided": "не указан",
        "new_booking_admin": "📩 Новая запись",
        "enter_price": "Введите цену (0 — бесплатно):",
        "enter_number": "Введите число.",
        "service_created": "✅ Услуга создана: {name}",
        "service_deleted": "✅ Услуга удалена.",
        "service_archived": "✅ Услуга архивирована.",
        "service_has_bookings_archived": "✅ Услуга архивирована. Старые записи сохранены.",
        "service_delete_confirm": (
            "⚠️ Удалить услугу?\n\n"
            "Если по услуге уже есть записи, она будет скрыта для новых клиентов, "
            "но старые записи сохранятся."
        ),
        "service_delete_confirm_yes": "✅ Да, удалить/архивировать",
        "service_delete_confirm_no": "❌ Отмена",
        "service_delete_cancelled": "Удаление отменено.",
        "service_archived_label": "Архив",
        "services_active_title": "Активные услуги:",
        "services_no_active": "Активных услуг нет.",
        "services_disabled_button": "🔴 Отключённые услуги",
        "services_disabled_title": "🔴 Отключённые услуги",
        "services_disabled_intro": "Эти услуги скрыты от клиентов, но не удалены.",
        "services_no_disabled": "Отключённых услуг нет.",
        "back_to_disabled_services": "🔙 Назад к отключённым услугам",
        "move_to_archive": "📦 Переместить в архив",
        "archived_services": "📦 Архив услуг",
        "archive_empty": "Архив пуст.",
        "archived_service_detail": (
            "📦 Архивная услуга\n\n"
            "Название: {name}\n"
            "Длительность: {duration} мин.\n"
            "Цена: {price}\n"
            "Старых записей: {bookings_count}"
        ),
        "restore_service": "♻️ Восстановить услугу",
        "service_restored": "✅ Услуга восстановлена.",
        "delete_permanently": "🗑 Удалить навсегда",
        "delete_permanently_confirm": (
            "⚠️ Удалить услугу навсегда?\n"
            "Это действие нельзя отменить."
        ),
        "delete_permanently_confirm_yes": "✅ Да, удалить навсегда",
        "delete_permanently_confirm_no": "❌ Отмена",
        "delete_permanently_success": "✅ Услуга удалена навсегда.",
        "delete_permanently_blocked_has_bookings": (
            "❌ Нельзя удалить навсегда, потому что по этой услуге есть старые записи.\n"
            "Услуга останется в архиве, чтобы история записей не сломалась."
        ),
        "back_to_archive": "🔙 Назад в архив",
        "back_to_services": "🔙 Назад к услугам",
        "back_to_admin_panel": "🔙 Назад в админ-панель",
        "archived_services_intro": (
            "Здесь находятся услуги, скрытые от клиентов.\n"
            "Старые записи по ним сохраняются."
        ),
        "service_not_found": "Услуга не найдена.",
        "updated": "Обновлено.",
        "edit_name": "✏️ Изменить название",
        "edit_description": "✏️ Изменить описание",
        "edit_duration": "⏱ Длительность",
        "edit_price": "💰 Цена",
        "enable_service": "🟢 Включить",
        "disable_service": "🔴 Отключить",
        "service_list_disabled": "🔴 {name} (отключена)",
        "service_disabled_success": "Услуга отключена и перенесена в раздел «Отключённые услуги».",
        "service_enabled_success": "Услуга включена и снова доступна в активных услугах.",
        "service_unavailable_booking": "Эта услуга сейчас недоступна для записи.",
        "delete_service": "🗑 Удалить",
        "enter_new_name": "Введите новое название:",
        "enter_new_description": "Введите новое описание:",
        "enter_new_duration": "Введите новую длительность (минуты):",
        "enter_new_price": "Введите новую цену:",
        "enter_value": "Введите значение:",
        "duration_label": "Длительность: {duration}",
        "price_label": "Цена: {price}",
        "price_free": "Бесплатно",
        "active_label": "Активна: {value}",
        "yes": "да",
        "no": "нет",
        "working_hours_current": "Текущее рабочее время:",
        "working_hours_set": "Часы для {day}\nВведите начало (ЧЧ:ММ):",
        "working_hours_updated": "Рабочее время обновлено для {day}.",
        "invalid_time": "Неверное время. Используйте ЧЧ:ММ",
        "invalid_time_short": "Неверное время.",
        "enter_end_time": "Введите конец (ЧЧ:ММ):",
        "unavailable_dates_title": "Недоступные даты:",
        "unavailable_none": "(нет)",
        "unavailable_hint": (
            "\n\nОтправьте дату (ДД.ММ.ГГГГ) чтобы закрыть день, или диапазон:\n"
            "ДАТА НАЧАЛО-КОНЕЦ для блокировки времени"
        ),
        "invalid_date": "Неверная дата.",
        "invalid_date_format": "Неверная дата. Используйте ДД.ММ.ГГГГ",
        "invalid_time_range": "Неверный диапазон времени.",
        "blocked_range": "Заблокировано {date} {start}-{end}",
        "date_marked_unavailable": "Дата {date} отмечена как недоступная.",
        "unav_title": "🚫 Недоступные даты",
        "unav_intro": (
            "Здесь можно закрыть дни или отдельное время для записи.\n"
            "Клиенты не смогут записаться на эти даты и часы."
        ),
        "unav_tomorrow": "⚡ Завтра выходной",
        "unav_next7": "⚡ Следующие 7 дней недоступны",
        "unav_block_day": "📅 Закрыть конкретный день",
        "unav_block_time": "🕘 Закрыть время в конкретный день",
        "unav_list": "📋 Список недоступного времени",
        "unav_tomorrow_confirm_text": (
            "🚫 Сделать завтра недоступным?\n"
            "Клиенты не смогут записаться на завтра."
        ),
        "unav_tomorrow_confirm_yes": "✅ Да, закрыть завтра",
        "unav_next7_confirm_text": (
            "🚫 Сделать следующие 7 дней недоступными?\n"
            "Клиенты не смогут записаться на ближайшие 7 дней.\n"
            "Обычное рабочее расписание не изменится."
        ),
        "unav_next7_confirm_yes": "✅ Да, закрыть 7 дней",
        "unav_confirm_yes": "✅ Да",
        "unav_confirm_no": "❌ Отмена",
        "unav_tomorrow_done": "✅ Завтра закрыто для записи.",
        "unav_next7_done": "✅ Ближайшие 7 дней закрыты для записи.",
        "unav_day_done": "✅ День закрыт для записи.",
        "unav_time_done": "✅ Время закрыто для записи.",
        "unav_date_today": "Сегодня",
        "unav_date_tomorrow": "Завтра",
        "unav_date_after_tomorrow": "Послезавтра",
        "unav_date_plus": "+{days} дня",
        "unav_enter_date_manual": "✏️ Ввести дату вручную",
        "unav_enter_date_prompt": "Введите дату в формате ДД.ММ.ГГГГ\nНапример: 25.06.2026",
        "unav_invalid_date": "❌ Неверная дата. Используйте ДД.ММ.ГГГГ и дату не из прошлого.",
        "unav_day_confirm_text": "🚫 Закрыть этот день для записи?\n{date}",
        "unav_day_confirm_yes": "✅ Да, закрыть день",
        "unav_full_day": "Весь день",
        "unav_enter_time_manual": "✏️ Ввести вручную",
        "unav_enter_time_prompt": "Введите время в формате:\n14:00-16:00",
        "unav_invalid_time": "❌ Неверный формат. Пример: 14:00-16:00",
        "unav_items_title": "📋 Недоступное время",
        "unav_items_empty": "Пока нет недоступных дат.",
        "unav_item_full_day": "🚫 {date} — весь день",
        "unav_item_time": "🚫 {date} — {start}–{end}",
        "unav_item_full_day_btn": "🗑 {date} — весь день",
        "unav_item_time_btn": "🗑 {date} — {start}–{end}",
        "unav_delete_confirm_text": "Удалить это недоступное время?",
        "unav_delete_yes": "✅ Да, удалить",
        "unav_delete_done": "✅ Недоступное время удалено.",
        "upcoming_bookings": "Предстоящие записи:",
        "no_bookings_admin": "Нет записей",
        "booking_confirmed_admin": "✅ Подтверждено",
        "booking_cancelled_admin": "Запись #{id} отменена.",
        "booking_already_cancelled_or_missing": "Эта запись уже отменена или не найдена.",
        "confirm_booking_btn": "✅ Подтвердить запись",
        "cancel_booking_btn": "❌ Отменить запись",
        "my_booking_detail_title": "📋 Ваша запись",
        "my_booking_service_location": "Место проведения",
        "my_booking_client_address": "Адрес клиента",
        "my_booking_comment": "Комментарий",
        "reschedule_booking_btn": "🔁 Перенести запись",
        "change_location_btn": "📍 Изменить место",
        "change_address_btn": "🏠 Изменить адрес клиента",
        "change_comment_btn": "💬 Изменить комментарий",
        "back_to_my_bookings": "🔙 Назад к моим записям",
        "confirm_reschedule": (
            "Подтвердить перенос записи?\n"
            "Было: {old_datetime}\n"
            "Стало: {new_datetime}"
        ),
        "confirm_reschedule_btn": "✅ Подтвердить перенос",
        "booking_rescheduled": "✅ Запись перенесена.",
        "service_location_changed": "✅ Место проведения изменено.",
        "address_changed": "✅ Адрес изменён.",
        "comment_changed": "✅ Комментарий изменён.",
        "reschedule_too_late": (
            "❌ Эту запись уже нельзя перенести. Свяжитесь с администратором."
        ),
        "booking_not_editable": "Эту запись уже нельзя изменить.",
        "booking_changed_admin": (
            "🔁 Запись изменена клиентом\n"
            "Услуга: {service}\n"
            "Клиент: {client_name}\n"
            "Телефон: {phone}\n"
            "Было: {old_value}\n"
            "Стало: {new_value}"
        ),
        "enter_new_address": "Введите новый адрес или место встречи",
        "enter_new_comment": (
            "Введите новый комментарий или нажмите «Пропустить», чтобы очистить."
        ),
        "message_client_btn": "✉️ Написать клиенту",
        "enter_message_client": "Введите сообщение для клиента:",
        "message_sent": "Сообщение отправлено.",
        "message_from_admin": "📩 Сообщение от администратора:\n{text}",
        "calendar_settings_title": "Настройки Google Calendar:",
        "calendar_settings_body": (
            "Включено (env): {env_enabled}\n"
            "Включено (БД): {db_enabled}\n"
            "Calendar ID: {calendar_id}\n"
            "Refresh token: {token_stored}\n\n"
            "Настройте GOOGLE_* в .env. Сохраните refresh token через ключ "
            "'google_refresh_token' или в таблице calendar_settings."
        ),
        "settings_calendar_btn": "📅 Google Calendar",
        "settings_calendar_title": "📅 Google Calendar",
        "settings_calendar_body": (
            "Статус: {status}\n"
            "Calendar ID: {calendar_id}\n"
            "Синхронизация событий: {sync}\n"
            "Env (.env): {env_status}"
        ),
        "settings_calendar_toggle_on": "✅ Выключить Google Calendar",
        "settings_calendar_toggle_off": "❌ Включить Google Calendar",
        "settings_calendar_toggle_env_off": "❌ Выключено в .env",
        "settings_calendar_test_btn": "📋 Проверить подключение",
        "settings_calendar_env_note": "Установите GOOGLE_CALENDAR_ENABLED=true в .env для синхронизации.",
        "calendar_test_checking": "Проверка подключения Google Calendar...",
        "calendar_test_disabled_env": "Google Calendar выключен в .env (GOOGLE_CALENDAR_ENABLED=false).",
        "calendar_test_disabled_db": "Синхронизация Google Calendar выключена в настройках бота.",
        "calendar_test_missing_credentials": "Не хватает данных: {missing}",
        "calendar_test_client_build_failed": "Не удалось создать клиент Google Calendar. Проверьте пакеты и credentials.",
        "calendar_test_success": "✅ Подключение OK. Календарь: {detail}",
        "calendar_test_failed": "❌ Ошибка подключения: {detail}",
        "calendar_test_invalid_token": "❌ Неверный или просроченный refresh token. Пройдите OAuth заново.",
        "calendar_test_permission_denied": "❌ Нет доступа. Проверьте OAuth scopes и доступ к календарю.",
        "calendar_test_invalid_calendar_id": "❌ Календарь не найден: {detail}",
        "calendar_enabled_msg": "✅ Синхронизация Google Calendar включена.",
        "calendar_disabled_msg": "❌ Синхронизация Google Calendar выключена.",
        "calendar_event_title": "Запись: {service_name}",
        "calendar_label_client": "Клиент: {value}",
        "calendar_label_phone": "Телефон: {value}",
        "calendar_label_service": "Услуга: {value}",
        "calendar_label_datetime": "Дата/время: {value}",
        "calendar_label_address": "Адрес: {value}",
        "calendar_label_service_location": "Место проведения: {title}",
        "calendar_label_service_location_address": "Адрес места: {value}",
        "calendar_label_comment": "Комментарий: {value}",
        "calendar_label_booking_id": "ID записи: {value}",
        "bot_settings_title": "Настройки бота — отправьте в формате:",
        "bot_settings_format": "KEY=VALUE",
        "bot_settings_keys": (
            "Доступные ключи:\n"
            "auto_confirm\n"
            "contact_admin_username\n"
            "reminders_enabled\n"
            "client_reminder_1_minutes\n"
            "client_reminder_2_minutes\n"
            "admin_reminder_minutes\n"
            "reminder_test_mode\n"
            "test_client_reminder_minutes\n"
            "test_admin_reminder_minutes"
        ),
        "bot_settings_auto_confirm": "auto_confirm=true — записи подтверждаются сразу",
        "settings_saved": "✅ Настройка {key} сохранена.",
        "invalid_format": "Используйте формат KEY=VALUE",
        "status_pending": "ожидает подтверждения",
        "status_confirmed": "подтверждена",
        "status_cancelled": "отменена",
        "status_completed": "завершена",
        "booking_status_line": "Статус: {status}",
        "reminder_client": (
            "🔔 Напоминание о записи\n"
            "Услуга: {service_name}\n"
            "Дата и время: {date_time}\n"
            "Ждём вас!"
        ),
        "reminder_admin": (
            "🔔 Скоро запись клиента\n"
            "Услуга: {service_name}\n"
            "Дата и время: {date_time}\n"
            "Клиент: {client_name}\n"
            "Телефон: {client_phone}"
            "{location_block}{comment_block}"
        ),
        "reminder_admin_location": "\n📍 Адрес клиента: {location}",
        "reminder_admin_service_location": "\n📍 Место проведения: {title}",
        "reminder_admin_service_location_address": "\nАдрес: {address}",
        "reminder_admin_comment": "\n💬 Комментарий: {comment}",
        "phone_not_provided": "—",
        "settings_menu_title": "⚙️ Настройки бота",
        "settings_menu_body": (
            "Текущие настройки:\n"
            "✅ Автоподтверждение: {auto_confirm}\n"
            "🔔 Напоминания: {reminders}\n"
            "🌐 Язык: {language}\n"
            "📞 Контакт админа: {contact}"
        ),
        "label_enabled": "включено",
        "label_disabled": "выключено",
        "lang_name_ru": "Русский",
        "lang_name_en": "English",
        "settings_auto_confirm_btn_on": "✅ Автоподтверждение",
        "settings_auto_confirm_btn_off": "❌ Автоподтверждение",
        "settings_reminders_btn": "🔔 Напоминания",
        "settings_language_btn": "🌐 Язык",
        "settings_enabled_languages_btn": "🌐 Доступные языки",
        "settings_enabled_languages_title": "🌐 Доступные языки",
        "settings_enabled_languages_body": (
            "Сейчас: {current}\n\n"
            "Выберите, какие языки будут доступны пользователям."
        ),
        "enabled_languages_mode_ru": "Русский",
        "enabled_languages_mode_en": "English",
        "enabled_languages_mode_both": "Русский + English",
        "enabled_languages_btn_ru": "🇷🇺 Только русский",
        "enabled_languages_btn_en": "🇬🇧 English only",
        "enabled_languages_btn_both": "🇷🇺🇬🇧 Русский + English",
        "enabled_languages_saved": "✅ Доступные языки обновлены.",
        "language_switching_disabled": "Смена языка отключена. В этом боте доступен только русский язык.",
        "settings_contact_btn": "📞 Контакт админа",
        "start_screen_btn": "👋 Стартовое сообщение",
        "start_screen_menu_title": "👋 Стартовое сообщение",
        "start_screen_menu_body": (
            "Текст RU: {text_ru}\n"
            "Текст EN: {text_en}\n"
            "Фото RU: {photo_ru}\n"
            "Фото EN: {photo_en}"
        ),
        "start_screen_menu_body_single": "Текст: {text}\nФото: {photo}",
        "start_screen_edit_text_btn": "✏️ Изменить текст",
        "start_screen_upload_photo_btn": "🖼 Загрузить фото",
        "start_screen_toggle_photo_on": "❌ Выключить фото",
        "start_screen_toggle_photo_off": "✅ Включить фото",
        "start_screen_preview_btn": "👁 Предпросмотр",
        "start_screen_text_custom": "настроен",
        "start_screen_text_default": "стандартный",
        "start_screen_photo_set": "есть",
        "start_screen_photo_not_set": "нет",
        "start_screen_edit_ru_btn": "✏️ Изменить текст RU",
        "start_screen_edit_en_btn": "✏️ Изменить текст EN",
        "start_screen_upload_ru_btn": "🖼 Загрузить фото RU",
        "start_screen_upload_en_btn": "🖼 Загрузить фото EN",
        "start_screen_toggle_ru_on": "❌ Выключить фото RU",
        "start_screen_toggle_ru_off": "✅ Включить фото RU",
        "start_screen_toggle_en_on": "❌ Выключить фото EN",
        "start_screen_toggle_en_off": "✅ Включить фото EN",
        "start_screen_preview_ru_btn": "👁 Предпросмотр RU",
        "start_screen_preview_en_btn": "👁 Предпросмотр EN",
        "start_screen_reset_btn": "♻️ Сбросить к стандартному",
        "start_screen_back_settings_btn": "🔙 Назад к настройкам",
        "start_screen_prompt_ru": "Отправьте новый текст для /start на русском языке.",
        "start_screen_prompt_en": "Отправьте новый текст для /start на английском языке.",
        "start_screen_prompt_photo_ru": "Отправьте фото для русского стартового сообщения.",
        "start_screen_prompt_photo_en": "Отправьте фото для английского стартового сообщения.",
        "start_screen_not_photo": "❌ Отправьте именно фото.",
        "start_screen_text_too_long": "❌ Текст слишком длинный. Максимум 1000 символов.",
        "start_screen_text_empty": "❌ Текст не может быть пустым.",
        "start_screen_upload_first_ru": "Сначала загрузите фото RU.",
        "start_screen_upload_first_en": "Сначала загрузите фото EN.",
        "start_screen_reset_confirm": "Сбросить стартовое сообщение к стандартному?",
        "start_screen_reset_yes": "✅ Да, сбросить",
        "start_screen_reset_no": "❌ Отмена",
        "start_screen_photo_saved_ru": "✅ Фото RU для старта сохранено.",
        "start_screen_photo_saved_en": "✅ Фото EN для старта сохранено.",
        "settings_advanced_btn": "⚙️ Расширенные настройки",
        "settings_back_admin_btn": "🔙 Назад в админ-панель",
        "settings_back_settings_btn": "🔙 Назад к настройкам",
        "settings_back_reminders_btn": "🔙 Назад",
        "settings_back_test_btn": "🔙 Назад",
        "auto_confirm_enabled_msg": "✅ Автоподтверждение включено.",
        "auto_confirm_disabled_msg": "❌ Автоподтверждение выключено.",
        "settings_reminders_title": "🔔 Настройки напоминаний",
        "settings_reminders_body": (
            "Статус: {status}\n"
            "Клиенту: за {client1} и за {client2}\n"
            "Админу: за {admin}\n"
            "Тестовый режим: {test_mode}"
        ),
        "settings_reminders_toggle_on": "✅ Выключить напоминания",
        "settings_reminders_toggle_off": "❌ Включить напоминания",
        "settings_reminder_client1_btn": "⏰ Первое напоминание клиенту",
        "settings_reminder_client2_btn": "⏰ Второе напоминание клиенту",
        "settings_reminder_admin_btn": "👤 Напоминание админу",
        "settings_reminder_test_btn": "🧪 Тестовый режим",
        "settings_enter_manual_btn": "✏️ Ввести вручную",
        "settings_enter_minutes_prompt": "Введите время в минутах, например 60",
        "settings_invalid_minutes": "Введите число от 1 до 10080.",
        "settings_time_saved": "✅ Сохранено.",
        "settings_test_title": "🧪 Тестовый режим напоминаний",
        "settings_test_body": (
            "Этот режим нужен только для проверки.\n"
            "Например, можно создать запись через 6–10 минут и быстро проверить напоминания.\n\n"
            "Статус: {status}\n"
            "Клиенту: за {client}\n"
            "Админу: за {admin}"
        ),
        "settings_test_toggle_on": "✅ Выключить тестовый режим",
        "settings_test_toggle_off": "❌ Включить тестовый режим",
        "settings_test_client_section": "👤 Напоминание клиенту",
        "settings_test_admin_section": "👨‍💼 Напоминание админу",
        "settings_contact_title": "📞 Контакт админа",
        "settings_contact_body": "Текущий контакт: {contact}",
        "settings_contact_not_set": "не задан",
        "settings_contact_edit_btn": "✏️ Изменить контакт",
        "settings_contact_clear_btn": "❌ Очистить контакт",
        "settings_contact_prompt": "Отправьте username, например @username:",
        "settings_contact_saved": "✅ Контакт сохранён.",
        "settings_contact_cleared": "✅ Контакт очищен.",
        "settings_contact_invalid": "Используйте формат @username.",
        "settings_language_title": "🌐 Язык",
        "settings_advanced_title": "⚙️ Расширенные настройки",
        "settings_advanced_body": (
            "Этот раздел нужен только для разработчика или ручной настройки.\n"
            "Обычно вам не нужно использовать системные ключи.\n"
            "Для обычной настройки используйте кнопки:\n"
            "✅ Автоподтверждение\n"
            "🔔 Напоминания\n"
            "🌐 Язык\n"
            "📞 Контакт админа"
        ),
        "settings_advanced_keys_title": "Системные ключи:",
        "settings_advanced_enter_btn": "✏️ Ввести параметр вручную",
        "settings_advanced_show_keys_btn": "📋 Показать системные ключи",
        "settings_back_advanced_btn": "🔙 Назад к расширенным настройкам",
        "settings_advanced_manual_prompt": (
            "Отправьте параметр в формате:\n"
            "ключ=значение\n\n"
            "Пример:\n"
            "auto_confirm=true"
        ),
        "settings_advanced_keys_list": (
            "auto_confirm — автоподтверждение записей\n"
            "contact_admin_username — username для связи с админом\n"
            "reminders_enabled — включить или выключить напоминания\n"
            "client_reminder_1_minutes — первое напоминание клиенту, в минутах\n"
            "client_reminder_2_minutes — второе напоминание клиенту, в минутах\n"
            "admin_reminder_minutes — напоминание админу, в минутах\n"
            "reminder_test_mode — тестовый режим напоминаний\n"
            "test_client_reminder_minutes — тестовое напоминание клиенту, в минутах\n"
            "test_admin_reminder_minutes — тестовое напоминание админу, в минутах"
        ),
        "time_preset_1440": "24 часа",
        "time_preset_720": "12 часов",
        "time_preset_360": "6 часов",
        "time_preset_180": "3 часа",
        "time_preset_120": "2 часа",
        "time_preset_60": "1 час",
        "time_preset_30": "30 минут",
        "time_preset_15": "15 минут",
        "time_preset_10": "10 минут",
        "time_preset_5": "5 минут",
        "time_preset_3": "3 минуты",
        "time_preset_1": "1 минута",
        "duration_days": "{n} дн.",
        "duration_hours": "{n} ч.",
        "duration_minutes": "{n} мин.",
        "duration_one_hour": "1 час",
        "duration_n_hours": "{n} часа",
        "duration_n_minutes": "{n} мин",
        "duration_hours_minutes": "{hours} {minutes_part}",
        "weekday_0": "Понедельник",
        "weekday_1": "Вторник",
        "weekday_2": "Среда",
        "weekday_3": "Четверг",
        "weekday_4": "Пятница",
        "weekday_5": "Суббота",
        "weekday_6": "Воскресенье",
        "weekday_short_0": "Пн",
        "weekday_short_1": "Вт",
        "weekday_short_2": "Ср",
        "weekday_short_3": "Чт",
        "weekday_short_4": "Пт",
        "weekday_short_5": "Сб",
        "weekday_short_6": "Вс",
        "wh_title": "🕘 Рабочее время",
        "wh_current_schedule": "Текущее расписание:",
        "wh_day_line_working": "{day}: {start}–{end}",
        "wh_day_line_off": "{day}: выходной",
        "wh_day_detail_working": "🕘 {day}\nСтатус: рабочий день\nВремя: {start}–{end}",
        "wh_day_detail_off": "🕘 {day}\nСтатус: выходной",
        "wh_toggle_to_off": "❌ Выходной",
        "wh_toggle_to_on": "✅ Рабочий день",
        "wh_change_time": "🕘 Изменить время",
        "wh_back_schedule": "🔙 Назад к расписанию",
        "wh_choose_time": "Выберите рабочее время:",
        "wh_enter_manual": "✏️ Ввести вручную",
        "wh_manual_prompt": "Введите рабочее время в формате:\n09:00-18:00",
        "wh_invalid_time_format": "❌ Неверный формат. Пример: 09:00-18:00",
        "wh_updated": "Расписание обновлено.",
        "wh_quick_presets": "⚡ Быстрые шаблоны",
        "wh_week_off": "🚫 Сделать неделю выходной",
        "wh_presets_title": "⚡ Быстрые шаблоны расписания\nВыберите готовый вариант:",
        "wh_preset_monfri_9_18": "Пн–Пт 09:00–18:00",
        "wh_preset_monfri_10_19": "Пн–Пт 10:00–19:00",
        "wh_preset_everyday_10_20": "Каждый день 10:00–20:00",
        "wh_preset_satsun_off": "Сб–Вс выходные",
        "wh_preset_everyday_off": "Каждый день выходной",
        "wh_preset_applied": "Шаблон применён.",
        "wh_week_off_confirm_text": (
            "🚫 Сделать следующую неделю недоступной?\n"
            "Клиенты не смогут записаться на ближайшие 7 дней.\n"
            "Обычное рабочее расписание не изменится."
        ),
        "wh_week_off_confirm_yes": "✅ Да, сделать недоступной",
        "wh_week_off_confirm_no": "❌ Отмена",
        "wh_week_off_done": "Ближайшие 7 дней отмечены как недоступные.",
        "wh_on": "вкл",
        "wh_off": "выкл",
    },
}


def _resolve_lang(lang: str) -> str:
    settings = get_settings()
    if lang in TEXTS:
        return lang
    if settings.default_language in TEXTS:
        return settings.default_language
    return "en"


def t(lang: str, text_key: str, **kwargs: str) -> str:
    lang = _resolve_lang(lang)
    template = TEXTS.get(lang, {}).get(text_key)
    if template is None:
        template = TEXTS.get(get_settings().default_language, {}).get(text_key)
    if template is None:
        template = TEXTS.get("en", {}).get(text_key)
    if template is None:
        return text_key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError, TypeError):
            return template
    return template


def format_duration(lang: str, minutes: int) -> str:
    if minutes >= 1440 and minutes % 1440 == 0:
        return t(lang, "duration_days", n=str(minutes // 1440))
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return t(
            lang,
            "duration_hours_minutes",
            hours=format_duration_hours(hours, lang),
            minutes_part=format_duration_minutes(mins, lang),
        )
    if hours:
        return format_duration_hours(hours, lang)
    return format_duration_minutes(minutes, lang)


def format_duration_hours(hours: int, lang: str) -> str:
    if hours == 1:
        return t(lang, "duration_one_hour")
    if lang == "ru":
        if hours % 10 == 1 and hours % 100 != 11:
            return f"{hours} час"
        if hours % 10 in (2, 3, 4) and hours % 100 not in (12, 13, 14):
            return f"{hours} часа"
        return f"{hours} часов"
    return t(lang, "duration_n_hours", n=str(hours))


def format_duration_minutes(minutes: int, lang: str) -> str:
    return t(lang, "duration_n_minutes", n=str(minutes))


def format_buffer(lang: str, minutes: int) -> str:
    if minutes == 0:
        return t(lang, "no_buffer")
    return format_duration(lang, minutes)


def status_label(lang: str, status: str) -> str:
    return t(lang, f"status_{status}")


def weekday_name(lang: str, day: int, short: bool = False) -> str:
    prefix = "weekday_short" if short else "weekday"
    return t(lang, f"{prefix}_{day}")


def all_texts(key: str) -> frozenset[str]:
    return frozenset(TEXTS[lang][key] for lang in TEXTS if key in TEXTS[lang])


def cancel_texts() -> frozenset[str]:
    texts = {"Cancel", "Отмена", "❌ Cancel", "❌ Отмена"}
    for lang in TEXTS:
        if "cancel" in TEXTS[lang]:
            texts.add(TEXTS[lang]["cancel"])
    return frozenset(texts)


CANCEL_TEXTS = cancel_texts()

LANG_RU = "🇷🇺 Русский"
LANG_EN = "🇬🇧 English"
