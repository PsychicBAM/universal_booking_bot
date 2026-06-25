from __future__ import annotations

from app.config import get_settings

# Extend with "ar": {...} when Arabic translations are ready.
TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "welcome": "👋 Welcome to the booking bot!",
        "welcome_sub": "Book an appointment, view your bookings, or contact the admin.",
        "support_line": "\nSupport: @{username}",
        "book_appointment": "📅 Book appointment",
        "main_menu_services": "📋 Choose service",
        "main_menu_my_activity": "📂 My bookings & requests",
        "my_activity_title": "📂 My bookings & requests",
        "my_activity_intro": "Choose a section:",
        "my_activity_bookings": "📋 My bookings",
        "my_activity_orders": "🗂 My requests",
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
        "booking_choose_time_period": "Choose a time period:",
        "booking_period_morning": "🌅 Morning",
        "booking_period_day": "🌞 Day",
        "booking_period_evening": "🌙 Evening",
        "booking_slots_count": "{count} slots",
        "booking_back_to_dates": "⬅️ Back to dates",
        "booking_back_to_periods": "⬅️ Back to periods",
        "booking_back_to_service": "⬅️ Back to service",
        "booking_back_to_time": "⬅️ Back to time",
        "booking_back_to_confirm": "⬅️ Back to confirmation",
        "booking_choose_time_in_period": "Choose a time:",
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
        "unknown_action_open_again": "This action is outdated or not handled yet. Please reopen the section.",
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
        "my_bookings_title": "Your bookings:",
        "my_bookings_empty": "You have no active bookings.",
        "client_booking_service_fallback": "Service",
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
        "schedule_button": "📅 Schedule",
        "schedule_title": "📅 Schedule & availability",
        "schedule_wh_section": "🕘 Working hours:",
        "schedule_unav_section": "🚫 Upcoming closures:",
        "schedule_unav_empty": "No upcoming closures.",
        "schedule_unav_more": "…and {count} more",
        "schedule_configure_wh": "🕘 Configure working hours",
        "schedule_block_dates": "🚫 Block dates/times",
        "schedule_quick_actions": "⚡ Quick actions",
        "schedule_closures_list": "📋 Closures list",
        "schedule_back_admin": "🔙 Back to admin panel",
        "schedule_quick_title": "⚡ Quick actions",
        "admin_working_hours": "🕘 Working hours",
        "admin_unavailable": "🚫 Unavailable dates",
        "admin_bookings": "📒 Bookings",
        "admin_clients_button": "👥 Clients",
        "clients_title": "👥 Clients",
        "clients_hub_simplified_title": "👥 Clients",
        "clients_hub_simplified_intro": (
            "All clients are collected here.\n"
            "Open a client to see bookings, requests and contacts."
        ),
        "clients_all_button": "📋 All clients",
        "clients_search_button": "🔎 Search client",
        "client_tag_new": "🆕",
        "client_tag_repeated": "🔁",
        "client_tag_future_booking": "📅 {count}",
        "client_tag_has_order": "📝 {count}",
        "client_tag_cancelled": "❌ {count}",
        "clients_intro": (
            "This section shows client history: previous visits, first-time clients, "
            "returning clients, and upcoming bookings."
        ),
        "clients_filter_upcoming": "📅 With upcoming bookings",
        "clients_filter_visited": "✅ Visited before",
        "clients_filter_new": "🆕 New clients",
        "clients_filter_returning": "🔁 Returning clients",
        "clients_filter_cancelled": "❌ Had cancellations",
        "clients_filter_all": "📋 All clients",
        "clients_search": "🔍 Search client",
        "clients_no_results": "No clients found.",
        "clients_back_admin": "🔙 Back to admin panel",
        "clients_back_list": "🔙 Back to list",
        "client_callback_invalid": "This clients screen is outdated. Open Clients again.",
        "booking_back_context_invalid": "This screen is outdated. Open the section again.",
        "calendar_auth_expired_admin_hint": (
            "Google Calendar needs re-authorization. The booking was saved, but no calendar event was added."
        ),
        "clients_list_new": "🆕 {name} — {count} booking(s)",
        "clients_list_returning": "🔁 {name} — {count} bookings, next {date}",
        "clients_list_returning_no_next": "🔁 {name} — {count} bookings",
        "clients_list_visited": "✅ {name} — visited {count} time(s)",
        "clients_list_cancelled": "❌ {name} — {count} cancellation(s)",
        "client_detail_title": "👤 Client",
        "client_name_line": "Name: {name}",
        "client_phone_line": "Phone: {phone}",
        "client_username_line": "Username: {username}",
        "client_telegram_id_line": "Telegram ID: {telegram_id}",
        "client_stats_title": "Statistics:",
        "client_total_bookings": "Total bookings: {count}",
        "client_upcoming_count": "Upcoming: {count}",
        "client_past_count": "Visited: {count}",
        "client_cancelled_count": "Cancelled: {count}",
        "client_cannot_attend_count": "Cannot attend / needs change: {count}",
        "client_first_booking": "First booking: {date}",
        "client_last_booking": "Last booking: {date}",
        "client_next_booking": "Next booking: {date}",
        "client_next_booking_none": "none",
        "client_status_line": "Status: {status}",
        "client_status_new": "new",
        "client_status_returning": "returning",
        "client_status_visited": "visited before",
        "client_future_bookings": "📅 Future bookings",
        "client_booking_history": "📜 Booking history",
        "client_message_button": "✉️ Message client",
        "client_send_confirmation_nearest": "🔔 Send confirmation for nearest booking",
        "client_no_upcoming_booking": "This client has no upcoming bookings.",
        "client_search_prompt": "Enter client name, phone, username, or Telegram ID.",
        "date_today": "Today",
        "date_tomorrow": "Tomorrow",
        "booking_id_label": "Booking ID: {id}",
        "client_future_booking_row": "#{id} {datetime} — {service} — {status}",
        "client_history_past": "✅ #{id} {datetime} — {service}",
        "client_history_cancelled": "❌ #{id} {datetime} — {service} — cancelled",
        "client_history_cannot_attend": "⚠️ #{id} {datetime} — {service} — needs change",
        "admin_calendar": "📆 Calendar settings",
        "admin_settings": "⚙️ Bot settings",
        "services_management": "🛠 Services",
        "services_hub_intro": "Choose a section:",
        "services_folder_active": "✅ Active services — {count}",
        "services_folder_disabled": "🔴 Disabled services — {count}",
        "services_folder_archive": "📦 Service archive — {count}",
        "services_search_button": "🔎 Search service",
        "services_active_title": "✅ Active services",
        "services_disabled_title": "🔴 Disabled services",
        "services_archive_title": "📦 Service archive",
        "services_group_booking": "📅 Bookings:",
        "services_group_order": "📝 Requests:",
        "services_search_prompt": "Enter service name to search:",
        "services_search_no_results": "No services found.",
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
        "bookings_hub_title": "📒 Bookings",
        "bookings_hub_intro": "Choose a section:",
        "bookings_active_summary": "Active bookings: {count}",
        "bookings_pending_summary": "🕓 Waiting for admin approval: {count}",
        "bookings_confirmed_summary": "✅ Confirmed: {count}",
        "bookings_waiting_client_response_summary": "❔ Waiting for client response: {count}",
        "bookings_history_summary": "📜 History: {count}",
        "bookings_cancelled_summary": "❌ Cancelled: {count}",
        "bookings_choose_action": "Choose an action:",
        "bookings_all_active_button": "📋 All active bookings",
        "bookings_pending_admin_button": "🕓 Waiting for admin approval",
        "bookings_search_button": "🔎 Search booking",
        "bookings_all_active_title": "📋 All active bookings",
        "bookings_pending_admin_title": "🕓 Waiting for admin approval",
        "bookings_search_prompt": "Enter client name, phone, service name, or booking ID:",
        "bookings_search_no_results": "No bookings found.",
        "bookings_folder_upcoming": "📅 Upcoming bookings",
        "bookings_folder_pending_admin": "🕓 Waiting for admin approval",
        "bookings_folder_confirmed_bookings": "✅ Confirmed bookings",
        "bookings_folder_waiting_client_response": "❔ Waiting for client response",
        "bookings_folder_needs_change": "⚠️ Needs change",
        "bookings_folder_history": "📜 Booking history",
        "bookings_folder_cancelled": "❌ Cancelled",
        "bookings_pending_admin_intro": "These requests are waiting for admin approval.",
        "bookings_confirmed_bookings_intro": "These bookings are confirmed by the admin and active.",
        "bookings_waiting_client_response_intro": "These clients have not answered the booking reminder question yet.",
        "bookings_folder_needs_change_intro": "These clients said the booking needs to be changed or cancelled.",
        "bookings_folder_waiting": "❔ Waiting for confirmation",
        "bookings_folder_confirmed": "✅ Confirmed by client",
        "bookings_folder_waiting_intro": "These clients have not responded to the booking confirmation yet.",
        "bookings_folder_confirmed_intro": "These clients confirmed their booking.",
        "booking_cancelled_by_client_admin_title": "❌ Client cancelled a booking",
        "booking_cancelled_by_client_admin_status": "cancelled by client",
        "booking_cancelled_by_admin_client_title": (
            "❌ Your booking was cancelled by the administrator"
        ),
        "booking_cancelled_by_admin_client_body": (
            "Service: {service}\n"
            "Date and time: {datetime}\n\n"
            "If you have questions, please contact the administrator."
        ),
        "order_cancelled_by_client_admin_title": "❌ Client cancelled a request",
        "order_cancelled_by_client_admin_status": "cancelled by client",
        "order_cancelled_by_admin_client_title": (
            "❌ Your request was cancelled by the administrator"
        ),
        "order_cancelled_by_admin_client_body": (
            "Service: {service}\n\n"
            "If you have questions, please contact the administrator."
        ),
        "booking_rescheduled_by_client_admin_title": "🔄 Client rescheduled a booking",
        "booking_status_label": "Booking status: {status}",
        "client_response_label": "Client response: {response}",
        "booking_status_pending_admin": "waiting for admin approval",
        "booking_status_confirmed": "confirmed",
        "booking_status_cancelled": "cancelled",
        "client_response_no_response": "no response",
        "client_response_confirmed": "confirmed",
        "client_response_needs_change": "needs change",
        "bookings_empty_folder": "There are no bookings in this section.",
        "bookings_back_to_hub": "🔙 Back to bookings",
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
        "reschedule_back_to_booking": "⬅️ Back to booking",
        "change_location_btn": "📍 Change location",
        "change_address_btn": "🏠 Change client address",
        "change_comment_btn": "💬 Change comment",
        "back_to_my_bookings": "🔙 Back to my bookings",
        "confirm_reschedule": (
            "Confirm reschedule?\n"
            "Was: {old_datetime}\n"
            "Now: {new_datetime}"
        ),
        "reschedule_was_line": "Was: {datetime}",
        "reschedule_became_line": "Now: {datetime}",
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
        "attendance_yes_button": "✅ Confirm",
        "attendance_no_button": "❌ Need to change",
        "attendance_prompt": "Please confirm that your booking is still valid.",
        "attendance_reminder_title": "🔔 Booking confirmation",
        "attendance_reminder_intro": "You have an upcoming booking:",
        "attendance_reminder_service": "Service: {service}",
        "attendance_reminder_datetime": "Date and time: {date_time}",
        "attendance_reminder_service_location": "Location: {title}",
        "attendance_reminder_service_location_address": "\nAddress: {address}",
        "attendance_reminder_client_address": "Address: {address}",
        "attendance_reminder_response_confirmed": "Client response: confirmed",
        "attendance_reminder_response_cannot": "Client response: cannot attend",
        "attendance_confirmed_client": "✅ Thank you! The admin has received your confirmation.",
        "attendance_confirmed_admin": (
            "✅ Client confirmed the booking\n"
            "Client: {client_name}\n"
            "Phone: {phone}\n"
            "Service: {service}\n"
            "Date and time: {date_time}"
        ),
        "attendance_cannot_attend_admin": (
            "⚠️ Client said the booking needs changes\n"
            "Client: {client_name}\n"
            "Phone: {phone}\n"
            "Service: {service}\n"
            "Date and time: {date_time}"
        ),
        "attendance_action_prompt": "What would you like to do with this booking?",
        "attendance_reschedule_button": "🔁 Reschedule booking",
        "attendance_cancel_button": "❌ Cancel booking",
        "attendance_reason_button": "💬 Add reason",
        "attendance_keep_button": "🔙 Keep booking",
        "attendance_reason_prompt": "Write the reason why you can't attend.",
        "attendance_reason_saved": "Reason saved. The admin has been notified.",
        "attendance_reason_too_long": "Reason is too long (max {max_len} characters).",
        "attendance_keep_saved": (
            "Okay, the booking remains unchanged. The admin has already received your response."
        ),
        "attendance_unavailable": "This booking is no longer available.",
        "attendance_status_confirmed": "✅ Client confirmed the booking",
        "attendance_status_cannot_attend": "⚠️ Client said the booking needs changes",
        "attendance_status_reason": "Reason: {reason}",
        "attendance_client_response_confirmed": "Reminder response: confirmed",
        "attendance_client_response_cannot": "Reminder response: cannot attend",
        "attendance_reason_admin": (
            "💬 Client provided a reason\n"
            "Client: {client_name}\n"
            "Phone: {phone}\n"
            "Service: {service}\n"
            "Date and time: {date_time}\n"
            "Reason: {reason}"
        ),
        "attendance_reschedule_fallback": (
            'To reschedule, open "My bookings" and choose "Reschedule", or contact the admin.'
        ),
        "attendance_manual_title": "🔔 Booking confirmation",
        "attendance_manual_intro": "You have an upcoming booking:",
        "admin_attendance_button": "🔔 Booking confirmation",
        "admin_attendance_title": "🔔 Booking confirmation",
        "admin_attendance_filter_today": "🔥 Today",
        "admin_attendance_filter_tomorrow": "⏰ Tomorrow",
        "admin_attendance_filter_7d": "📅 7 days",
        "admin_attendance_filter_all": "🗓 All upcoming",
        "admin_attendance_filter_no_response": "❔ No response",
        "admin_attendance_section_today": "🔥 Today",
        "admin_attendance_section_tomorrow": "⏰ Tomorrow",
        "admin_attendance_section_week": "📅 Next 7 days",
        "admin_attendance_section_later": "🗓 Later",
        "admin_attendance_no_bookings": "No upcoming bookings for this filter.",
        "admin_attendance_send_question": "🔔 Send confirmation question",
        "admin_attendance_sent": "✅ Question sent to client.",
        "admin_attendance_send_failed": "❌ Could not send the question. The client may have blocked the bot.",
        "admin_attendance_already_answered_confirm": "Client already responded. Send the question again?",
        "admin_attendance_resend_yes": "✅ Yes, send",
        "admin_attendance_resend_no": "❌ No",
        "admin_attendance_client_response": "Client response: {response}",
        "admin_attendance_no_response": "no response",
        "admin_attendance_client_response_confirmed": "confirmed",
        "admin_attendance_client_response_cannot": "cannot attend",
        "admin_attendance_client_response_reason": "reason provided",
        "admin_attendance_booking_line": "Booking: #{booking_id}",
        "admin_attendance_client_line": "Client: {client_name}",
        "admin_attendance_phone_line": "Phone: {phone}",
        "admin_attendance_service_line": "Service: {service}",
        "admin_attendance_datetime_line": "Date and time: {date_time}",
        "admin_attendance_reason_line": "Reason: {reason}",
        "admin_attendance_manual_info": "Manually sent: {count} time(s)",
        "admin_attendance_back_to_list": "🔙 Back to list",
        "pagination_prev": "⬅️ Previous",
        "pagination_next": "Next ➡️",
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
        "client_data_settings_button": "👤 Client data",
        "client_data_settings_title": "👤 Client data",
        "client_data_settings_intro": "Configure which data the bot uses during booking.",
        "client_use_telegram_name": "✅ Telegram name: {value}",
        "client_confirm_telegram_name": "✅ Confirm name: {value}",
        "client_phone_request_contact": "✅ Telegram phone button: {value}",
        "client_phone_manual_input": "✅ Manual phone input: {value}",
        "client_phone_required": "✅ Phone required: {value}",
        "client_fast_reuse_saved_data": "✅ Fast booking for returning clients: {value}",
        "client_data_toggle_fast_on": "✅ Fast booking",
        "client_data_toggle_fast_off": "❌ Fast booking",
        "client_data_preview_step_fast_reuse": "{step}. Returning clients see confirmation immediately with saved name and phone.",
        "booking_review_title": "📋 Review your booking:",
        "booking_edit_details": "✏️ Edit details",
        "booking_edit_what": "What would you like to change?",
        "booking_edit_name": "👤 Name",
        "booking_edit_phone": "📞 Phone",
        "booking_edit_address": "📍 Client address",
        "booking_edit_comment": "💬 Comment",
        "booking_edit_back_to_confirm": "🔙 Back to confirmation",
        "client_data_preview": "👁 Preview scenario",
        "client_data_invalid_phone_config": "You cannot disable both phone input methods while phone is required.",
        "client_data_toggle_use_name_on": "✅ Use Telegram name",
        "client_data_toggle_use_name_off": "❌ Use Telegram name",
        "client_data_toggle_confirm_name_on": "✅ Confirm name",
        "client_data_toggle_confirm_name_off": "❌ Confirm name",
        "client_data_toggle_contact_on": '✅ "Share phone" button',
        "client_data_toggle_contact_off": '❌ "Share phone" button',
        "client_data_toggle_manual_on": "✅ Manual phone input",
        "client_data_toggle_manual_off": "❌ Manual phone input",
        "client_data_toggle_required_on": "✅ Phone required",
        "client_data_toggle_required_off": "❌ Phone required",
        "client_data_preview_title": "Booking scenario preview",
        "client_data_preview_step_confirm_name": "{step}. The bot will suggest the Telegram name and ask for confirmation.",
        "client_data_preview_step_auto_name": "{step}. The bot will use the Telegram name automatically.",
        "client_data_preview_step_manual_name": "{step}. The bot will ask for the client's name.",
        "client_data_preview_step_phone_both": "{step}. The bot will offer Telegram contact share or manual phone entry.",
        "client_data_preview_step_phone_contact": "{step}. The bot will offer the Telegram contact share button.",
        "client_data_preview_step_phone_manual": "{step}. The bot will ask for phone number manually.",
        "client_data_preview_step_phone_optional": "{step}. Phone is optional — the client can skip it.",
        "client_data_preview_step_phone_required_missing": "{step}. Phone is required but no input method is enabled.",
        "client_data_preview_step_confirm": "{step}. The client proceeds to booking confirmation.",
        "booking_use_telegram_name_prompt": "Your Telegram name: {telegram_full_name}\nUse this name for the booking?",
        "booking_use_telegram_name_yes": "✅ Yes, use it",
        "booking_enter_other_name": "✏️ Enter another name",
        "booking_saved_phone_prompt": "Your saved number: {phone}\nUse it?",
        "booking_use_saved_phone": "✅ Yes, use it",
        "booking_share_phone": "📱 Share Telegram number",
        "booking_share_phone_button": "📱 Share phone number",
        "booking_enter_phone_manual": "✏️ Enter manually",
        "booking_skip_phone": "⏭ Skip",
        "booking_contact_prompt": "Share your phone number using the button below or enter it manually.",
        "booking_manual_phone_prompt": "Enter your phone number.",
        "booking_wrong_contact": "❌ Please share your own phone number using the button.",
        "booking_phone_received": "✅ Phone number received.",
        "booking_phone_not_provided": "not provided",
        "booking_phone_source_telegram": "Telegram",
        "booking_phone_source_manual": "manual",
        "admin_booking_telegram_line": "🔗 Telegram: {username}",
        "client_telegram_name_line": "Telegram name: {name}",
        "client_phone_source_line": "Phone source: {source}",
        "client_last_seen_line": "Last seen: {datetime}",
        "client_open_telegram_profile": "👤 Open Telegram profile",
        "confirm_settings_button": "🔔 Booking confirmation",
        "confirm_settings_title": "🔔 Booking confirmation",
        "confirm_settings_title_lang": "🔔 Booking confirmation — {target_lang}",
        "confirm_settings_intro": (
            "Customize the question and button labels clients see in reminders "
            "or when you send a confirmation question manually."
        ),
        "confirm_select_language": "Choose a language to configure:",
        "confirm_current_texts": "Current texts:",
        "confirm_current_title": "Title: {value}",
        "confirm_current_question": "Question: {value}",
        "confirm_button_confirm": "Confirm button: {value}",
        "confirm_button_change": "Change button: {value}",
        "confirm_group_main_text": "✏️ Main text",
        "confirm_group_responses": "💬 Responses & notifications",
        "confirm_preview_btn": "👁 Preview",
        "confirm_preview_ru": "👁 Preview RU",
        "confirm_preview_en": "👁 Preview EN",
        "confirm_reset_btn": "♻️ Reset",
        "confirm_back": "🔙 Back",
        "confirm_back_to_confirmation": "🔙 Back",
        "confirm_edit_title_plain": "✏️ Title",
        "confirm_edit_question_plain": "✏️ Question",
        "confirm_edit_confirm_button": "✏️ Confirm button",
        "confirm_edit_change_button": "✏️ Change button",
        "confirm_edit_client_confirm_response": "✏️ Client reply after confirm",
        "confirm_edit_client_change_prompt": "✏️ Text after “need to change”",
        "confirm_edit_admin_confirm_notice": "✏️ Admin notice: confirmed",
        "confirm_edit_admin_change_notice": "✏️ Admin notice: needs changes",
        "confirm_reset_confirm_text": "Reset booking confirmation texts for {target_lang}?",
        "confirm_reset_yes": "✅ Yes, reset",
        "confirm_reset_no": "❌ No",
        "confirm_lang_name_ru": "Russian",
        "confirm_lang_name_en": "English",
        "confirm_edit_prompt": "Send new text for: {field}\nMax length: {max_len}",
        "confirm_value_empty": "Text cannot be empty.",
        "confirm_value_too_long": "Text is too long (max {max_len} characters).",
        "confirm_preview_hint": "Preview only — buttons are not active.",
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
        "settings_test_send_nearest_btn": "🧪 Send test reminder for nearest booking",
        "reminder_test_manual_ok": "✅ Test reminders sent for booking #{booking_id} (scheduled flags unchanged).",
        "reminder_test_manual_partial": "⚠️ Only some test reminders were delivered for booking #{booking_id}. Check logs.",
        "reminder_test_manual_fail": "❌ Could not send test reminders. Check logs and Telegram delivery.",
        "reminder_test_manual_no_bookings": "❌ No upcoming bookings found for a test reminder.",
        "reminder_test_manual_hint": "Tip: enable test mode and use scripts/check_reminders.py to see due windows.",
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
        "wh_working_hours_label": "Working hours:",
        "working_breaks_title": "Breaks",
        "working_breaks_empty": "No breaks added.",
        "working_break_add": "➕ Add break",
        "working_break_edit": "✏️ Edit break",
        "working_break_delete": "🗑 Delete break",
        "working_break_toggle": "🔄 Toggle break",
        "working_break_toggle_on": "🔄 Enable",
        "working_break_toggle_off": "🔄 Disable",
        "working_break_start_prompt": "Enter break start time in HH:MM format.\nExample: 12:00",
        "working_break_end_prompt": "Enter break end time in HH:MM format.\nExample: 13:00",
        "working_break_title_prompt": "Break title is optional.\nExample: Lunch\nYou can tap Skip.",
        "working_break_skip_title": "Skip",
        "working_break_added": "Break added.",
        "working_break_updated": "Break updated.",
        "working_break_deleted": "Break deleted.",
        "working_break_invalid_time": "Invalid time. Use HH:MM format.",
        "working_break_invalid_range": "Invalid break time range.",
        "working_break_lunch_preset": "🍽 Lunch 12:00–13:00",
        "working_break_manual": "✏️ Enter manually",
        "working_breaks_summary_none": "no breaks",
        "working_breaks_summary_label": "break",
        "working_break_add_prompt": "Choose how to add a break:",
        "working_break_choose_weekday": "Choose a weekday:",
        "working_break_edit_prompt": "Choose an action:",
        "working_break_edit_time": "✏️ Edit time",
        "working_break_edit_title_btn": "✏️ Edit title",
        "working_break_delete_confirm": "Delete this break?",
        "working_break_delete_yes": "Yes, delete",
        "working_break_delete_no": "Cancel",
        "working_break_back_day": "🔙 Back",
        "working_break_back_list": "🔙 Back",
        "working_break_not_found": "Break not found.",
        "working_break_lunch_title": "Lunch",
        "service_modes_settings_button": "🧩 Service modes",
        "service_modes_title": "🧩 Service modes",
        "service_modes_intro": "Choose which service types are available in the bot.",
        "service_mode_booking": "Date & time booking",
        "service_mode_order": "Orders without date/time",
        "service_mode_booking_on": "✅ Date & time booking",
        "service_mode_booking_off": "❌ Date & time booking",
        "service_mode_order_on": "✅ Orders without date/time",
        "service_mode_order_off": "❌ Orders without date/time",
        "service_mode_cannot_disable_all": "You cannot disable both modes. Keep at least one service type enabled.",
        "service_type_booking": "Service type: 📅 Date & time booking",
        "service_type_order": "Service type: Request without date/time",
        "service_order_no_time_label": "📝 Request without date/time",
        "service_type_booking_btn": "📅 Booking",
        "service_type_order_btn": "📝 Order",
        "service_type_choose_title": "Choose service type",
        "service_type_choose_intro": "📅 Date & time booking — client picks date and time.\n📝 Order request — client submits a request without choosing time.",
        "service_type_change": "🔄 Change service type",
        "service_type_changed": "Service type updated.",
        "service_type_change_warning": "Changing to order type means clients will no longer choose date/time for this service. Existing bookings are kept.",
        "order_button": "📝 Submit request",
        "order_services_button": "🛒 Order service",
        "order_details_prompt": "Please describe what you need.\nExample:\n\"I need a Telegram bot for client bookings\"\nor\n\"I need an app for an online course\"",
        "order_details_required": "Please describe your request.",
        "order_details_label": "Description",
        "order_confirm_title": "📋 Review your request",
        "order_submit": "✅ Submit request",
        "order_edit_data": "✏️ Edit details",
        "order_submitted_client": "✅ Request submitted!\nThe administrator has received your request and will contact you.",
        "order_new_admin_title": "📝 New request",
        "orders_admin_button": "📝 Orders",
        "orders_title": "📝 Orders",
        "orders_hub_intro": "Choose a section:",
        "orders_folder_new": "🆕 New — {count}",
        "orders_folder_in_progress": "🔄 In progress — {count}",
        "orders_folder_completed": "✅ Completed — {count}",
        "orders_folder_cancelled": "❌ Cancelled — {count}",
        "orders_back_hub": "🔙 Back",
        "order_detail_title": "📝 Request",
        "order_status_new": "waiting approval",
        "order_status_accepted": "accepted",
        "order_status_in_progress": "in progress",
        "order_status_completed": "completed",
        "order_status_cancelled": "cancelled",
        "order_status_declined": "declined",
        "order_status_updated": "Status updated.",
        "order_accept_button": "✅ Accept request",
        "order_decline_button": "❌ Decline",
        "order_accepted_admin": "✅ Request accepted.",
        "order_accepted_client": "✅ Your request was accepted",
        "order_accepted_client_body": "The administrator reviewed your request and will contact you soon.\nYou can also send more details about the request in the bot.",
        "order_decline_reason_prompt": "Enter the decline reason for the client.\n\nFor example:\n«Unfortunately, I cannot take this request right now.»\nor\n«This task does not match my services.»",
        "order_declined_admin": "✅ Decline sent to the client.",
        "order_declined_client": "❌ Your request was declined",
        "order_decline_reason_label": "Administrator message:",
        "order_full_info_button": "👁 Full details",
        "order_message_history_button": "👁 Message history",
        "order_write_to_order_button": "✉️ Write about request",
        "order_message_prompt_client": "Write your message about this request:",
        "order_message_prompt_admin": "Write a message to the client about this request:",
        "order_message_sent_client": "✅ Message sent.",
        "order_message_sent_admin": "✅ Message sent to the client.",
        "order_new_message_admin_title": "💬 New message about request",
        "order_new_message_client_title": "💬 Message about your request",
        "order_history_title": "💬 Message history",
        "order_history_empty": "No messages yet.",
        "order_history_sender_client": "Client",
        "order_history_sender_admin": "Admin",
        "order_history_sender_system": "System",
        "order_message_label": "Message:",
        "order_reply_button": "↩️ Reply",
        "order_system_status_accepted": "Request accepted by administrator.",
        "order_system_status_in_progress": "Request marked in progress.",
        "order_system_status_completed": "Request completed.",
        "order_system_status_cancelled": "Request cancelled.",
        "order_system_status_declined": "Request declined by administrator.",
        "orders_folder_declined": "🚫 Declined — {count}",
        "order_mark_in_progress": "🔄 Mark in progress",
        "order_mark_completed": "✅ Complete",
        "order_cancel": "❌ Cancel",
        "order_cancel_client": "❌ Cancel request",
        "order_admin_note": "Admin note",
        "order_admin_note_btn": "📝 Admin note",
        "order_admin_note_prompt": "Enter admin note:",
        "order_admin_note_saved": "Note saved.",
        "order_admin_note_label": "Admin note",
        "order_open_btn": "👁 Open request",
        "order_created_at": "Request date",
        "order_service_fallback": "Service",
        "my_orders_button": "🗂 My requests",
        "my_orders_title": "📝 My requests",
        "my_orders_empty": "You have no requests yet.",
        "my_orders_active_count": "Active requests: {count}",
        "my_orders_history_count": "Request history: {count}",
        "my_orders_choose_section": "Choose a section:",
        "my_orders_active_button": "📂 Active requests — {count}",
        "my_orders_history_button": "📜 Request history — {count}",
        "my_orders_active_title": "📂 Active requests",
        "my_orders_history_title": "📜 Request history",
        "my_orders_empty_active": "You have no active requests.",
        "my_orders_empty_history": "Your request history is empty.",
        "my_orders_back_to_hub": "🔙 Back",
        "my_orders_active_new_summary": "🆕 Waiting approval: {count}",
        "my_orders_active_accepted_summary": "✅ Accepted: {count}",
        "my_orders_active_in_progress_summary": "🔄 In progress: {count}",
        "my_orders_history_completed_summary": "✅ Completed: {count}",
        "my_orders_history_cancelled_summary": "❌ Cancelled: {count}",
        "my_orders_history_declined_summary": "🚫 Declined: {count}",
        "schedule_disabled_booking_off": "Schedule is hidden while date & time booking is disabled.",
        "bookings_disabled_booking_off": "Bookings are hidden while date & time booking is disabled.",
        "message_client_btn": "✉️ Message client",
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
        "main_menu_services": "📋 Выбрать услугу",
        "main_menu_my_activity": "📂 Мои записи и заявки",
        "my_activity_title": "📂 Мои записи и заявки",
        "my_activity_intro": "Выберите раздел:",
        "my_activity_bookings": "📋 Мои записи",
        "my_activity_orders": "🗂 Мои заявки",
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
        "booking_choose_time_period": "Выберите часть дня:",
        "booking_period_morning": "🌅 Утро",
        "booking_period_day": "🌞 День",
        "booking_period_evening": "🌙 Вечер",
        "booking_slots_count": "{count} мест",
        "booking_back_to_dates": "⬅️ К датам",
        "booking_back_to_periods": "⬅️ К частям дня",
        "booking_back_to_service": "⬅️ К услуге",
        "booking_back_to_time": "⬅️ Ко времени",
        "booking_back_to_confirm": "⬅️ К проверке записи",
        "booking_choose_time_in_period": "Выберите время:",
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
        "unknown_action_open_again": "Действие устарело или пока не обработано. Откройте раздел заново.",
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
        "my_bookings_title": "Ваши записи:",
        "my_bookings_empty": "У вас нет активных записей.",
        "client_booking_service_fallback": "Услуга",
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
        "schedule_button": "📅 Расписание",
        "schedule_title": "📅 Расписание и доступность",
        "schedule_wh_section": "🕘 Рабочее время:",
        "schedule_unav_section": "🚫 Ближайшие закрытия:",
        "schedule_unav_empty": "Нет запланированных закрытий.",
        "schedule_unav_more": "…и ещё {count}",
        "schedule_configure_wh": "🕘 Настроить рабочее время",
        "schedule_block_dates": "🚫 Закрыть даты/время",
        "schedule_quick_actions": "⚡ Быстрые действия",
        "schedule_closures_list": "📋 Список закрытий",
        "schedule_back_admin": "🔙 Назад в админ-панель",
        "schedule_quick_title": "⚡ Быстрые действия",
        "admin_working_hours": "🕘 Рабочее время",
        "admin_unavailable": "🚫 Недоступные даты",
        "admin_bookings": "📒 Записи",
        "admin_clients_button": "👥 Клиенты",
        "clients_title": "👥 Клиенты",
        "clients_hub_simplified_title": "👥 Клиенты",
        "clients_hub_simplified_intro": (
            "Здесь собраны все клиенты.\n"
            "Откройте клиента, чтобы увидеть его записи, заявки и контакты."
        ),
        "clients_all_button": "📋 Все клиенты",
        "clients_search_button": "🔎 Поиск клиента",
        "client_tag_new": "🆕",
        "client_tag_repeated": "🔁",
        "client_tag_future_booking": "📅 {count}",
        "client_tag_has_order": "📝 {count}",
        "client_tag_cancelled": "❌ {count}",
        "clients_intro": (
            "Здесь собрана история клиентов: кто был раньше, кто записан впервые, "
            "у кого есть будущие записи."
        ),
        "clients_filter_upcoming": "📅 С будущими записями",
        "clients_filter_visited": "✅ Уже были",
        "clients_filter_new": "🆕 Новые клиенты",
        "clients_filter_returning": "🔁 Повторные клиенты",
        "clients_filter_cancelled": "❌ Отменяли",
        "clients_filter_all": "📋 Все клиенты",
        "clients_search": "🔍 Поиск клиента",
        "clients_no_results": "Клиенты не найдены.",
        "clients_back_admin": "🔙 Назад в админ-панель",
        "clients_back_list": "🔙 Назад к списку",
        "client_callback_invalid": "Раздел клиентов устарел. Откройте Клиенты заново.",
        "booking_back_context_invalid": "Экран устарел. Откройте раздел заново.",
        "calendar_auth_expired_admin_hint": (
            "Google Calendar требует повторной авторизации. Запись сохранена, но событие в календарь не добавлено."
        ),
        "clients_list_new": "🆕 {name} — {count} запись(ей)",
        "clients_list_returning": "🔁 {name} — {count} записей, след. {date}",
        "clients_list_returning_no_next": "🔁 {name} — {count} записей",
        "clients_list_visited": "✅ {name} — был {count} раз(а)",
        "clients_list_cancelled": "❌ {name} — {count} отмен(ы)",
        "client_detail_title": "👤 Клиент",
        "client_name_line": "Имя: {name}",
        "client_phone_line": "Телефон: {phone}",
        "client_username_line": "Username: {username}",
        "client_telegram_id_line": "Telegram ID: {telegram_id}",
        "client_stats_title": "Статистика:",
        "client_total_bookings": "Всего записей: {count}",
        "client_upcoming_count": "Будущих: {count}",
        "client_past_count": "Уже были: {count}",
        "client_cancelled_count": "Отменено: {count}",
        "client_cannot_attend_count": "Не сможет/нужно изменить: {count}",
        "client_first_booking": "Первый раз: {date}",
        "client_last_booking": "Последняя запись: {date}",
        "client_next_booking": "Следующая запись: {date}",
        "client_next_booking_none": "нет",
        "client_status_line": "Статус: {status}",
        "client_status_new": "новый",
        "client_status_returning": "повторный",
        "client_status_visited": "уже был",
        "client_future_bookings": "📅 Будущие записи",
        "client_booking_history": "📜 История записей",
        "client_message_button": "✉️ Написать клиенту",
        "client_send_confirmation_nearest": "🔔 Отправить подтверждение по ближайшей записи",
        "client_no_upcoming_booking": "У клиента нет будущих записей.",
        "client_search_prompt": "Введите имя, телефон, username или Telegram ID клиента.",
        "date_today": "Сегодня",
        "date_tomorrow": "Завтра",
        "booking_id_label": "ID записи: {id}",
        "client_future_booking_row": "#{id} {datetime} — {service} — {status}",
        "client_history_past": "✅ #{id} {datetime} — {service}",
        "client_history_cancelled": "❌ #{id} {datetime} — {service} — отменено",
        "client_history_cannot_attend": "⚠️ #{id} {datetime} — {service} — нужно изменить",
        "admin_calendar": "📆 Настройки календаря",
        "admin_settings": "⚙️ Настройки бота",
        "services_management": "🛠 Услуги",
        "services_hub_intro": "Выберите раздел:",
        "services_folder_active": "✅ Активные услуги — {count}",
        "services_folder_disabled": "🔴 Отключённые услуги — {count}",
        "services_folder_archive": "📦 Архив услуг — {count}",
        "services_search_button": "🔎 Поиск услуги",
        "services_active_title": "✅ Активные услуги",
        "services_disabled_title": "🔴 Отключённые услуги",
        "services_archive_title": "📦 Архив услуг",
        "services_group_booking": "📅 Записи:",
        "services_group_order": "📝 Заявки:",
        "services_search_prompt": "Введите название услуги для поиска:",
        "services_search_no_results": "Услуги не найдены.",
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
        "bookings_hub_title": "📒 Записи",
        "bookings_hub_intro": "Выберите раздел:",
        "bookings_active_summary": "Активные записи: {count}",
        "bookings_pending_summary": "🕓 Ждут решения админа: {count}",
        "bookings_confirmed_summary": "✅ Подтверждённые: {count}",
        "bookings_waiting_client_response_summary": "❔ Ожидают ответа клиента: {count}",
        "bookings_history_summary": "📜 История: {count}",
        "bookings_cancelled_summary": "❌ Отменённые: {count}",
        "bookings_choose_action": "Выберите действие:",
        "bookings_all_active_button": "📋 Все активные записи",
        "bookings_pending_admin_button": "🕓 Ждут решения админа",
        "bookings_search_button": "🔎 Поиск записи",
        "bookings_all_active_title": "📋 Все активные записи",
        "bookings_pending_admin_title": "🕓 Ждут решения админа",
        "bookings_search_prompt": "Введите имя, телефон, услугу или ID записи:",
        "bookings_search_no_results": "Записи не найдены.",
        "bookings_folder_upcoming": "📅 Предстоящие записи",
        "bookings_folder_pending_admin": "🕓 Ожидают решения админа",
        "bookings_folder_confirmed_bookings": "✅ Подтверждённые записи",
        "bookings_folder_waiting_client_response": "❔ Ожидают ответа клиента",
        "bookings_folder_needs_change": "⚠️ Нужно изменить",
        "bookings_folder_history": "📜 История записей",
        "bookings_folder_cancelled": "❌ Отменённые",
        "bookings_pending_admin_intro": "Эти заявки ждут подтверждения администратора.",
        "bookings_confirmed_bookings_intro": "Эти записи подтверждены администратором и активны.",
        "bookings_waiting_client_response_intro": "Эти клиенты ещё не ответили на вопрос о записи.",
        "bookings_folder_needs_change_intro": "Эти клиенты сообщили, что запись нужно изменить или отменить.",
        "bookings_folder_waiting": "❔ Ожидают подтверждения",
        "bookings_folder_confirmed": "✅ Подтверждённые клиентом",
        "bookings_folder_waiting_intro": "Эти клиенты ещё не ответили на подтверждение записи.",
        "bookings_folder_confirmed_intro": "Эти клиенты подтвердили запись.",
        "booking_cancelled_by_client_admin_title": "❌ Клиент отменил запись",
        "booking_cancelled_by_client_admin_status": "отменена клиентом",
        "booking_cancelled_by_admin_client_title": (
            "❌ Ваша запись отменена администратором"
        ),
        "booking_cancelled_by_admin_client_body": (
            "Услуга: {service}\n"
            "Дата и время: {datetime}\n\n"
            "Если у вас есть вопросы, свяжитесь с администратором."
        ),
        "order_cancelled_by_client_admin_title": "❌ Клиент отменил заявку",
        "order_cancelled_by_client_admin_status": "отменена клиентом",
        "order_cancelled_by_admin_client_title": (
            "❌ Ваша заявка отменена администратором"
        ),
        "order_cancelled_by_admin_client_body": (
            "Услуга: {service}\n\n"
            "Если у вас есть вопросы, свяжитесь с администратором."
        ),
        "booking_rescheduled_by_client_admin_title": "🔄 Клиент изменил время записи",
        "booking_status_label": "Статус записи: {status}",
        "client_response_label": "Ответ клиента: {response}",
        "booking_status_pending_admin": "ожидает решения админа",
        "booking_status_confirmed": "подтверждена",
        "booking_status_cancelled": "отменена",
        "client_response_no_response": "нет ответа",
        "client_response_confirmed": "подтвердил",
        "client_response_needs_change": "нужно изменить",
        "bookings_empty_folder": "Записей в этом разделе нет.",
        "bookings_back_to_hub": "🔙 Назад к записям",
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
        "reschedule_back_to_booking": "⬅️ Назад к записи",
        "change_location_btn": "📍 Изменить место",
        "change_address_btn": "🏠 Изменить адрес клиента",
        "change_comment_btn": "💬 Изменить комментарий",
        "back_to_my_bookings": "🔙 Назад к моим записям",
        "confirm_reschedule": (
            "Подтвердить перенос записи?\n"
            "Было: {old_datetime}\n"
            "Стало: {new_datetime}"
        ),
        "reschedule_was_line": "Было: {datetime}",
        "reschedule_became_line": "Стало: {datetime}",
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
        "attendance_yes_button": "✅ Подтверждаю",
        "attendance_no_button": "❌ Нужно изменить",
        "attendance_prompt": "Подтвердите, пожалуйста, актуальность вашей записи.",
        "attendance_reminder_title": "🔔 Подтверждение записи",
        "attendance_reminder_intro": "У вас запланирована запись:",
        "attendance_reminder_service": "Услуга: {service}",
        "attendance_reminder_datetime": "Дата и время: {date_time}",
        "attendance_reminder_service_location": "Место: {title}",
        "attendance_reminder_service_location_address": "\nАдрес: {address}",
        "attendance_reminder_client_address": "Адрес: {address}",
        "attendance_reminder_response_confirmed": "Ответ клиента: подтверждено",
        "attendance_reminder_response_cannot": "Ответ клиента: не сможет прийти",
        "attendance_confirmed_client": "✅ Спасибо! Администратор получил подтверждение.",
        "attendance_confirmed_admin": (
            "✅ Клиент подтвердил запись\n"
            "Клиент: {client_name}\n"
            "Телефон: {phone}\n"
            "Услуга: {service}\n"
            "Дата и время: {date_time}"
        ),
        "attendance_cannot_attend_admin": (
            "⚠️ Клиент сообщил, что запись нужно изменить\n"
            "Клиент: {client_name}\n"
            "Телефон: {phone}\n"
            "Услуга: {service}\n"
            "Дата и время: {date_time}"
        ),
        "attendance_action_prompt": "Что вы хотите сделать с записью?",
        "attendance_reschedule_button": "🔁 Перенести запись",
        "attendance_cancel_button": "❌ Отменить запись",
        "attendance_reason_button": "💬 Указать причину",
        "attendance_keep_button": "🔙 Оставить как есть",
        "attendance_reason_prompt": "Напишите причину, почему не сможете прийти.",
        "attendance_reason_saved": "Причина сохранена. Администратор уведомлён.",
        "attendance_reason_too_long": "Слишком длинный текст (макс. {max_len} символов).",
        "attendance_keep_saved": (
            "Хорошо, запись оставлена без изменений. Администратор уже получил ваш ответ."
        ),
        "attendance_unavailable": "Эта запись уже недоступна.",
        "attendance_status_confirmed": "✅ Клиент подтвердил запись",
        "attendance_status_cannot_attend": "⚠️ Клиент сообщил, что запись нужно изменить",
        "attendance_status_reason": "Причина: {reason}",
        "attendance_client_response_confirmed": "Ответ на напоминание: подтверждено",
        "attendance_client_response_cannot": "Ответ на напоминание: не сможет прийти",
        "attendance_reason_admin": (
            "💬 Клиент указал причину\n"
            "Клиент: {client_name}\n"
            "Телефон: {phone}\n"
            "Услуга: {service}\n"
            "Дата и время: {date_time}\n"
            "Причина: {reason}"
        ),
        "attendance_reschedule_fallback": (
            "Чтобы перенести запись, откройте «Мои записи» и выберите «Перенести», либо напишите администратору."
        ),
        "attendance_manual_title": "🔔 Подтверждение записи",
        "attendance_manual_intro": "У вас запланирована запись:",
        "admin_attendance_button": "🔔 Подтверждение записи",
        "admin_attendance_title": "🔔 Подтверждение записи",
        "admin_attendance_filter_today": "🔥 Сегодня",
        "admin_attendance_filter_tomorrow": "⏰ Завтра",
        "admin_attendance_filter_7d": "📅 7 дней",
        "admin_attendance_filter_all": "🗓 Все будущие",
        "admin_attendance_filter_no_response": "❔ Без ответа",
        "admin_attendance_section_today": "🔥 Сегодня",
        "admin_attendance_section_tomorrow": "⏰ Завтра",
        "admin_attendance_section_week": "📅 Ближайшие 7 дней",
        "admin_attendance_section_later": "🗓 Позже",
        "admin_attendance_no_bookings": "Нет подходящих предстоящих записей.",
        "admin_attendance_send_question": "🔔 Отправить вопрос подтверждения",
        "admin_attendance_sent": "✅ Вопрос отправлен клиенту.",
        "admin_attendance_send_failed": "❌ Не удалось отправить вопрос. Возможно, клиент заблокировал бота.",
        "admin_attendance_already_answered_confirm": "Клиент уже ответил. Отправить вопрос ещё раз?",
        "admin_attendance_resend_yes": "✅ Да, отправить",
        "admin_attendance_resend_no": "❌ Нет",
        "admin_attendance_client_response": "Ответ клиента: {response}",
        "admin_attendance_no_response": "нет ответа",
        "admin_attendance_client_response_confirmed": "подтверждено",
        "admin_attendance_client_response_cannot": "не сможет прийти",
        "admin_attendance_client_response_reason": "указана причина",
        "admin_attendance_booking_line": "Запись: #{booking_id}",
        "admin_attendance_client_line": "Клиент: {client_name}",
        "admin_attendance_phone_line": "Телефон: {phone}",
        "admin_attendance_service_line": "Услуга: {service}",
        "admin_attendance_datetime_line": "Дата и время: {date_time}",
        "admin_attendance_reason_line": "Причина: {reason}",
        "admin_attendance_manual_info": "Отправлено вручную: {count} раз(а)",
        "admin_attendance_back_to_list": "🔙 Назад к списку",
        "pagination_prev": "⬅️ Назад",
        "pagination_next": "Далее ➡️",
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
        "client_data_settings_button": "👤 Данные клиента",
        "client_data_settings_title": "👤 Данные клиента",
        "client_data_settings_intro": "Настройте, какие данные бот будет использовать при записи.",
        "client_use_telegram_name": "✅ Имя из Telegram: {value}",
        "client_confirm_telegram_name": "✅ Подтверждать имя: {value}",
        "client_phone_request_contact": "✅ Кнопка телефона Telegram: {value}",
        "client_phone_manual_input": "✅ Ручной ввод телефона: {value}",
        "client_phone_required": "✅ Телефон обязателен: {value}",
        "client_fast_reuse_saved_data": "✅ Быстрая запись для повторных клиентов: {value}",
        "client_data_toggle_fast_on": "✅ Быстрая запись",
        "client_data_toggle_fast_off": "❌ Быстрая запись",
        "client_data_preview_step_fast_reuse": "{step}. Если клиент уже есть в базе, бот сразу покажет подтверждение записи с сохранённым именем и телефоном.",
        "booking_review_title": "📋 Проверьте запись:",
        "booking_edit_details": "✏️ Изменить данные",
        "booking_edit_what": "Что хотите изменить?",
        "booking_edit_name": "👤 Имя",
        "booking_edit_phone": "📞 Телефон",
        "booking_edit_address": "📍 Адрес клиента",
        "booking_edit_comment": "💬 Комментарий",
        "booking_edit_back_to_confirm": "🔙 Назад к подтверждению",
        "client_data_preview": "👁 Предпросмотр сценария",
        "client_data_invalid_phone_config": "Нельзя отключить оба способа ввода телефона, если телефон обязателен.",
        "client_data_toggle_use_name_on": "✅ Использовать имя из Telegram",
        "client_data_toggle_use_name_off": "❌ Использовать имя из Telegram",
        "client_data_toggle_confirm_name_on": "✅ Подтверждать имя",
        "client_data_toggle_confirm_name_off": "❌ Подтверждать имя",
        "client_data_toggle_contact_on": "✅ Кнопка «Поделиться номером»",
        "client_data_toggle_contact_off": "❌ Кнопка «Поделиться номером»",
        "client_data_toggle_manual_on": "✅ Ручной ввод телефона",
        "client_data_toggle_manual_off": "❌ Ручной ввод телефона",
        "client_data_toggle_required_on": "✅ Телефон обязателен",
        "client_data_toggle_required_off": "❌ Телефон обязателен",
        "client_data_preview_title": "Сценарий записи",
        "client_data_preview_step_confirm_name": "{step}. Бот предложит имя из Telegram и спросит подтверждение.",
        "client_data_preview_step_auto_name": "{step}. Бот автоматически использует имя из Telegram.",
        "client_data_preview_step_manual_name": "{step}. Бот попросит ввести имя.",
        "client_data_preview_step_phone_both": "{step}. Бот предложит поделиться номером Telegram или ввести вручную.",
        "client_data_preview_step_phone_contact": "{step}. Бот предложит кнопку «Поделиться номером».",
        "client_data_preview_step_phone_manual": "{step}. Бот попросит ввести телефон вручную.",
        "client_data_preview_step_phone_optional": "{step}. Телефон необязателен — клиент может пропустить.",
        "client_data_preview_step_phone_required_missing": "{step}. Телефон обязателен, но способ ввода не настроен.",
        "client_data_preview_step_confirm": "{step}. Клиент перейдёт к подтверждению записи.",
        "booking_use_telegram_name_prompt": "Ваше имя в Telegram: {telegram_full_name}\nИспользовать это имя для записи?",
        "booking_use_telegram_name_yes": "✅ Да, использовать",
        "booking_enter_other_name": "✏️ Ввести другое имя",
        "booking_saved_phone_prompt": "Ваш сохранённый номер: {phone}\nИспользовать его?",
        "booking_use_saved_phone": "✅ Да, использовать",
        "booking_share_phone": "📱 Поделиться номером Telegram",
        "booking_share_phone_button": "📱 Поделиться номером",
        "booking_enter_phone_manual": "✏️ Ввести вручную",
        "booking_skip_phone": "⏭ Пропустить",
        "booking_contact_prompt": "Поделитесь номером через кнопку ниже или введите вручную.",
        "booking_manual_phone_prompt": "Введите номер телефона.",
        "booking_wrong_contact": "❌ Отправьте, пожалуйста, свой номер телефона через кнопку.",
        "booking_phone_received": "✅ Номер получен.",
        "booking_phone_not_provided": "не указан",
        "booking_phone_source_telegram": "Telegram",
        "booking_phone_source_manual": "вручную",
        "admin_booking_telegram_line": "🔗 Telegram: {username}",
        "client_telegram_name_line": "Имя в Telegram: {name}",
        "client_phone_source_line": "Источник телефона: {source}",
        "client_last_seen_line": "Последний визит: {datetime}",
        "client_open_telegram_profile": "👤 Открыть профиль Telegram",
        "confirm_settings_button": "🔔 Подтверждение записи",
        "confirm_settings_title": "🔔 Подтверждение записи",
        "confirm_settings_title_lang": "🔔 Подтверждение записи — {target_lang}",
        "confirm_settings_intro": (
            "Настройте текст вопроса и кнопок, которые клиент видит "
            "в напоминании или при ручной отправке вопроса."
        ),
        "confirm_select_language": "Выберите язык для настройки:",
        "confirm_current_texts": "Текущие тексты:",
        "confirm_current_title": "Заголовок: {value}",
        "confirm_current_question": "Вопрос: {value}",
        "confirm_button_confirm": "Кнопка подтверждения: {value}",
        "confirm_button_change": "Кнопка изменения: {value}",
        "confirm_group_main_text": "✏️ Основной текст",
        "confirm_group_responses": "💬 Ответы и уведомления",
        "confirm_preview_btn": "👁 Предпросмотр",
        "confirm_preview_ru": "👁 Предпросмотр RU",
        "confirm_preview_en": "👁 Preview EN",
        "confirm_reset_btn": "♻️ Сбросить",
        "confirm_back": "🔙 Назад",
        "confirm_back_to_confirmation": "🔙 Назад",
        "confirm_edit_title_plain": "✏️ Заголовок",
        "confirm_edit_question_plain": "✏️ Вопрос",
        "confirm_edit_confirm_button": "✏️ Кнопка подтверждения",
        "confirm_edit_change_button": "✏️ Кнопка изменения",
        "confirm_edit_client_confirm_response": "✏️ Ответ клиенту после подтверждения",
        "confirm_edit_client_change_prompt": "✏️ Текст после «нужно изменить»",
        "confirm_edit_admin_confirm_notice": "✏️ Уведомление админу: подтверждено",
        "confirm_edit_admin_change_notice": "✏️ Уведомление админу: нужно изменить",
        "confirm_reset_confirm_text": "Сбросить настройки подтверждения записи для {target_lang}?",
        "confirm_reset_yes": "✅ Да, сбросить",
        "confirm_reset_no": "❌ Нет",
        "confirm_lang_name_ru": "русского языка",
        "confirm_lang_name_en": "английского языка",
        "confirm_edit_prompt": "Отправьте новый текст: {field}\nМакс. длина: {max_len}",
        "confirm_value_empty": "Текст не может быть пустым.",
        "confirm_value_too_long": "Слишком длинный текст (макс. {max_len} символов).",
        "confirm_preview_hint": "Только предпросмотр — кнопки неактивны.",
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
        "settings_test_send_nearest_btn": "🧪 Отправить тестовое напоминание по ближайшей записи",
        "reminder_test_manual_ok": "✅ Тестовые напоминания отправлены по записи #{booking_id} (флаги расписания не изменены).",
        "reminder_test_manual_partial": "⚠️ Часть тестовых напоминаний не доставлена по записи #{booking_id}. Смотрите логи.",
        "reminder_test_manual_fail": "❌ Не удалось отправить тестовые напоминания. Проверьте логи и доставку в Telegram.",
        "reminder_test_manual_no_bookings": "❌ Нет предстоящих записей для тестового напоминания.",
        "reminder_test_manual_hint": "Подсказка: включите тестовый режим и запустите scripts/check_reminders.py для проверки окон.",
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
        "wh_working_hours_label": "Рабочее время:",
        "working_breaks_title": "Перерывы",
        "working_breaks_empty": "Перерывы не добавлены.",
        "working_break_add": "➕ Добавить перерыв",
        "working_break_edit": "✏️ Изменить перерыв",
        "working_break_delete": "🗑 Удалить перерыв",
        "working_break_toggle": "🔄 Включить/выключить",
        "working_break_toggle_on": "🔄 Включить",
        "working_break_toggle_off": "🔄 Выключить",
        "working_break_start_prompt": "Введите начало перерыва в формате HH:MM.\nНапример: 12:00",
        "working_break_end_prompt": "Введите конец перерыва в формате HH:MM.\nНапример: 13:00",
        "working_break_title_prompt": "Название перерыва необязательно.\nНапример: Обед\nМожно нажать Пропустить.",
        "working_break_skip_title": "Пропустить",
        "working_break_added": "Перерыв добавлен.",
        "working_break_updated": "Перерыв обновлён.",
        "working_break_deleted": "Перерыв удалён.",
        "working_break_invalid_time": "Неверное время. Используйте формат HH:MM.",
        "working_break_invalid_range": "Неверный интервал перерыва.",
        "working_break_lunch_preset": "🍽 Обед 12:00–13:00",
        "working_break_manual": "✏️ Ввести вручную",
        "working_breaks_summary_none": "без перерывов",
        "working_breaks_summary_label": "перерыв",
        "working_break_add_prompt": "Выберите способ добавления перерыва:",
        "working_break_choose_weekday": "Выберите день недели:",
        "working_break_edit_prompt": "Выберите действие:",
        "working_break_edit_time": "✏️ Изменить время",
        "working_break_edit_title_btn": "✏️ Изменить название",
        "working_break_delete_confirm": "Удалить этот перерыв?",
        "working_break_delete_yes": "Да, удалить",
        "working_break_delete_no": "Отмена",
        "working_break_back_day": "🔙 Назад",
        "working_break_back_list": "🔙 Назад",
        "working_break_not_found": "Перерыв не найден.",
        "working_break_lunch_title": "Обед",
        "service_modes_settings_button": "🧩 Режимы услуг",
        "service_modes_title": "🧩 Режимы услуг",
        "service_modes_intro": "Выберите, какие типы услуг доступны в боте.",
        "service_mode_booking": "Запись по дате и времени",
        "service_mode_order": "Заявки без даты и времени",
        "service_mode_booking_on": "✅ Запись по дате и времени",
        "service_mode_booking_off": "❌ Запись по дате и времени",
        "service_mode_order_on": "✅ Заявки без даты и времени",
        "service_mode_order_off": "❌ Заявки без даты и времени",
        "service_mode_cannot_disable_all": "Нельзя отключить оба режима. Оставьте хотя бы один тип услуг.",
        "service_type_booking": "Тип услуги: 📅 Запись по времени",
        "service_type_order": "Тип услуги: Заявка без даты и времени",
        "service_order_no_time_label": "📝 Заявка без даты и времени",
        "service_type_booking_btn": "📅 Запись",
        "service_type_order_btn": "📝 Заявка",
        "service_type_choose_title": "Выберите тип услуги",
        "service_type_choose_intro": "📅 Запись по дате и времени — клиент выбирает дату и время.\n📝 Заявка без даты и времени — клиент оставляет заявку без выбора времени.",
        "service_type_change": "🔄 Изменить тип услуги",
        "service_type_changed": "Тип услуги обновлён.",
        "service_type_change_warning": "При смене на заявку клиенты больше не будут выбирать дату и время. Существующие записи сохранятся.",
        "order_button": "📝 Оставить заявку",
        "order_services_button": "🛒 Заказать услугу",
        "order_details_prompt": "Опишите, пожалуйста, что вам нужно.\nНапример:\n«Хочу Telegram-бота для записи клиентов»\nили\n«Нужно приложение для онлайн-курса»",
        "order_details_required": "Пожалуйста, опишите заявку.",
        "order_details_label": "Описание",
        "order_confirm_title": "📋 Проверьте заявку",
        "order_submit": "✅ Отправить заявку",
        "order_edit_data": "✏️ Изменить данные",
        "order_submitted_client": "✅ Заявка отправлена!\nАдминистратор получил вашу заявку и свяжется с вами.",
        "order_new_admin_title": "📝 Новая заявка",
        "orders_admin_button": "📝 Заявки",
        "orders_title": "📝 Заявки",
        "orders_hub_intro": "Выберите раздел:",
        "orders_folder_new": "🆕 Новые — {count}",
        "orders_folder_in_progress": "🔄 В работе — {count}",
        "orders_folder_completed": "✅ Завершённые — {count}",
        "orders_folder_cancelled": "❌ Отменённые — {count}",
        "orders_back_hub": "🔙 Назад",
        "order_detail_title": "📝 Заявка",
        "order_status_new": "ожидает решения",
        "order_status_accepted": "принята",
        "order_status_in_progress": "в работе",
        "order_status_completed": "завершена",
        "order_status_cancelled": "отменена",
        "order_status_declined": "отказано",
        "order_status_updated": "Статус обновлён.",
        "order_accept_button": "✅ Принять заявку",
        "order_decline_button": "❌ Отказать",
        "order_accepted_admin": "✅ Заявка принята.",
        "order_accepted_client": "✅ Ваша заявка принята",
        "order_accepted_client_body": "Администратор рассмотрел вашу заявку и скоро свяжется с вами.\nВы также можете написать детали по заявке в боте.",
        "order_decline_reason_prompt": "Напишите причину отказа для клиента.\n\nНапример:\n«К сожалению, сейчас не смогу выполнить эту услугу.»\nили\n«Эта задача не подходит под мои услуги.»",
        "order_declined_admin": "✅ Отказ отправлен клиенту.",
        "order_declined_client": "❌ По вашей заявке отказ",
        "order_decline_reason_label": "Сообщение администратора:",
        "order_full_info_button": "👁 Полная информация",
        "order_message_history_button": "👁 История сообщений",
        "order_write_to_order_button": "✉️ Написать по заявке",
        "order_message_prompt_client": "Напишите сообщение по этой заявке:",
        "order_message_prompt_admin": "Напишите сообщение клиенту по этой заявке:",
        "order_message_sent_client": "✅ Сообщение отправлено.",
        "order_message_sent_admin": "✅ Сообщение отправлено клиенту.",
        "order_new_message_admin_title": "💬 Новое сообщение по заявке",
        "order_new_message_client_title": "💬 Сообщение по вашей заявке",
        "order_history_title": "💬 История сообщений",
        "order_history_empty": "Сообщений пока нет.",
        "order_history_sender_client": "Клиент",
        "order_history_sender_admin": "Админ",
        "order_history_sender_system": "Система",
        "order_message_label": "Сообщение:",
        "order_reply_button": "↩️ Ответить",
        "order_system_status_accepted": "Заявка принята администратором.",
        "order_system_status_in_progress": "Заявка переведена в работу.",
        "order_system_status_completed": "Заявка завершена.",
        "order_system_status_cancelled": "Заявка отменена.",
        "order_system_status_declined": "Заявка отклонена администратором.",
        "orders_folder_declined": "🚫 Отказы — {count}",
        "order_mark_in_progress": "🔄 В работу",
        "order_mark_completed": "✅ Завершить",
        "order_cancel": "❌ Отменить",
        "order_cancel_client": "❌ Отменить заявку",
        "order_admin_note": "Заметка админа",
        "order_admin_note_btn": "📝 Заметка админа",
        "order_admin_note_prompt": "Введите заметку администратора:",
        "order_admin_note_saved": "Заметка сохранена.",
        "order_admin_note_label": "Заметка админа",
        "order_open_btn": "👁 Открыть заявку",
        "order_created_at": "Дата заявки",
        "order_service_fallback": "Услуга",
        "my_orders_button": "🗂 Мои заявки",
        "my_orders_title": "📝 Мои заявки",
        "my_orders_empty": "У вас пока нет заявок.",
        "my_orders_active_count": "Активные заявки: {count}",
        "my_orders_history_count": "История заявок: {count}",
        "my_orders_choose_section": "Выберите раздел:",
        "my_orders_active_button": "📂 Активные заявки — {count}",
        "my_orders_history_button": "📜 История заявок — {count}",
        "my_orders_active_title": "📂 Активные заявки",
        "my_orders_history_title": "📜 История заявок",
        "my_orders_empty_active": "У вас нет активных заявок.",
        "my_orders_empty_history": "История заявок пока пустая.",
        "my_orders_back_to_hub": "🔙 Назад",
        "my_orders_active_new_summary": "🆕 Ожидает решения: {count}",
        "my_orders_active_accepted_summary": "✅ Принятые: {count}",
        "my_orders_active_in_progress_summary": "🔄 В работе: {count}",
        "my_orders_history_completed_summary": "✅ Завершённые: {count}",
        "my_orders_history_cancelled_summary": "❌ Отменённые: {count}",
        "my_orders_history_declined_summary": "🚫 Отказы: {count}",
        "schedule_disabled_booking_off": "Расписание скрыто, пока отключена запись по дате и времени.",
        "bookings_disabled_booking_off": "Записи скрыты, пока отключена запись по дате и времени.",
        "message_client_btn": "✉️ Написать клиенту",
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
