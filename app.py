"""
EF101-P07: Classroom/Laboratory Booking System
Backend Web Application (Flask + SQLite)

Simple, elegant architecture for first-year students:
- User & Admin Roles with separate panels
- Fixed Admin Credentials: username='mehtab', password='mehtab2026'
- User Sign Up (unique username, email, phone, password >= 8 chars)
- User Sign In (username or email + password)
- Users only see & cancel their own bookings
- Admin manages rooms (Show, Add, Edit, Delete), inspects all users & bookings
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date, timedelta
import os
import database

app = Flask(__name__)
# Secret key for secure session storage and flash messages
app.secret_key = "ef101-classroom-booking-secret-key-2026"

# Ensure the database and demo data exist when the app starts
database.init_db(force_reset=False)
check_time_conflict = database.check_time_conflict


# ---------------------------------------------------------
# Access Control: Require Login for Protected Pages
# ---------------------------------------------------------

@app.before_request
def require_login():
    """
    Ensure the first thing a visitor sees is the login page.
    Public routes: 'login', 'register', 'static'.
    """
    public_endpoints = ["login", "register", "static"]
    if request.endpoint and request.endpoint not in public_endpoints:
        if "user_id" not in session:
            return redirect(url_for("login"))


# Context processor to make current user info available in all templates
@app.context_processor
def inject_user():
    return {
        "current_user": {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
            "role": session.get("role")
        }
    }


# ---------------------------------------------------------
# Authentication Routes (Login, Register, Logout)
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page: Asks user to log in as User or Admin.
    - Admin: Fixed username='mehtab', password='mehtab2026'
    - User: username or email + password
    """
    # If already logged in, redirect to dashboard or admin
    if "user_id" in session:
        if session.get("role") == "Admin":
            return redirect(url_for("admin_panel"))
        return redirect(url_for("index"))

    if request.method == "POST":
        login_type = request.form.get("login_type", "user")

        # 1. ADMIN LOGIN
        if login_type == "admin":
            admin_user = request.form.get("admin_username", "").strip()
            admin_pass = request.form.get("admin_password", "").strip()

            # Check database for admin credentials or fixed fallback
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users
                WHERE (username = ? OR email = ?) AND password = ? AND role = 'Admin'
            """, (admin_user, admin_user, admin_pass))
            admin_row = cursor.fetchone()
            conn.close()

            if admin_row or (admin_user == "mehtab" and admin_pass == "mehtab2026"):
                session["user_id"] = admin_row["id"] if admin_row else 1
                session["username"] = admin_row["username"] if admin_row else "mehtab"
                session["user_name"] = admin_row["name"] if admin_row else "System Administrator"
                session["user_email"] = admin_row["email"] if admin_row else "admin@university.edu"
                session["role"] = "Admin"
                flash("Welcome to Administrator Control Panel!", "success")
                return redirect(url_for("admin_panel"))
            else:
                flash("Invalid Administrator username or password.", "danger")
                return render_template("login.html", active_tab="admin")

        # 2. USER SIGN IN
        else:
            login_id = request.form.get("login_id", "").strip()  # username or email
            password = request.form.get("password", "").strip()

            if not (login_id and password):
                flash("Please enter both username/email and password.", "warning")
                return render_template("login.html", active_tab="user")

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users
                WHERE (username = ? OR email = ?) AND password = ?
            """, (login_id, login_id, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]
                session["role"] = user["role"]

                if user["role"] == "Admin":
                    flash("Welcome, Administrator!", "success")
                    return redirect(url_for("admin_panel"))
                else:
                    flash(f"Welcome back, {user['name']}!", "success")
                    return redirect(url_for("index"))
            else:
                flash("Invalid username/email or password. Please try again or Sign Up.", "danger")
                return render_template("login.html", active_tab="user", login_id=login_id)

    return render_template("login.html", active_tab="user")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Sign Up for new users:
    - Required: Full Name, username, email, phone, password, confirm_password
    - All of username, email, phone must be UNIQUE
    - Password must be at least 8 characters
    """
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # 1. Check all fields filled
        if not (name and username and email and phone and password and confirm_password):
            flash("All fields are required. Please complete the registration form.", "warning")
            return render_template("register.html", form_data=request.form)

        # 2. Password matching check
        if password != confirm_password:
            flash("Passwords do not match! Please verify your password.", "danger")
            return render_template("register.html", form_data=request.form)

        # 3. Password length >= 8 characters
        if len(password) < 8:
            flash("Password must be at least 8 characters long (letters, numbers, or mix).", "danger")
            return render_template("register.html", form_data=request.form)

        # 4. Check uniqueness of username, email, and phone
        conn = database.get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            flash(f"Username '{username}' is already taken! Please choose a different username.", "danger")
            return render_template("register.html", form_data=request.form)

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash(f"Email '{email}' is already registered! Please use another email or sign in.", "danger")
            return render_template("register.html", form_data=request.form)

        cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        if cursor.fetchone():
            conn.close()
            flash(f"Phone number '{phone}' is already registered in the system!", "danger")
            return render_template("register.html", form_data=request.form)

        # 5. Insert new user
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (username, password, name, email, phone, role, created_at)
            VALUES (?, ?, ?, ?, ?, 'User', ?)
        """, (username, password, name, email, phone, now_ts))
        conn.commit()
        conn.close()

        flash("Registration successful! You can now sign in with your new account.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    """
    Log out the current user or admin and clear session.
    """
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------
# User Panel Routes
# ---------------------------------------------------------

@app.route("/")
def index():
    """
    User Dashboard: Stats overview, quick room search, and today's schedule preview.
    """
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'")
    active_bookings = cursor.fetchone()[0]

    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT b.*, r.name as room_name, r.location 
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.booking_date = ? AND b.status = 'Confirmed'
        ORDER BY b.start_time ASC
    """, (today_str,))
    todays_bookings = cursor.fetchall()

    cursor.execute("SELECT * FROM rooms LIMIT 6")
    featured_rooms = cursor.fetchall()

    cursor.execute("SELECT DISTINCT room_type FROM rooms ORDER BY room_type")
    room_types = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template(
        "index.html",
        total_rooms=total_rooms,
        active_bookings=active_bookings,
        todays_bookings=todays_bookings,
        featured_rooms=featured_rooms,
        room_types=room_types,
        today=today_str
    )


