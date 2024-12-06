let currentDate = new Date(); // Keep track of the current date
let currentDayIndex = currentDate.getDay(); // Current day index (0-6)
const uuid = document.getElementById("uid").value;
const daysOfWeek = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const availableTime = {};
let updatingTime = false;

// Function to format date as mm/dd/yyyy
function formatDate(date) {
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Add leading zero if needed
    const day = date.getDate().toString().padStart(2, '0'); // Add leading zero if needed
    const year = date.getFullYear();
    return `${year}-${month}-${day}`;
}

function convertTo12HourFormat(time) {
    const [hours, minutes] = time.split(':');  // Split the time into hours and minutes
    let hour = parseInt(hours);
    const period = hour >= 12 ? 'PM' : 'AM';   // Determine AM or PM

    hour = hour % 12 || 12;  // Convert 0-23 hours to 1-12

    return `${hour}:${minutes} ${period}`;
}

// Updated fetchAvailableTime to handle date ranges
async function fetchAvailableTime(startDate, endDate, duration) {
    const start = formatDate(startDate);
    const end = formatDate(endDate);
    const dateKey = `${start}-${end}-${duration}`;

    if (!start || !end || !duration) return {};

    // Check if data is already cached
    if (dateKey in availableTime) {
        return availableTime[dateKey];
    }

    try {
        // Fetch available times from the API
        const response = await fetch(`/student/guest/${uuid}/availability?start_date=${start}&end_date=${end}&duration=${duration}`);
        const data = await response.json();
        availableTime[dateKey] = data.available_times; // Cache the results
        return data.available_times;
    } catch (error) {
        console.error("Error fetching available times:", error);
        return {};
    }
}

// Updated updateTimeslots to handle multiple days
async function updateTimeslots() {
    if (!updatingTime) {
        updatingTime = true;

        const timeslotGrid = document.querySelector('.timeslots-grid');
        const startDayOffset = 2; // Number of days to show after current day (current + 2 days)
        const endDate = new Date(currentDate);
        endDate.setDate(currentDate.getDate() + startDayOffset);

        try {
            // Fetch available times for the range
            const duration = document.getElementById("duration").value;
            const availableTimes = await fetchAvailableTime(currentDate, endDate, duration);

            // Iterate through the days and update each day's timeslots
            const allDays = [];
            for (let i = 0; i <= startDayOffset; i++) {
                const dayIndex = i; // Adjust index to start from 0
                const day = new Date(currentDate);
                day.setDate(currentDate.getDate() + i);

                const timeslotElement = timeslotGrid.querySelector(`.day-timeslots[data-index="${dayIndex}"]`);
                if (timeslotElement) {
                    updateDayHeader(timeslotElement, day); // Update header synchronously
                    allDays.push({ element: timeslotElement, date: day, timeslots: availableTimes[formatDate(day)] || [] });
                }
            }

            // Update timeslot content for all days
            allDays.forEach(({ element, date, timeslots }) => {
                updateDayTimeslotContent(element, timeslots, date);
            });
        } catch (error) {
            console.error('Error while updating timeslots:', error);
        }

        updatingTime = false;
    }
}

// Updated updateDayTimeslotContent to use pre-fetched timeslots
function updateDayTimeslotContent(dayTimeslotElement, timesForDay, date) {
    const timeslotsContainer = dayTimeslotElement.querySelector('.timeslots');
    timeslotsContainer.setAttribute('data-date', formatDate(date));

    // Clear existing timeslot buttons
    timeslotsContainer.innerHTML = '';

    // Add timeslot buttons dynamically
    timesForDay.forEach(time => {
        const timeButton = document.createElement('button');
        timeButton.textContent = convertTo12HourFormat(time['start']);
        timeButton.value = time;

        // Add click listener for the button
        timeButton.addEventListener('click', () => {
            document.querySelectorAll('.timeslots button').forEach(b => b.classList.remove('selected'));
            timeButton.classList.add('selected');
            document.getElementById('selectedTimeSlot').value = timeButton.value;
            document.getElementById('selectedDate').value = timeslotsContainer.getAttribute('data-date');
        });

        timeslotsContainer.appendChild(timeButton);
    });
}


function updateDayHeader(dayTimeslotElement, date) {
    const dayIndex = date.getDay();
    const dayName = daysOfWeek[dayIndex]; // Get the day name

    // Update day name and date
    const dayNameElement = dayTimeslotElement.querySelector('.day-name');
    const dayDateElement = dayTimeslotElement.querySelector('.day-date');

    dayNameElement.textContent = dayName;
    dayDateElement.textContent = date.getDate(); // Day of the month
}

function moveDate(direction) {
    const daysToOffset = 3 * direction;

    // Calculate tomorrow's date
    const tomorrow = new Date();
    tomorrow.setHours(0, 0, 0, 0); // Reset time to midnight for accurate comparison

    // Calculate the new date with the offset
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + daysToOffset);

    // Ensure newDate is not earlier than tomorrow
    if (newDate < tomorrow) {
        currentDate = tomorrow; // Reset to tomorrow's date if below minimum
    } else {
        currentDate = newDate; // Update currentDate to the calculated newDate
    }

    // Update the dateField value
    const dateField = document.getElementById('dateField');
    dateField.value = currentDate.toISOString().split('T')[0]; // Format as YYYY-MM-DD

    // Update the timeslots
    updateTimeslots();
}


function setMinDate() {
    const dateInput = document.getElementById('dateField');
    const today = new Date();

    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);
    currentDate = tomorrow
    // Format date as YYYY-MM-DD
    const minDate = tomorrow.toISOString().split('T')[0];

    // Set the min attribute of the date input
    dateInput.setAttribute('min', minDate);
    document.getElementById('dateField').value = minDate;

}


window.onload = () => {
    setMinDate();
    updateTimeslots();

    document.getElementById('leftArrow').addEventListener('click', () => moveDate(-1)); // Move to previous day
    document.getElementById('rightArrow').addEventListener('click', () => moveDate(1)); // Move to next day
    document.getElementById("dateField").addEventListener("change", function (event) {
        const selectedDate = event.target.value;

        if (selectedDate) {
            currentDate = new Date(selectedDate);
        }
        updateTimeslots();
    });
};

document.getElementById('duration').addEventListener('change', updateTimeslots);