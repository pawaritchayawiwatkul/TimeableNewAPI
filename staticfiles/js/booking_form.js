let currentIndex = 0;
const scrollContainer = document.querySelector('.scroll-container');
const sections = document.querySelectorAll('.section');
const backButton = document.getElementById('backButton');
const nextButton = document.getElementById('nextButton');

async function submitBooking() {
    // Get values from the form elements
    const name = document.getElementById('fullName').value;
    const email = document.getElementById('email').value;
    const type = document.querySelector('button.btn-type.active') ? document.querySelector('button.btn-type.active').textContent.trim() : ''; // Onsite or Online (from active button)
    const date = document.getElementById('selectedDate').value; // Date selected
    const timeslot = document.getElementById('selectedTimeSlot').value; // Timeslot selected
    const duration = document.getElementById('duration').value; // Duration selected
    const note = document.getElementById('note').value || "-"; // Default to "-" if no note

    // Validation: Check if required fields are filled

    if (!timeslot) {
        document.querySelectorAll('.timeslots button').forEach(b => b.classList.add('error'));
        return;
    }

    if (!name || !email || !date || !timeslot || !duration || !type) {
        alert("Please fill out all fields.");
        return;
    }

    // Format the datetime (combine date and timeslot into one ISO string)
    const datetime = `${date}T${timeslot}Z`;  // Assuming timeslot is already in 24-hour format (HH:mm:ss)

    // Set online status based on the selected type (Onsite or Online)
    const online = type.toLowerCase() === "online";  // Convert to boolean

    // Create the booking data object
    const bookingData = {
        notes: note,
        datetime: datetime,
        duration: parseInt(duration, 10), // Ensure duration is an integer
        online: online,
        name: name,
        email: email
    };


    try {
        currentIndex++;
        scrollToSection(currentIndex);
        updateButtons();

        // Sending the data to the server via API
        const response = await fetch(`/student/guest/${uuid}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(bookingData)
        });
        if (response.ok) {
            // Success case
            successBooking()
        } else {
            failedBooking()
        }
    } catch (error) {
        failedBooking()
    }
}

function successBooking() {
    document.getElementById("status").innerHTML = `
    <img id="status-image" src="${successUrl}" alt="status">
    <div id="status-title" class="title">Lesson booked successfully</div>
    <p id="status-subtitle" class="subtitle">
        Your lesson has been successfully booked. You can now join the class at the scheduled time.
    </p>`;
}

function failedBooking() {
    document.getElementById("status").innerHTML = `
    <img id="status-image" src="${failedUrl}" alt="status">
    <div id="status-title" class="title">Lesson booking failed</div>
    <p id="status-subtitle" class="subtitle">
        There was an issue booking your lesson. Please try again or contact support.
    </p>`;
}

function scrollToSection() {
    const targetX = currentIndex * scrollContainer.clientWidth / 3;
    scrollContainer.style.transform = `translateX(-${targetX}px)`;
}

function teleportToSection() {
    const targetX = currentIndex * scrollContainer.clientWidth / 3;
    scrollContainer.style.transition = "none";  // Disable transition for instant movement
    scrollContainer.style.transform = `translateX(-${targetX}px)`;
}

function updateButtons() {
    if (currentIndex === 0) {
        backButton.style.display = 'none';
        nextButton.textContent = 'Next';
    } else if (currentIndex === 1) {
        backButton.style.display = 'inline-block';
        nextButton.textContent = 'Submit';
    } else {
        backButton.style.display = 'none';
        nextButton.style.display = 'none';
    }
}

function moveToNextStep() {
    console.log("next");
    if (currentIndex < 1) {
        let isValid = validateForm();
        if (!isValid) {
            return;
        }
        currentIndex++;
        scrollToSection();
        updateButtons();
    } else {
        submitBooking();
    }
}

function moveToPreviousStep() {
    if (currentIndex > 0) {
        currentIndex--;
        scrollToSection();
        updateButtons();
    }
}


function validateForm() {
    let isValid = true;

    // Clear previous errors
    const errorMessages = document.querySelectorAll(".error-message");
    errorMessages.forEach((msg) => (msg.style.display = "none"));

    const inputs = document.querySelectorAll("input, textarea, button");
    inputs.forEach((input) => input.classList.remove("error"));

    // Validate full name
    const fullName = document.getElementById("fullName");
    if (fullName.value.trim() === "") {
        showError(fullName, "Full name is required.");
        isValid = false;
    }

    // Validate full name
    const nickName = document.getElementById("nickname");
    if (nickName.value.trim() === "") {
        showError(nickName, "Nick name is required.");
        isValid = false;
    }


    // Validate email
    const email = document.getElementById("email");
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email.value)) {
        showError(email, "Please enter a valid email.");
        isValid = false;
    }

    // Validate Button
    const buttons = document.querySelectorAll(".btn-type");
    let typeSelected = false;
    buttons.forEach((button) => {
        if (button.classList.contains("active")) {
            typeSelected = true;
        }
    });
    if (!typeSelected) {
        buttons.forEach((button) => {
            button.classList.add("error");
        })
        const errorMessage = document.getElementById(`typeError`);
        errorMessage.style.display = "block";
        errorMessage.textContent = "Please select a type.";
        isValid = false;
    }
    return isValid
}

function showError(element, message) {
    const errorMessage = document.getElementById(`${element.id}Error`);
    errorMessage.style.display = "block";
    errorMessage.textContent = message;
    element.classList.add("error");
}

// Button type toggle
// const buttons = document.querySelectorAll(".btn-type");
// buttons.forEach((button) => {
//     button.addEventListener("click", function () {
//         buttons.forEach((btn) => btn.classList.remove("active", "error"));
//         this.classList.add("active");
//     });
// });

document.querySelectorAll('.duration-buttons button').forEach(button => {
    button.addEventListener('click', function () {
        const duration = button.value;
        const durationSelect = document.getElementById('duration');
        durationSelect.value = duration;
        updateTimeslots();
    });
});


window.addEventListener('resize', teleportToSection);
nextButton.addEventListener('click', moveToNextStep);
backButton.addEventListener('click', moveToPreviousStep);

updateButtons();