@app.route("/rooms")
def rooms_list():
    """
    View room/lab list & details. Filter by capacity, room type, or equipment.
    """
    conn = database.get_db()
    cursor = conn.cursor()

    selected_type = request.args.get("type", "").strip()
    min_capacity = request.args.get("capacity", "").strip()
    equipment_keyword = request.args.get("equipment", "").strip()
    search_text = request.args.get("q", "").strip()

    query = "SELECT * FROM rooms WHERE 1=1"
    params = []

    if selected_type:
        query += " AND room_type = ?"
        params.append(selected_type)
    if min_capacity and min_capacity.isdigit():
        query += " AND capacity >= ?"
        params.append(int(min_capacity))
    if equipment_keyword:
        query += " AND equipment LIKE ?"
        params.append(f"%{equipment_keyword}%")
    if search_text:
        query += " AND (id LIKE ? OR name LIKE ? OR location LIKE ?)"
        wildcard = f"%{search_text}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    rooms = cursor.fetchall()

    cursor.execute("SELECT DISTINCT room_type FROM rooms ORDER BY room_type")
    all_types = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template(
        "rooms.html",
        rooms=rooms,
        all_types=all_types,
        selected_type=selected_type,
        min_capacity=min_capacity,
        equipment_keyword=equipment_keyword,
        search_text=search_text,
        result_count=len(rooms)
    )


