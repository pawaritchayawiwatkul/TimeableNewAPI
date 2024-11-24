let currentDate = new Date(); // Keep track of the current date
let currentDayIndex = currentDate.getDay(); // Current day index (0-6)
const uuid = document.getElementById("uid").value;
const daysOfWeek = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const availableTime = {};
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
    date = formatDate(date);
    if (!date || !duration) return [];
    if (date in availableTime) {
        return availableTime[date];
    }
    try {
        const response = await fetch(`/student/guest/${uuid}/availability?date=${date}&duration=${duration}`);
        const data = await response.json();
        let parsedData = data.availables.map(slot => slot.start);
        availableTime[date] = parsedData
        return parsedData;
    } catch (error) {
        return [];
    }
}

async function createTimeSlot(date) {
    const dayIndex = date.getDay(); // Get the index of the day (0-6)
    const dayName = daysOfWeek[dayIndex]; // Get the day name

    // Create the elements for the timeslot
    const dayTimeslot = document.createElement('div');
    dayTimeslot.classList.add('day-timeslots');

    const dayslot = document.createElement('div');
    dayslot.classList.add('dayslot');

    // Day name
    const dayNameElement = document.createElement('h1');
    dayNameElement.textContent = dayName;

    // Date (day of the month)
    const dayDate = document.createElement('h2');
    dayDate.textContent = date.getDate(); // Get the day of the month

    // Append the day name and date to the day slot
    dayslot.appendChild(dayNameElement);
    dayslot.appendChild(dayDate);

    // Create the timeslots section
    const timeslots = document.createElement('div');
    timeslots.classList.add('timeslots');
    timeslots.setAttribute('data-date', formatDate(date)); // You can dynamically assign this value

    // Add timeslot buttons based on the selected day
    const timesForDay = await fetchAvailableTime(date)
    timesForDay.forEach(time => {
        const timeButton = document.createElement('button');
        timeButton.textContent = convertTo12HourFormat(time);
        timeButton.value = time;
        timeslots.appendChild(timeButton);
    });

    // Append the dayslot and timeslots to the dayTimeslot element
    dayTimeslot.appendChild(dayslot);
    dayTimeslot.appendChild(timeslots);
    return dayTimeslot;
}

// Function to update the timeslot grid
async function updateTimeslots() {
    document.querySelectorAll('.timeslots button').forEach(b => b.classList.remove('selected'));
    document.getElementById('selectedTimeSlot').value = "";
    document.getElementById('selectedDate').value = "";

    const timeslotGrid = document.querySelector('.timeslots-grid');
    timeslotGrid.innerHTML = ''; // Clear existing content


    // Check if it's mobile (screen width <= 768px)
    const isMobile = window.innerWidth <= 768;

    // Generate the days based on the numDays
    const startDayOffset = isMobile ? 1 : 2;// Calculate how many days before and after
    for (let i = -startDayOffset; i < startDayOffset + 1; i++) {
        const day = new Date(currentDate);
        day.setDate(currentDate.getDate() + i); // Adjust the day by the offset
        let dayTimeslot = await createTimeSlot(day)
        timeslotGrid.appendChild(dayTimeslot);
    }

    document.querySelectorAll('.timeslots button').forEach(button => {
        button.addEventListener('click', function () {
            document.querySelectorAll('.timeslots button').forEach(b => b.classList.remove('selected'));
            button.classList.add('selected');
            document.getElementById('selectedTimeSlot').value = button.value;
            document.getElementById('selectedDate').value = button.parentNode.getAttribute('data-date');
        });
    });
}

function moveDate(direction) {
    const isMobile = window.innerWidth <= 768;
    const daysToOffset = (isMobile ? 3 : 5) * direction;
    currentDate.setDate(currentDate.getDate() + daysToOffset);
    updateTimeslots();
}

window.onload = () => {
    updateTimeslots();

    document.getElementById('leftArrow').addEventListener('click', () => moveDate(-1)); // Move to previous day
    document.getElementById('rightArrow').addEventListener('click', () => moveDate(1)); // Move to next day
};


window.addEventListener('resize', updateTimeslots);
document.getElementById('duration').addEventListener('change', updateTimeslots);