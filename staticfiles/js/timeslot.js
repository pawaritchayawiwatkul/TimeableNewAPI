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

async function fetchAvailableTime(date) {
    const duration = document.getElementById("duration").value;
    date = formatDate(date, duration);
    let dateKey = `${date}-${duration}`
    if (!date || !duration) return [];
    if (date in availableTime) {
        return availableTime[dateKey];
    }
    try {
        const response = await fetch(`/student/guest/${uuid}/availability?date=${date}&duration=${duration}`);
        const data = await response.json();
        let parsedData = data.availables.map(slot => slot.start);
        availableTime[dateKey] = parsedData
        return parsedData;
    } catch (error) {
        return [];
    }
}

async function updateTimeslots() {
    if (!updatingTime) {
        updatingTime = true;

        const timeslotGrid = document.querySelector('.timeslots-grid');
        const startDayOffset = 1;

        try {
            for (let i = -startDayOffset; i <= startDayOffset; i++) {
                const dayIndex = i + startDayOffset; // Adjust for predefined elements
                const day = new Date(currentDate);
                day.setDate(currentDate.getDate() + i); // Adjust the date by the offset

                // Update timeslot for the specific day
                const timeslotElement = timeslotGrid.querySelector(`.day-timeslots[data-index="${dayIndex}"]`);
                if (timeslotElement) {
                    await updateDayTimeslot(timeslotElement, day);
                }
            }
        } catch (error) {
            console.error('Error while updating timeslots:', error);
        }

        updatingTime = false;
    }
}

async function updateDayTimeslot(dayTimeslotElement, date) {
    const dayIndex = date.getDay();
    const dayName = daysOfWeek[dayIndex]; // Get the day name

    // Update day name and date
    const dayNameElement = dayTimeslotElement.querySelector('.day-name');
    const dayDateElement = dayTimeslotElement.querySelector('.day-date');
    const timeslotsContainer = dayTimeslotElement.querySelector('.timeslots');

    dayNameElement.textContent = dayName;
    dayDateElement.textContent = date.getDate(); // Day of the month
    timeslotsContainer.setAttribute('data-date', formatDate(date));

    // Clear existing timeslot buttons
    timeslotsContainer.innerHTML = '';

    // Add timeslot buttons dynamically
    const timesForDay = await fetchAvailableTime(date);
    timesForDay.forEach(time => {
        const timeButton = document.createElement('button');
        timeButton.textContent = convertTo12HourFormat(time);
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

function moveDate(direction) {
    const daysToOffset = 3 * direction;
    currentDate.setDate(currentDate.getDate() + daysToOffset);

    // Update the dateField value
    const dateField = document.getElementById('dateField');
    dateField.value = currentDate.toISOString().split('T')[0]; // Format as YYYY-MM-DD

    // Update the timeslots
    updateTimeslots();
}

window.onload = () => {
    updateTimeslots();

    document.getElementById('leftArrow').addEventListener('click', () => moveDate(-1)); // Move to previous day
    document.getElementById('rightArrow').addEventListener('click', () => moveDate(1)); // Move to next day
    document.getElementById("dateField").addEventListener("change", function (event) {
        // Get the selected date
        const selectedDate = event.target.value;

        if (selectedDate) {
            currentDate = new Date(selectedDate);
        }
        console.log(selectedDate)
        updateTimeslots();
    })
    const today = new Date().toISOString().split('T')[0];

    // Set the default value of the date input to today's date
    document.getElementById('dateField').value = today;
};

// window.addEventListener('resize', updateTimeslots);
document.getElementById('duration').addEventListener('change', updateTimeslots);