@app.route("/room/<room_id>")
def room_detail(room_id):
    """
    View individual room details, full equipment specs, and upcoming bookings.
    """
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = cursor.fetchone()

    if not room:
        conn.close()
        flash("Room not found!", "danger")
        return redirect(url_for("rooms_list"))

    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT * FROM bookings
        WHERE room_id = ? AND booking_date >= ? AND status = 'Confirmed'
        ORDER BY booking_date ASC, start_time ASC
        LIMIT 10
    """, (room_id, today_str))
    upcoming_bookings = cursor.fetchall()

    conn.close()
    return render_template("room_detail.html", room=room, upcoming_bookings=upcoming_bookings)


@app.route("/check-availability", methods=["GET"])
def check_availability():
    """
    Select date, start time, end time -> Display availability for the requested period.
    """
    today_str = date.today().isoformat()
    now_str = datetime.now().strftime("%H:%M")
    check_date = request.args.get("date", today_str)

    if check_date < today_str:
        flash(f"Note: {check_date} has already passed. Reset to today ({today_str}).", "warning")
        check_date = today_str

    start_time = request.args.get("start_time", "09:00")
    end_time = request.args.get("end_time", "11:00")
    room_type = request.args.get("type", "")
    min_cap = request.args.get("capacity", "")

    conn = database.get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM rooms WHERE 1=1"
    params = []
    if room_type:
        query += " AND room_type = ?"
        params.append(room_type)
    if min_cap and min_cap.isdigit():
        query += " AND capacity >= ?"
        params.append(int(min_cap))
    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    all_rooms = cursor.fetchall()

    available_rooms = []
    booked_rooms = []

    for r in all_rooms:
        conflict = check_time_conflict(r["id"], check_date, start_time, end_time)
        if conflict:
            booked_rooms.append({"room": r, "conflict": conflict})
        else:
            available_rooms.append(r)

    cursor.execute("SELECT DISTINCT room_type FROM rooms ORDER BY room_type")
    all_types = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template(
        "availability.html",
        check_date=check_date,
        start_time=start_time,
        end_time=end_time,
        room_type=room_type,
        min_cap=min_cap,
        available_rooms=available_rooms,
        booked_rooms=booked_rooms,
        all_types=all_types,
        today=today_str,
        now_time=now_str
    )


@app.route("/book", methods=["GET", "POST"])
def book_room():
    """
    Create a booking.
    - User details (name, email) automatically linked from session.
    - Rejects invalid time ranges and past dates/times.
    - Prevents double-booking / overlapping reservations.
    """
    conn = database.get_db()
    cursor = conn.cursor()

    today_date_str = date.today().isoformat()
    current_time_str = datetime.now().strftime("%H:%M")

    if request.method == "POST":
        room_id = request.form.get("room_id", "").strip()
        booking_date = request.form.get("booking_date", "").strip()
        start_time = request.form.get("start_time", "").strip()
        end_time = request.form.get("end_time", "").strip()
        purpose = request.form.get("purpose", "").strip()

        # Logged-in user information
        user_name = session.get("user_name", "Student User")
        user_email = session.get("user_email", "student@university.edu")
        user_id = session.get("user_id", 1)

        # 1. Required fields
        if not (room_id and booking_date and start_time and end_time and purpose):
            flash("All fields are required. Please fill in the complete form.", "warning")
            return redirect(request.url)

        # 2. Time range validation (end_time > start_time)
        if end_time <= start_time:
            flash("Invalid Time Range: The end time must be strictly after the start time!", "danger")
            return redirect(request.url)

        # 3. Reject past dates & times
        if booking_date < today_date_str:
            flash(f"Invalid Date: You cannot reserve a room for a past date ({booking_date})!", "danger")
            cursor.execute("SELECT * FROM rooms ORDER BY id ASC")
            rooms = cursor.fetchall()
            conn.close()
            return render_template("book.html", rooms=rooms, form_data=request.form, today=today_date_str, now_time=current_time_str)

        if booking_date == today_date_str and start_time < current_time_str:
            flash(f"Invalid Time: You cannot reserve for a time that has already passed today! (Current: {current_time_str}, Start: {start_time})", "danger")
            cursor.execute("SELECT * FROM rooms ORDER BY id ASC")
            rooms = cursor.fetchall()
            conn.close()
            return render_template("book.html", rooms=rooms, form_data=request.form, today=today_date_str, now_time=current_time_str)

        # 4. Check room existence
        cursor.execute("SELECT name FROM rooms WHERE id = ?", (room_id,))
        room = cursor.fetchone()
        if not room:
            flash(f"Room '{room_id}' does not exist.", "danger")
            return redirect(request.url)

        # 5. Conflict / Overlap Prevention
        conflict = check_time_conflict(room_id, booking_date, start_time, end_time)
        if conflict:
            flash(
                f"Booking Conflict! Room {room_id} is already reserved by {conflict['user_name']} "
                f"from {conflict['start_time']} to {conflict['end_time']} "
                f"for '{conflict['purpose']}'. Please choose another room or time.",
                "danger"
            )
            cursor.execute("SELECT * FROM rooms ORDER BY id ASC")
            rooms = cursor.fetchall()
            conn.close()
            return render_template("book.html", rooms=rooms, form_data=request.form, today=today_date_str, now_time=current_time_str)

        # 6. Save reservation to SQLite
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO bookings (room_id, user_id, user_name, user_email, booking_date, start_time, end_time, purpose, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?)
        """, (room_id, user_id, user_name, user_email, booking_date, start_time, end_time, purpose, now_ts))

        conn.commit()
        conn.close()

        flash(f"Success! Room {room_id} has been reserved successfully for {booking_date} ({start_time} - {end_time}).", "success")
        return redirect(url_for("my_bookings"))

    # GET request
    selected_room_id = request.args.get("room_id", "")
    preset_date = request.args.get("date", today_date_str)
    if preset_date < today_date_str:
        preset_date = today_date_str

    preset_start = request.args.get("start_time", "09:00")
    preset_end = request.args.get("end_time", "11:00")

    cursor.execute("SELECT * FROM rooms ORDER BY id ASC")
    rooms = cursor.fetchall()
    conn.close()

    return render_template(
        "book.html",
        rooms=rooms,
        selected_room_id=selected_room_id,
        preset_date=preset_date,
        preset_start=preset_start,
        preset_end=preset_end,
        today=today_date_str,
        now_time=current_time_str
    )


