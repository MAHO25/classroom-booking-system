/**
 * EF101-P07 Classroom/Laboratory Booking System
 * Client-Side Validation: Past Date & Time Rejection + Range Check
 */

document.addEventListener("DOMContentLoaded", () => {
    const bookingForm = document.getElementById("bookingForm");
    const dateInput = document.getElementById("booking_date");
    const startTimeInput = document.getElementById("start_time");
    const endTimeInput = document.getElementById("end_time");
    const timeWarning = document.getElementById("timeWarning");

    // Format current date and time
    const now = new Date();
    const todayStr = now.toISOString().split("T")[0];
    const currentHours = String(now.getHours()).padStart(2, "0");
    const currentMinutes = String(now.getMinutes()).padStart(2, "0");
    const currentTimeStr = `${currentHours}:${currentMinutes}`;

    // 1. Ensure all date inputs have min set to today
    const allDateInputs = document.querySelectorAll('input[type="date"]');
    allDateInputs.forEach(input => {
        input.setAttribute("min", todayStr);
        if (!input.value) {
            input.value = todayStr;
        }
    });

    // 2. Validate Date and Time
    function validateBookingDateTime() {
        if (!dateInput || !startTimeInput || !endTimeInput) return true;

        const selectedDate = dateInput.value;
        const start = startTimeInput.value;
        const end = endTimeInput.value;

        // Reset error states
        dateInput.classList.remove("is-invalid");
        startTimeInput.classList.remove("is-invalid");
        endTimeInput.classList.remove("is-invalid");
        if (timeWarning) {
            timeWarning.classList.add("d-none");
            timeWarning.textContent = "";
        }

        // Rule A: Date cannot be in the past
        if (selectedDate && selectedDate < todayStr) {
            showError(dateInput, `Cannot reserve a past date! (${selectedDate} has already passed).`);
            return false;
        }

        // Rule B: If booking for TODAY, start time cannot be in the past
        if (selectedDate === todayStr && start && start < currentTimeStr) {
            showError(startTimeInput, `Cannot reserve a past time! Current time is ${currentTimeStr}, but you selected ${start}.`);
            return false;
        }

        // Rule C: End time must be strictly after start time
        if (start && end && end <= start) {
            showError(endTimeInput, `Invalid Time Range: End time (${end}) must be strictly AFTER start time (${start})!`);
            return false;
        }

        return true;
    }

    function showError(element, message) {
        element.classList.add("is-invalid");
        if (timeWarning) {
            timeWarning.innerHTML = `<i class="bi bi-exclamation-octagon-fill me-2"></i><strong>Validation Error:</strong> ${message}`;
            timeWarning.classList.remove("d-none");
        }
    }

    // Attach listeners on input change
    if (dateInput) dateInput.addEventListener("change", validateBookingDateTime);
    if (startTimeInput) startTimeInput.addEventListener("change", validateBookingDateTime);
    if (endTimeInput) endTimeInput.addEventListener("change", validateBookingDateTime);

    if (bookingForm) {
        bookingForm.addEventListener("submit", (e) => {
            if (!validateBookingDateTime()) {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    }

    // 3. Simple Tooltip activation for Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
});
