# EF101-P07: Student Presentation & Viva Guide
**Classroom / Laboratory Booking Information System**
*(Prepared specifically for first-year university students)*

---

## 🎯 1. How to Run the Project (Using Conda)

Activate your conda environment and run the project:

```bash
# 1. Activate your conda environment
conda activate booking_env

# 2. Run the Web Application (Opens automatically in your browser!):
python main.py

# 3. Or run the automated 6-step test verification in front of your professor:
python test_system.py
```

---

## 📚 2. Answering the "Required Understanding" Questions

The project assignment lists specific conceptual points that first-year students must understand. Here are the exact explanations in simple, clear language:

### A. Database Relationships between Room, User, and Booking
- **Tables in our SQLite Database:**
  1. `rooms` table: Stores physical properties (ID, name, capacity, equipment, location).
  2. `users` table: Stores people who make reservations (name, email, role).
  3. `bookings` table: Represents the actual reservations.
- **The Relationships:**
  - **One-to-Many (Room ➔ Bookings):** One single room (e.g. `LAB-101`) can have many bookings across different days and times.
  - **One-to-Many (User ➔ Bookings):** One single user (e.g. Alice) can reserve many different rooms.
  - **Foreign Key (`FOREIGN KEY (room_id) REFERENCES rooms(id)`):** The `bookings` table links to `rooms` via `room_id`. This prevents booking a room that doesn't exist.

```
+---------------+           1:N           +---------------+
|     ROOMS     | ----------------------> |   BOOKINGS    |
| (id, name...) |                         | (id, room_id, |
+---------------+                         |  user_name,   |
                                          |  date, time)  |
+---------------+           1:N           +---------------+
|     USERS     | ---------------------->
| (id, email..) |
+---------------+
```

---

### B. Primary and Unique IDs
- **What is a Primary Key?**
  A unique identifier that guarantees every single row in a database table can be uniquely found and referenced without ambiguity.
- **In our project:**
  - `rooms.id`: A unique string ID (e.g., `LAB-101`, `CLS-201`, `AUD-101`). No two rooms can have the same ID.
  - `bookings.id`: An auto-incrementing integer (`1, 2, 3...`) uniquely identifying each reservation.
  - `users.id`: Unique integer primary key.
  - `users.username`, `users.email`, `users.phone`: Defined as `UNIQUE` columns in SQLite, ensuring no duplicates.

---

### C. Role-Based Access: User vs Admin Panels
- **1. Administrator Panel:**
  - **Fixed Credentials:** Username = `mehtab`, Password = `mehtab2026`.
  - Capabilities:
    - Manage Rooms: Add new room, Edit room specs, Delete room.
    - Inspect All Users: Table of all registered users with "View Details" to see their profile and bookings.
    - Inspect & Cancel Any Booking across the university.
- **2. Student / User Panel:**
  - Sign Up with unique username, email, phone, and password (>= 8 chars).
  - Sign In with username or email + password.
  - Can view all rooms, check availability, and make reservations.
  - In "My Bookings", users see **ONLY** their own reservations and can only cancel their own bookings.

---

### C. Why Conflict Checking Must Occur BEFORE Saving
- **The Problem with Manual Systems:**
  In a paper logbook or naive system, if two people write down "LAB-101 at 10:00 AM", both think they have the room. A scheduling conflict occurs.
- **Why Check Before Saving in Code?**
  Once data is written to disk (`INSERT`), the reservation is considered confirmed. Therefore, the system must execute a **Validation Query** first:
  1. Look up any existing confirmed bookings for that exact room and date.
  2. Check if the requested start and end times overlap with any existing booking.
  3. **Only if 0 conflicts are found** does the system proceed to execute `INSERT INTO bookings`.
  4. If a conflict is found, the system immediately rejects the request and warns the user.

---

### D. The Mathematical Overlap Formula (Easy to Draw on Whiteboard!)

When does Time Interval A `[start_A, end_A]` overlap with Time Interval B `[start_B, end_B]`?

```
Interval A:         [------- A -------]
Interval B:              [------- B -------]   <-- OVERLAP!

Formula:
Overlap = (start_A < end_B) AND (end_A > start_B)
```

In our Python code (`check_time_conflict`):
```python
cursor.execute('''
    SELECT * FROM bookings
    WHERE room_id = ?
      AND booking_date = ?
      AND status != 'Cancelled'
      AND (start_time < ? AND end_time > ?)
''', (room_id, date, new_end_time, new_start_time))
```

---

### E. Frontend vs Backend
- **Frontend (Web Browser):**
  - Rendered in your web browser using HTML, Bootstrap 5, and JavaScript.
  - What the user sees: responsive search cards, date pickers, filter dropdowns, and schedule timetables.
  - Handles client-side validation (stops submission immediately if end time <= start time).
- **Backend (Python Server):**
  - Runs in `app.py` using Flask and SQLite (`database.py`).
  - Receives web requests (GET / POST), runs the overlap conflict formula, and writes to `booking_system.db`.

---

### F. Introductory Transaction Concept
- A database **Transaction** is a sequence of one or more database operations treated as a single, atomic unit of work.
- **Commit (`conn.commit()`):** Saves changes permanently to disk.
- **Rollback (`conn.rollback()`):** If an error happens midway, all uncommitted changes are undone, preventing corrupted or half-saved records.
- This guarantees data integrity.

---

### G. How the System Changes a Manual Process into an Information System

| Manual Process (Paper/Whiteboard) | Automated Information System (Our Python Project) |
| :--- | :--- |
| Paper logs can be lost, stained, or misread | Persistent SQLite database saved on disk |
| Double-bookings happen easily when 2 people write simultaneously | Instant mathematical conflict check prevents overlaps 100% |
| Must walk to the room or flip pages to find an open lab | Instant search/filter by equipment (e.g., "Find room with Oscilloscope") |
| Checking weekly schedule requires manual calculation | Visual daily & weekly timetable automatically rendered |
| Cancellations require erasing and cause confusion | Single-click cancellation immediately frees slot for others |

---

## 🧪 3. Demonstrating the 6 Tests to Your Professor

Run this single command:
```bash
python test_system.py
```

It will execute and display:
1. **Test 1: Create a booking:** Successfully reserves `LAB-101` for 13:00 - 15:00.
2. **Test 2: Attempt overlapping booking:** Tries booking `LAB-101` for 14:00 - 16:00. **REJECTED!** (Overlap detected).
3. **Test 3: Cancel a booking:** Cancels booking #1. Confirms the 13:00-15:00 slot is immediately free again.
4. **Test 4: Book another room at the same time:** Books `LAB-102` at 13:00 - 15:00. **SUCCEEDS!** (Rooms are independent).
5. **Test 5: Search by equipment:** Filters rooms by "Oscilloscope" and finds `LAB-201`.
6. **Test 6: Weekly schedule:** Queries and displays the full week's timetable.