@app.route("/my-bookings")
def my_bookings():
    """
    User Panel: Users see ONLY their own bookings.
    """
    user_email = session.get("user_email")
    user_id = session.get("user_id")

    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.*, r.name as room_name, r.location, r.room_type 
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.user_id = ? OR b.user_email = ?
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, (user_id, user_email))

    bookings = cursor.fetchall()
    conn.close()

    return render_template("my_bookings.html", bookings=bookings)


@app.route("/cancel-booking/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    """
    Cancel booking:
    - Regular Users can ONLY cancel their OWN bookings.
    - Admins can cancel any booking.
    """
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        flash("Booking not found.", "danger")
        return redirect(request.referrer or url_for("my_bookings"))

    # Security check: User can only cancel their own booking
    is_admin = session.get("role") == "Admin"
    is_owner = (booking["user_id"] == session.get("user_id")) or (booking["user_email"] == session.get("user_email"))

    if not (is_admin or is_owner):
        conn.close()
        flash("Unauthorized: You can only cancel your own bookings!", "danger")
        return redirect(url_for("my_bookings"))

    cursor.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

    flash(f"Booking #{booking_id} for room {booking['room_id']} has been cancelled. The time slot is now open!", "info")
    return redirect(request.referrer or url_for("my_bookings"))


@app.route("/schedule")
def schedule_view():
    """
    Daily and Weekly timetable schedule views.
    """
    view_type = request.args.get("view", "day")
    selected_date_str = request.args.get("date", date.today().isoformat())
    selected_room_id = request.args.get("room_id", "")

    try:
        current_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        current_date = date.today()
        selected_date_str = current_date.isoformat()

    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rooms ORDER BY id ASC")
    rooms = cursor.fetchall()

    if view_type == "week":
        start_of_week = current_date - timedelta(days=current_date.weekday())
        week_days = [start_of_week + timedelta(days=i) for i in range(7)]
        week_dates_str = [d.isoformat() for d in week_days]

        query = """
            SELECT b.*, r.name as room_name 
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.booking_date BETWEEN ? AND ?
              AND b.status = 'Confirmed'
        """
        params = [week_dates_str[0], week_dates_str[-1]]
        if selected_room_id:
            query += " AND b.room_id = ?"
            params.append(selected_room_id)
        query += " ORDER BY b.start_time ASC"

        cursor.execute(query, params)
        week_bookings = cursor.fetchall()

        bookings_by_day = {d_str: [] for d_str in week_dates_str}
        for b in week_bookings:
            if b["booking_date"] in bookings_by_day:
                bookings_by_day[b["booking_date"]].append(b)

        prev_week = (current_date - timedelta(days=7)).isoformat()
        next_week = (current_date + timedelta(days=7)).isoformat()

        conn.close()
        return render_template(
            "schedule.html",
            view_type="week",
            current_date=current_date,
            week_days=week_days,
            bookings_by_day=bookings_by_day,
            rooms=rooms,
            selected_room_id=selected_room_id,
            prev_date=prev_week,
            next_date=next_week
        )
    else:
        cursor.execute("""
            SELECT b.*, r.name as room_name 
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.booking_date = ?
              AND b.status = 'Confirmed'
            ORDER BY b.start_time ASC
        """, (selected_date_str,))
        day_bookings = cursor.fetchall()

        room_schedules = {r["id"]: [] for r in rooms}
        for b in day_bookings:
            if b["room_id"] in room_schedules:
                room_schedules[b["room_id"]].append(b)

        prev_day = (current_date - timedelta(days=1)).isoformat()
        next_day = (current_date + timedelta(days=1)).isoformat()

        time_slots = [f"{hour:02d}:00" for hour in range(8, 21)]

        conn.close()
        return render_template(
            "schedule.html",
            view_type="day",
            current_date=current_date,
            rooms=rooms,
            room_schedules=room_schedules,
            time_slots=time_slots,
            prev_date=prev_day,
            next_date=next_day
        )


# ---------------------------------------------------------
# Administrator Panel Routes
# ---------------------------------------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    """
    Administrator Control Panel:
    - Inspect all reservations
    - View all registered users with details
    - Manage rooms: Add, Edit, Delete
    """
    if session.get("role") != "Admin":
        flash("Access Denied: You must be an Administrator to access this page.", "danger")
        return redirect(url_for("index"))

    conn = database.get_db()
    cursor = conn.cursor()

    # Handle Adding a New Room
    if request.method == "POST" and request.form.get("action") == "add_room":
        room_id = request.form.get("room_id", "").strip().upper()
        name = request.form.get("name", "").strip()
        room_type = request.form.get("room_type", "").strip()
        location = request.form.get("location", "").strip()
        capacity = request.form.get("capacity", "").strip()
        equipment = request.form.get("equipment", "").strip()
        description = request.form.get("description", "").strip()

        if not (room_id and name and room_type and location and capacity and equipment):
            flash("All room fields are required to add a new room.", "danger")
        else:
            try:
                cursor.execute("""
                    INSERT INTO rooms (id, name, room_type, location, capacity, equipment, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (room_id, name, room_type, location, int(capacity), equipment, description))
                conn.commit()
                flash(f"Room {room_id} added successfully!", "success")
            except Exception as e:
                flash(f"Error adding room: Room ID '{room_id}' might already exist. ({e})", "danger")
        return redirect(url_for("admin_panel"))

    # Fetch all rooms
    cursor.execute("SELECT * FROM rooms ORDER BY id ASC")
    rooms = cursor.fetchall()

    # Fetch all users + their total booking count
    cursor.execute("""
        SELECT u.*, COUNT(b.id) as booking_count
        FROM users u
        LEFT JOIN bookings b ON (u.id = b.user_id OR u.email = b.user_email)
        GROUP BY u.id
        ORDER BY u.id ASC
    """)
    users = cursor.fetchall()

    # Fetch all bookings with status filter
    status_filter = request.args.get("status", "All")
    if status_filter in ["Confirmed", "Cancelled"]:
        cursor.execute("""
            SELECT b.*, r.name as room_name 
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.status = ?
            ORDER BY b.booking_date DESC, b.start_time DESC
        """, (status_filter,))
    else:
        cursor.execute("""
            SELECT b.*, r.name as room_name 
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            ORDER BY b.booking_date DESC, b.start_time DESC
        """)
    all_bookings = cursor.fetchall()
    conn.close()

    return render_template(
        "admin.html",
        rooms=rooms,
        users=users,
        all_bookings=all_bookings,
        status_filter=status_filter
    )


@app.route("/admin/user/<int:user_id>")
def admin_user_details(user_id):
    """
    Admin: View complete details for a specific user and all their reservations,
    with the ability to cancel any booking.
    """
    if session.get("role") != "Admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("index"))

    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        flash("User not found.", "danger")
        return redirect(url_for("admin_panel"))

    # Fetch all bookings made by this user
    cursor.execute("""
        SELECT b.*, r.name as room_name, r.location 
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.user_id = ? OR b.user_email = ?
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, (user_id, user["email"]))
    user_bookings = cursor.fetchall()

    conn.close()
    return render_template("admin_user_detail.html", user=user, user_bookings=user_bookings)


@app.route("/admin/room/<room_id>/edit", methods=["POST"])
def admin_edit_room(room_id):
    """
    Admin: Edit existing room details (capacity, type, location, equipment).
    """
    if session.get("role") != "Admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("index"))

    name = request.form.get("name", "").strip()
    room_type = request.form.get("room_type", "").strip()
    location = request.form.get("location", "").strip()
    capacity = request.form.get("capacity", "").strip()
    equipment = request.form.get("equipment", "").strip()
    description = request.form.get("description", "").strip()

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE rooms
        SET name = ?, room_type = ?, location = ?, capacity = ?, equipment = ?, description = ?
        WHERE id = ?
    """, (name, room_type, location, int(capacity), equipment, description, room_id))
    conn.commit()
    conn.close()

    flash(f"Room {room_id} has been updated successfully.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/room/<room_id>/delete", methods=["POST"])
def admin_delete_room(room_id):
    """
    Admin: Delete a room from the system.
    """
    if session.get("role") != "Admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("index"))

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()

    flash(f"Room {room_id} has been deleted from the database.", "info")
    return redirect(url_for("admin_panel"))


# ---------------------------------------------------------
# Bonus Feature: Door Kiosk Display
# ---------------------------------------------------------

@app.route("/kiosk/<room_id>")
def room_kiosk(room_id):
    """
    Bonus Feature: Public Door Placard Display
    Shows live FREE / OCCUPIED status and today's schedule.
    """
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        return "Room not found", 404

    today_str = date.today().isoformat()
    now_time = datetime.now().strftime("%H:%M")

    cursor.execute("""
        SELECT * FROM bookings
        WHERE room_id = ?
          AND booking_date = ?
          AND status = 'Confirmed'
          AND start_time <= ? AND end_time > ?
    """, (room_id, today_str, now_time, now_time))
    current_occupant = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM bookings
        WHERE room_id = ? AND booking_date = ? AND status = 'Confirmed'
        ORDER BY start_time ASC
    """, (room_id, today_str))
    today_schedule = cursor.fetchall()

    conn.close()
    return render_template(
        "kiosk.html",
        room=room,
        current_occupant=current_occupant,
        today_schedule=today_schedule,
        now_time=now_time,
        today_str=today_str
    )


if __name__ == "__main__":
    import webbrowser
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    url = f"http://127.0.0.1:{port}"
    print("=" * 65)
    print("  EF101-P07 Classroom/Laboratory Booking System Web Application")
    print(f"  Running on: http://{host}:{port}")
    print("  Press Ctrl+C in terminal to stop the server.")
    print("=" * 65)

    if host == "127.0.0.1":
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            pass
    app.run(debug=False, use_reloader=False, host=host, port=port)
