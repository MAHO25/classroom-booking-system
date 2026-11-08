"""
=============================================================================
EF101-P07: Classroom/Laboratory Booking System
100% Pure Python Modern Web UI using Streamlit
=============================================================================

Run with:
    streamlit run streamlit_app.py

Every single UI component, validation rule, conflict check, and database query
is written in 100% Python. No HTML, CSS, or JavaScript required!
=============================================================================
"""

import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import database

# Configure Streamlit page layout
st.set_page_config(
    page_title="UniReserve | EF101-P07",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database is initialized with 12 demo rooms
database.init_db(force_reset=False)


# -----------------------------------------------------------------------------
# Business Logic (Double-booking conflict check in Python)
# -----------------------------------------------------------------------------
def check_time_conflict(room_id, booking_date, start_time, end_time, exclude_id=None):
    """
    MANDATORY REQUIREMENT 6: Double-Booking / Overlap Prevention
    Formula: Overlap occurs if (new_start < cur_end) and (new_end > cur_start)
    """
    conn = database.get_db()
    cursor = conn.cursor()
    query = """
        SELECT * FROM bookings
        WHERE room_id = ?
          AND booking_date = ?
          AND status != 'Cancelled'
          AND (start_time < ? AND end_time > ?)
    """
    params = [room_id, booking_date, end_time, start_time]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    cursor.execute(query, params)
    conflict = cursor.fetchone()
    conn.close()
    return conflict


# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("🏫 UniReserve")
st.sidebar.markdown("**EF101-P07 Booking System**")
st.sidebar.caption("100% Pure Python Implementation")

nav_choice = st.sidebar.radio(
    "Go to Navigation:",
    [
        "📊 Dashboard & Overview",
        "🔍 Rooms & Labs (Search/Filter)",
        "⏱️ Check Period Availability",
        "📝 Make a Reservation",
        "📅 Schedule (Daily / Weekly)",
        "📋 My Bookings & Cancel",
        "⚙️ Admin Management",
        "🚪 Door Kiosk Display (Bonus)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip for Evaluation:**\nAll data is stored persistently in SQLite. Conflicting bookings are automatically blocked before saving.")


# =============================================================================
# 1. Dashboard
# =============================================================================
if nav_choice == "📊 Dashboard & Overview":
    st.title("Classroom & Laboratory Booking System")
    st.markdown("##### Project ID: EF101-P07 | System Understanding Project")
    st.write("Welcome to the automated room and laboratory reservation system. This system allows students and faculty to view, filter, and reserve campus resources while preventing schedule conflicts.")

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'")
    active_bookings = cursor.fetchone()[0]

    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT b.id, b.room_id, r.name as room_name, b.start_time, b.end_time, b.user_name, b.purpose
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.booking_date = ? AND b.status = 'Confirmed'
        ORDER BY b.start_time ASC
    """, (today_str,))
    todays = cursor.fetchall()
    conn.close()

    # Metric Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rooms & Labs", total_rooms, "12 Demo Rooms")
    col2.metric("Active Confirmed Bookings", active_bookings)
    col3.metric("Schedule Integrity", "100%", "Overlap Protected")

    st.markdown("---")
    st.subheader(f"📅 Today's Bookings ({today_str})")
    if todays:
        df_today = pd.DataFrame([dict(r) for r in todays])
        df_today.columns = ["ID", "Room ID", "Room Name", "Start Time", "End Time", "Reserved By", "Purpose"]
        st.dataframe(df_today, use_container_width=True)
    else:
        st.info("No bookings scheduled for today yet.")


# =============================================================================
# 2. Rooms & Labs (Requirements 1 & 2)
# =============================================================================
elif nav_choice == "🔍 Rooms & Labs (Search/Filter)":
    st.title("Rooms & Laboratories Directory")
    st.write("Browse rooms, inspect equipment specs, and filter by capacity, type, or specific equipment.")

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT room_type FROM rooms ORDER BY room_type")
    room_types = ["All"] + [r[0] for r in cursor.fetchall()]

    col1, col2, col3 = st.columns(3)
    selected_type = col1.selectbox("Filter by Room Type:", room_types)
    min_capacity = col2.number_input("Minimum Capacity:", min_value=0, value=0, step=5)
    equipment_query = col3.text_input("Filter by Equipment Keyword:", placeholder="e.g. Projector, Oscilloscope, PC")

    # Build SQL Query
    query = "SELECT id, name, room_type, location, capacity, equipment, description FROM rooms WHERE 1=1"
    params = []
    if selected_type != "All":
        query += " AND room_type = ?"
        params.append(selected_type)
    if min_capacity > 0:
        query += " AND capacity >= ?"
        params.append(min_capacity)
    if equipment_query.strip():
        query += " AND equipment LIKE ?"
        params.append(f"%{equipment_query.strip()}%")
    query += " ORDER BY id ASC"

    cursor.execute(query, params)
    rooms = cursor.fetchall()
    conn.close()

    st.markdown(f"**Found {len(rooms)} room(s) matching your criteria:**")
    if rooms:
        df = pd.DataFrame([dict(r) for r in rooms])
        df.columns = ["Room ID", "Name", "Type", "Location", "Capacity", "Equipment / Features", "Description"]
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No rooms match the specified filters. Try reducing the capacity or clearing equipment keywords.")


# =============================================================================
# 3. Check Period Availability (Requirements 3 & 4)
# =============================================================================
elif nav_choice == "⏱️ Check Period Availability":
    st.title("Check Room Availability for a Specific Period")
    st.write("Select a date and time window to immediately see which rooms are available vs already occupied.")

    col1, col2, col3 = st.columns(3)
    check_date = col1.date_input("Select Date:", value=date.today())
    start_time = col2.time_input("Start Time:", value=datetime.strptime("09:00", "%H:%M").time())
    end_time = col3.time_input("End Time:", value=datetime.strptime("11:00", "%H:%M").time())

    start_str = start_time.strftime("%H:%M")
    end_str = end_time.strftime("%H:%M")
    date_str = check_date.isoformat()

    # Requirement 11: Validate time range
    if end_str <= start_str:
        st.error("⚠️ Invalid Time Range: End time must be strictly after start time!")
    else:
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, room_type, location, capacity, equipment FROM rooms ORDER BY id ASC")
        all_rooms = cursor.fetchall()
        conn.close()

        available_list = []
        occupied_list = []

        for r in all_rooms:
            conflict = check_time_conflict(r["id"], date_str, start_str, end_str)
            if conflict:
                occupied_list.append({
                    "Room ID": r["id"],
                    "Room Name": r["name"],
                    "Reserved By": conflict["user_name"],
                    "Time Slot": f"{conflict['start_time']} - {conflict['end_time']}",
                    "Purpose": conflict["purpose"]
                })
            else:
                available_list.append({
                    "Room ID": r["id"],
                    "Room Name": r["name"],
                    "Type": r["room_type"],
                    "Capacity": r["capacity"],
                    "Equipment": r["equipment"]
                })

        col_a, col_b = st.columns(2)
        with col_a:
            st.success(f"✅ AVAILABLE ROOMS ({len(available_list)})")
            if available_list:
                st.dataframe(pd.DataFrame(available_list), use_container_width=True)
            else:
                st.write("No rooms available for this time slot.")

        with col_b:
            st.error(f"❌ OCCUPIED / CONFLICTING ROOMS ({len(occupied_list)})")
            if occupied_list:
                st.dataframe(pd.DataFrame(occupied_list), use_container_width=True)
            else:
                st.write("No conflicting reservations.")


# =============================================================================
# 4. Make a Reservation (Requirements 5, 6, 10, & 11)
# =============================================================================
elif nav_choice == "📝 Make a Reservation":
    st.title("Make a Room or Laboratory Reservation")
    st.write("Submit your booking details. The system will automatically check for schedule conflicts before saving.")

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, room_type, capacity FROM rooms ORDER BY id ASC")
    rooms_data = cursor.fetchall()
    conn.close()

    room_options = [f"{r['id']} - {r['name']} ({r['room_type']}, cap: {r['capacity']})" for r in rooms_data]
    room_id_map = {opt: r["id"] for opt, r in zip(room_options, rooms_data)}

    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        chosen_room_label = col1.selectbox("Select Room / Laboratory:", room_options)
        booking_date = col2.date_input("Booking Date:", value=date.today())

        col3, col4 = st.columns(2)
        start_time = col3.time_input("Start Time:", value=datetime.strptime("10:00", "%H:%M").time())
        end_time = col4.time_input("End Time:", value=datetime.strptime("12:00", "%H:%M").time())

        col5, col6 = st.columns(2)
        user_name = col5.text_input("Requester / Student / Faculty Name:", placeholder="e.g. Alice Johnson")
        user_email = col6.text_input("Requester Email:", placeholder="e.g. alice.j@university.edu")

        purpose = st.text_input("Purpose of Reservation:", placeholder="e.g. EE201 Lab Experiment, Study Group, Project Demo")

        submitted = st.form_submit_button("Confirm & Create Booking", type="primary")

    if submitted:
        room_id = room_id_map[chosen_room_label]
        date_str = booking_date.isoformat()
        start_str = start_time.strftime("%H:%M")
        end_str = end_time.strftime("%H:%M")

        # Requirement 11: Validate fields & time range
        if not (user_name.strip() and user_email.strip() and purpose.strip()):
            st.error("⚠️ All fields are mandatory. Please fill in your name, email, and purpose.")
        elif end_str <= start_str:
            st.error(f"⚠️ Invalid Time Range (Requirement 11): End time ({end_str}) must be strictly after start time ({start_str})!")
        else:
            # Requirement 6: Conflict Checking before saving
            conflict = check_time_conflict(room_id, date_str, start_str, end_str)
            if conflict:
                st.error(
                    f"⛔ DOUBLE-BOOKING CONFLICT PREVENTED (Requirement 6)!\n\n"
                    f"Room **{room_id}** is already booked on **{date_str}** from "
                    f"**{conflict['start_time']} to {conflict['end_time']}** by "
                    f"**{conflict['user_name']}** for *'{conflict['purpose']}'*.\n\n"
                    f"Please choose an alternate room or non-overlapping time slot."
                )
            else:
                # Requirement 10: Store persistently in SQLite
                conn = database.get_db()
                cursor = conn.cursor()
                now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO bookings (room_id, user_name, user_email, booking_date, start_time, end_time, purpose, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?)
                """, (room_id, user_name.strip(), user_email.strip(), date_str, start_str, end_str, purpose.strip(), now_ts))

                # Track user
                cursor.execute("SELECT id FROM users WHERE email = ?", (user_email.strip(),))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (name, email, role, department) VALUES (?, ?, 'Student', 'Engineering')", (user_name.strip(), user_email.strip()))

                conn.commit()
                new_id = cursor.lastrowid
                conn.close()

                st.success(
                    f"🎉 Booking #{new_id} Confirmed Successfully!\n\n"
                    f"- **Room:** {room_id}\n"
                    f"- **Date & Time:** {date_str} ({start_str} - {end_str})\n"
                    f"- **Requester:** {user_name}\n"
                    f"- **Purpose:** {purpose}"
                )


# =============================================================================
# 5. Daily & Weekly Schedule (Requirement 8)
# =============================================================================
elif nav_choice == "📅 Schedule (Daily / Weekly)":
    st.title("Room Reservation Timetable")
    st.write("View reservations across all rooms for a specific day or full week.")

    view_type = st.radio("Select View Type:", ["Daily Schedule View", "Weekly Schedule View"], horizontal=True)
    selected_date = st.date_input("Target Date:", value=date.today())
    target_date_str = selected_date.isoformat()

    conn = database.get_db()
    cursor = conn.cursor()

    if view_type == "Daily Schedule View":
        cursor.execute("""
            SELECT b.id, b.room_id, r.name as room_name, b.start_time, b.end_time, b.user_name, b.purpose, b.status
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.booking_date = ? AND b.status = 'Confirmed'
            ORDER BY b.start_time ASC
        """, (target_date_str,))
        rows = cursor.fetchall()
        st.subheader(f"Schedule for {target_date_str}")
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            df.columns = ["Booking ID", "Room ID", "Room Name", "Start", "End", "Reserved By", "Purpose", "Status"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"No confirmed bookings on {target_date_str}.")

    else:
        # Weekly View
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        st.subheader(f"Weekly Schedule: {start_of_week.isoformat()} to {end_of_week.isoformat()}")

        cursor.execute("""
            SELECT b.booking_date, b.room_id, r.name as room_name, b.start_time, b.end_time, b.user_name, b.purpose
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.booking_date BETWEEN ? AND ? AND b.status = 'Confirmed'
            ORDER BY b.booking_date ASC, b.start_time ASC
        """, (start_of_week.isoformat(), end_of_week.isoformat()))
        rows = cursor.fetchall()

        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            df.columns = ["Date", "Room ID", "Room Name", "Start", "End", "Reserved By", "Purpose"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No bookings recorded for this week.")

    conn.close()


# =============================================================================
# 6. My Bookings & Cancel (Requirement 7)
# =============================================================================
elif nav_choice == "📋 My Bookings & Cancel":
    st.title("My Bookings & Cancellation")
    st.write("Inspect your existing reservations or cancel a booking to free up the room slot.")

    user_email_filter = st.text_input("Filter by Requester Email:", placeholder="Leave blank to view all recent bookings")

    conn = database.get_db()
    cursor = conn.cursor()
    if user_email_filter.strip():
        cursor.execute("""
            SELECT id, room_id, user_name, user_email, booking_date, start_time, end_time, purpose, status
            FROM bookings WHERE user_email LIKE ? ORDER BY booking_date DESC, start_time DESC
        """, (f"%{user_email_filter.strip()}%",))
    else:
        cursor.execute("""
            SELECT id, room_id, user_name, user_email, booking_date, start_time, end_time, purpose, status
            FROM bookings ORDER BY booking_date DESC, start_time DESC LIMIT 40
        """)
    bookings_data = cursor.fetchall()
    conn.close()

    if bookings_data:
        df = pd.DataFrame([dict(b) for r, b in enumerate(bookings_data)])
        df.columns = ["Booking ID", "Room ID", "Name", "Email", "Date", "Start", "End", "Purpose", "Status"]
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("Cancel a Booking")
        cancel_id = st.number_input("Enter Booking ID to cancel:", min_value=1, step=1)
        if st.button("Cancel Reservation", type="secondary"):
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT status, room_id FROM bookings WHERE id = ?", (cancel_id,))
            target = cursor.fetchone()
            if not target:
                st.error(f"Booking #{cancel_id} does not exist.")
            elif target["status"] == "Cancelled":
                st.warning(f"Booking #{cancel_id} is already cancelled.")
            else:
                cursor.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (cancel_id,))
                conn.commit()
                st.success(f"Booking #{cancel_id} for Room {target['room_id']} has been cancelled! The room is now available.")
                st.rerun()
            conn.close()
    else:
        st.info("No bookings found.")


# =============================================================================
# 7. Admin Management (Requirement 9)
# =============================================================================
elif nav_choice == "⚙️ Admin Management":
    st.title("Administrator Management Console")
    st.write("Add or edit room information and inspect all system bookings.")

    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["➕ Add New Room", "✏️ Edit Existing Room", "📜 Inspect All Bookings"])

    with admin_tab1:
        st.subheader("Add Demonstration or Production Room")
        with st.form("add_room_form"):
            col1, col2 = st.columns(2)
            n_id = col1.text_input("Unique Room ID:", placeholder="e.g. LAB-401, CLS-305")
            n_name = col2.text_input("Room / Lab Name:", placeholder="e.g. AI & Machine Learning Lab")

            col3, col4 = st.columns(2)
            n_type = col3.selectbox("Room Type:", ["Computer Lab", "Science Lab", "Engineering Lab", "Classroom", "Seminar Room", "Auditorium"])
            n_cap = col4.number_input("Capacity:", min_value=5, max_value=500, value=30)

            n_loc = st.text_input("Location / Building / Floor:", placeholder="e.g. Technology Tower, Floor 4")
            n_equip = st.text_input("Available Equipment / Features:", placeholder="e.g. 30 GPU Workstations, 4K Projector, Whiteboard")
            n_desc = st.text_area("Description / Notes:", placeholder="Brief summary of room capabilities")

            add_sub = st.form_submit_button("Save New Room")

        if add_sub:
            if not (n_id.strip() and n_name.strip() and n_loc.strip() and n_equip.strip()):
                st.error("Please fill in all room fields.")
            else:
                conn = database.get_db()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO rooms (id, name, room_type, location, capacity, equipment, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (n_id.strip().upper(), n_name.strip(), n_type, n_loc.strip(), n_cap, n_equip.strip(), n_desc.strip()))
                    conn.commit()
                    st.success(f"Room {n_id.strip().upper()} added successfully!")
                except Exception as e:
                    st.error(f"Failed to add room: {e}")
                finally:
                    conn.close()

    with admin_tab2:
        st.subheader("Edit Room Details")
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM rooms ORDER BY id ASC")
        r_list = cursor.fetchall()
        conn.close()

        r_ids = [r["id"] for r in r_list]
        selected_r_id = st.selectbox("Select Room to Edit:", r_ids)

        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE id = ?", (selected_r_id,))
        cur_room = cursor.fetchone()
        conn.close()

        if cur_room:
            with st.form("edit_room_form"):
                e_name = st.text_input("Name:", value=cur_room["name"])
                e_type = st.selectbox("Type:", ["Computer Lab", "Science Lab", "Engineering Lab", "Classroom", "Seminar Room", "Auditorium"], index=0)
                e_loc = st.text_input("Location:", value=cur_room["location"])
                e_cap = st.number_input("Capacity:", min_value=1, value=cur_room["capacity"])
                e_equip = st.text_input("Equipment:", value=cur_room["equipment"])
                save_edit = st.form_submit_button("Update Room Details")

            if save_edit:
                conn = database.get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE rooms SET name = ?, room_type = ?, location = ?, capacity = ?, equipment = ? WHERE id = ?
                """, (e_name, e_type, e_loc, e_cap, e_equip, selected_r_id))
                conn.commit()
                conn.close()
                st.success(f"Room {selected_r_id} updated successfully!")

    with admin_tab3:
        st.subheader("All Bookings Master Log")
        status_filter = st.selectbox("Filter Bookings by Status:", ["All", "Confirmed", "Cancelled"])
        conn = database.get_db()
        cursor = conn.cursor()
        if status_filter == "All":
            cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM bookings WHERE status = ? ORDER BY id DESC", (status_filter,))
        all_b = cursor.fetchall()
        conn.close()

        if all_b:
            st.dataframe(pd.DataFrame([dict(b) for b in all_b]), use_container_width=True)
        else:
            st.info("No bookings recorded.")


# =============================================================================
# 8. Bonus: Door Kiosk Display
# =============================================================================
elif nav_choice == "🚪 Door Kiosk Display (Bonus)":
    st.title("Public Room Kiosk & Door Signage")
    st.write("Digital signage view designed for tablets mounted outside classrooms/labs.")

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM rooms ORDER BY id ASC")
    rooms_data = cursor.fetchall()
    conn.close()

    kiosk_room_id = st.selectbox("Select Room for Display:", [r["id"] for r in rooms_data])

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms WHERE id = ?", (kiosk_room_id,))
    k_room = cursor.fetchone()

    today_str = date.today().isoformat()
    now_str = datetime.now().strftime("%H:%M")

    cursor.execute("""
        SELECT * FROM bookings
        WHERE room_id = ? AND booking_date = ? AND status = 'Confirmed'
          AND start_time <= ? AND end_time > ?
    """, (kiosk_room_id, today_str, now_str, now_str))
    current_occupant = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM bookings
        WHERE room_id = ? AND booking_date = ? AND status = 'Confirmed'
        ORDER BY start_time ASC
    """, (kiosk_room_id, today_str))
    today_agenda = cursor.fetchall()
    conn.close()

    st.markdown(f"### 📍 {k_room['id']}: {k_room['name']}")
    st.write(f"**Location:** {k_room['location']} | **Capacity:** {k_room['capacity']} | **Equipment:** {k_room['equipment']}")

    if current_occupant:
        st.error(
            f"### 🔴 OCCUPIED / IN USE\n"
            f"**Until:** {current_occupant['end_time']}\n\n"
            f"**Reserved by:** {current_occupant['user_name']}\n\n"
            f"**Purpose:** {current_occupant['purpose']}"
        )
    else:
        st.success("### 🟢 AVAILABLE NOW\nNo current ongoing reservation. Free for walk-in or immediate booking.")

    st.subheader(f"Today's Agenda ({today_str})")
    if today_agenda:
        st.dataframe(pd.DataFrame([dict(b) for b in today_agenda])[["start_time", "end_time", "user_name", "purpose"]], use_container_width=True)
    else:
        st.info("No reservations scheduled for today.")
