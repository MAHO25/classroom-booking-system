"""
Database setup and utility module for Classroom/Laboratory Booking System.
Designed to be clean, simple, and easy for 1st-year university students to understand.
Uses Python's standard 'sqlite3' library (no heavy ORM required).
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "booking_system.db")


def get_db():
    """
    Connect to the SQLite database.
    row_factory = sqlite3.Row allows accessing columns by name: row['capacity'].
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Enable foreign key support in SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def check_time_conflict(room_id, booking_date, start_time, end_time, exclude_booking_id=None):
    """
    MANDATORY REQUIREMENT 6: Double-Booking / Overlap Prevention
    
    Formula for time overlap between interval [new_start, new_end] and [cur_start, cur_end]:
        Overlap occurs IF AND ONLY IF:
            (new_start < cur_end) AND (new_end > cur_start)
    """
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT * FROM bookings
        WHERE room_id = ?
          AND booking_date = ?
          AND status != 'Cancelled'
          AND (start_time < ? AND end_time > ?)
    """
    params = [room_id, booking_date, end_time, start_time]
    if exclude_booking_id:
        query += " AND id != ?"
        params.append(exclude_booking_id)

    cursor.execute(query, params)
    conflict = cursor.fetchone()
    conn.close()
    return conflict


def init_db(force_reset=False):
    """
    Initialize the database tables and seed with demonstration data.
    If database already exists and has rooms, it will not overwrite unless force_reset=True.
    """
    if force_reset and os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = get_db()
    cursor = conn.cursor()

    # Check if existing schema needs upgrade (e.g. users table missing username)
    try:
        cursor.execute("SELECT username FROM users LIMIT 1")
    except Exception:
        # Recreate tables if old schema detected
        cursor.execute("DROP TABLE IF EXISTS bookings")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS rooms")

    # 1. Rooms Table
    # Mandatory Data: ID/name, location (building+floor), capacity, room type, available equipment
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            room_type TEXT NOT NULL,
            location TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            equipment TEXT NOT NULL,
            description TEXT
        )
    """)

    # 2. Users Table
    # Stores both regular users and admin with unique username, email, phone, and password >= 8 chars
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL DEFAULT 'User',
            created_at TEXT NOT NULL
        )
    """)

    # 3. Bookings Table
    # Mandatory: requester, room, date/time, purpose, status for cancellation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            user_id INTEGER,
            user_name TEXT NOT NULL,
            user_email TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            purpose TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Check if rooms already exist; if not, seed demonstration data
    cursor.execute("SELECT COUNT(*) FROM rooms")
    room_count = cursor.fetchone()[0]

    if room_count == 0:
        _seed_demo_data(cursor)

    # Ensure admin credentials are set to 'mehtab' / 'mehtab2026'
    cursor.execute("""
        UPDATE users
        SET username = 'mehtab', password = 'mehtab2026'
        WHERE role = 'Admin' OR username = 'admin'
    """)

    conn.commit()
    conn.close()


def _seed_demo_data(cursor):
    """
    Seed at least 10 realistic demonstration rooms and initial bookings.
    """
    demo_rooms = [
        (
            "LAB-101",
            "Computer Science Lab A",
            "Computer Lab",
            "Engineering Building, Floor 1",
            35,
            "35 High-End PCs, Projector, Gigabit LAN, Whiteboard",
            "Equipped with modern programming software and fast network access.",
        ),
        (
            "LAB-102",
            "Computer Science Lab B",
            "Computer Lab",
            "Engineering Building, Floor 1",
            30,
            "30 PCs, Smart Board, Audio System, Linux Workstations",
            "Optimized for systems programming and data science courses.",
        ),
        (
            "LAB-201",
            "Electronics & Circuits Lab",
            "Engineering Lab",
            "Science Complex, Floor 2",
            25,
            "12 Oscilloscopes, Function Generators, Soldering Stations, DC Power Supplies",
            "For electrical circuits, microcontrollers, and signal experiments.",
        ),
        (
            "LAB-202",
            "Robotics & IoT Lab",
            "Engineering Lab",
            "Science Complex, Floor 2",
            20,
            "3D Printers, Arduino/Raspberry Pi Kits, Projector, Soldering Station",
            "Specialized workshop space for hardware prototyping and robotics.",
        ),
        (
            "LAB-301",
            "Chemistry Laboratory",
            "Science Lab",
            "Science Complex, Floor 3",
            24,
            "Fume Hoods, Bunsen Burners, Chemical Reagents, Safety Showers, Analytical Balances",
            "Certified chemistry wet lab with complete safety containment.",
        ),
        (
            "LAB-302",
            "Physics & Optics Laboratory",
            "Science Lab",
            "Science Complex, Floor 3",
            28,
            "Optics Benches, Lasers, Spectrometers, Digital Multimeters, Projector",
            "Equipped for experiments in mechanics, thermodynamics, and optics.",
        ),
        (
            "CLS-101",
            "General Classroom 101",
            "Classroom",
            "Academic Hall A, Floor 1",
            50,
            "Projector, Whiteboard, Podium Mic, Air Conditioning",
            "Standard spacious lecture room with ergonomic desk seating.",
        ),
        (
            "CLS-102",
            "General Classroom 102",
            "Classroom",
            "Academic Hall A, Floor 1",
            45,
            "Smart TV, Whiteboard, Audio System, Air Conditioning",
            "Interactive medium-sized classroom suitable for tutorial sessions.",
        ),
        (
            "CLS-201",
            "Seminar Room A",
            "Seminar Room",
            "Academic Hall B, Floor 2",
            30,
            "Interactive Smart Board, Video Conference Camera, High-Speed WiFi, Whiteboard",
            "Designed for workshops, guest lectures, and hybrid meetings.",
        ),
        (
            "CLS-202",
            "Seminar Room B",
            "Seminar Room",
            "Academic Hall B, Floor 2",
            25,
            "Projector, Round Discussion Tables, Whiteboard",
            "Flexible room layout ideal for group discussions and team projects.",
        ),
        (
            "AUD-101",
            "Main University Auditorium",
            "Auditorium",
            "Central Campus Building, Floor 1",
            200,
            "Dual 4K Projectors, Surround Sound System, Stage Lighting, Wireless Mics",
            "Large capacity hall for keynote events, conferences, and examinations.",
        ),
        (
            "AUD-102",
            "Mini Lecture Hall",
            "Auditorium",
            "Central Campus Building, Floor 2",
            80,
            "Tiered Seating, Dual Projectors, Lapel Microphones, Document Camera",
            "Acoustically treated amphitheater seating for large class lectures.",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO rooms (id, name, room_type, location, capacity, equipment, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        demo_rooms,
    )

    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Demo users (including fixed Admin and demo student accounts)
    demo_users = [
        ("mehtab", "mehtab2026", "System Administrator", "admin@university.edu", "0500000000", "Admin", now_ts),
        ("alice", "alice1234", "Alice Johnson", "alice.j@university.edu", "0511111111", "User", now_ts),
        ("rsmith", "smith1234", "Prof. Robert Smith", "r.smith@university.edu", "0522222222", "User", now_ts),
        ("elena", "elena1234", "Dr. Elena Vance", "e.vance@university.edu", "0533333333", "User", now_ts),
    ]
    cursor.executemany(
        """
        INSERT INTO users (username, password, name, email, phone, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        demo_users,
    )

    # Demo bookings for today and tomorrow so schedule views immediately display data
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    sample_bookings = [
        (
            "LAB-101",
            2,
            "Alice Johnson",
            "alice.j@university.edu",
            today_str,
            "09:00",
            "11:00",
            "Python Programming Lab (CS101)",
            "Confirmed",
            now_ts,
        ),
        (
            "LAB-101",
            3,
            "Prof. Robert Smith",
            "r.smith@university.edu",
            today_str,
            "14:00",
            "16:00",
            "Data Structures Practice Exam",
            "Confirmed",
            now_ts,
        ),
        (
            "LAB-201",
            3,
            "Prof. Robert Smith",
            "r.smith@university.edu",
            today_str,
            "10:00",
            "12:00",
            "Digital Circuits Oscilloscope Workshop",
            "Confirmed",
            now_ts,
        ),
        (
            "CLS-101",
            4,
            "Dr. Elena Vance",
            "e.vance@university.edu",
            today_str,
            "11:00",
            "13:00",
            "Physics I Midterm Review",
            "Confirmed",
            now_ts,
        ),
        (
            "AUD-101",
            1,
            "System Administrator",
            "admin@university.edu",
            tomorrow_str,
            "10:00",
            "12:30",
            "Engineering Orientation Seminar",
            "Confirmed",
            now_ts,
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO bookings (room_id, user_id, user_name, user_email, booking_date, start_time, end_time, purpose, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        sample_bookings,
    )


if __name__ == "__main__":
    init_db(force_reset=True)
    print("Database initialized successfully with 12 demo rooms and initial bookings!")
