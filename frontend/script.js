const API_URL = "http://127.0.0.1:8000";

const loginButton = document.getElementById("login-button");
const loginMessage = document.getElementById("login-message");
const dashboard = document.getElementById("dashboard");
const coachDashboard = document.getElementById("coach-dashboard");

loginButton.addEventListener("click", login);


// =========================
// LOGIN
// =========================

async function login() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    if (!username || !password) {

        loginMessage.textContent =
            "Please enter your username and password.";

        return;
    }

    try {

        const formData = new URLSearchParams();

        formData.append("username", username);
        formData.append("password", password);

        const response = await fetch(
            `${API_URL}/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/x-www-form-urlencoded"
                },

                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {

            loginMessage.textContent =
                data.detail || "Login failed.";

            return;
        }

        localStorage.setItem(
            "token",
            data.access_token
        );

        const userResponse = await fetch(
            `${API_URL}/users/me`,
            {
                headers: {
                    "Authorization": `Bearer ${data.access_token}`
                }
            }
        );

        if (!userResponse.ok) {
            throw new Error("Unable to get user information.");
        }

        const user = await userResponse.json();

        localStorage.setItem("role", user.role);
        console.log("Logged-in user:", user);

        loginMessage.textContent =
             `Login successful! Role: ${user.role}`;

        if (user.role === "coach") {

            dashboard.style.display = "none";
            coachDashboard.style.display = "block";

            await loadCoachDashboard();

        } else {

            coachDashboard.style.display = "none";
            dashboard.style.display = "block";

            await loadDashboard();

        }

    } catch (error) {

        console.error(error);

        loginMessage.textContent =
            "Unable to connect to the server.";
    }
}


// =========================
// LOAD DASHBOARD
// =========================

async function loadDashboard() {

    try {

        const token =
            localStorage.getItem("token");

        if (!token) {
            return;
        }

        const response = await fetch(
            `${API_URL}/workouts/history`,
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load workouts"
            );
        }

        const workouts =
            await response.json();

        displayWorkouts(workouts);

        displayCalendarWorkouts(workouts);

        renderMonthlyCalendar(workouts);

        updateStats(workouts);

        loadWeeklyGoal();

    } catch (error) {

        console.error(error);

        document.getElementById(
            "workout-list"
        ).innerHTML =
            "<p>Unable to load workouts.</p>";
    }
}

// =========================
// LOAD WEEKLY GOAL
// =========================

async function loadWeeklyGoal() {

    try {

        const token = localStorage.getItem("token");

        const response = await fetch(
            `${API_URL}/goals/weekly`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            throw new Error("Unable to load weekly goal");
        }

        const data = await response.json();

        document.getElementById("weekly-goal").value =
            data.weekly_goal;

        document.getElementById("weekly-goal-progress").textContent =
            `${data.completed_days} of ${data.weekly_goal} workout days completed`;

        document.getElementById("weekly-progress-bar").value =
            data.progress_percentage;

        document.getElementById("weekly-goal-message").textContent =
            data.remaining_days === 0
                ? "Weekly goal completed! Great work!"
                : `${data.remaining_days} more workout days to reach your goal.`;

    } catch (error) {

        console.error(error);

        document.getElementById("weekly-goal-progress").textContent =
            "Unable to load weekly progress.";
    }
}

// =========================
// SAVE WEEKLY GOAL
// =========================

async function saveWeeklyGoal() {

    try {

        document.getElementById("weekly-goal-message").textContent =
            "Saving your goal...";

        const token = localStorage.getItem("token");

        const weeklyGoal = Number(
            document.getElementById("weekly-goal").value
        );

        const response = await fetch(
            `${API_URL}/goals/weekly`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    weekly_goal: weeklyGoal
                })
            }
        );

        if (!response.ok) {
            throw new Error("Unable to save weekly goal");
        }

        document.getElementById("weekly-goal-message").textContent =
            "Weekly goal saved successfully!";

        await loadWeeklyGoal();

    } catch (error) {

        console.error(error);

        document.getElementById("weekly-goal-message").textContent =
            "Unable to save weekly goal.";
    }
}

// =========================
// UPDATE STATISTICS
// =========================

function updateStats(workouts) {

    const workoutCount =
        workouts.length;

    const totalSets =
        workouts.reduce(
            (total, workout) =>
                total + workout.sets,
            0
        );

    const totalReps =
        workouts.reduce(
            (total, workout) =>
                total + workout.reps,
            0
        );

    const totalVolume =
        workouts.reduce(
            (total, workout) =>
                total + workout.volume,
            0
        );

    document.getElementById(
        "workout-count"
    ).textContent = workoutCount;

    document.getElementById(
        "total-sets"
    ).textContent = totalSets;

    document.getElementById(
        "total-reps"
    ).textContent = totalReps;

    document.getElementById(
        "total-volume"
    ).textContent =
        `${totalVolume} lbs`;

    updateProgressChart(workouts);
}


// =========================
// DISPLAY WORKOUTS
// =========================

function displayWorkouts(workouts) {

    const workoutList =
        document.getElementById(
            "workout-list"
        );

    if (workouts.length === 0) {

        workoutList.innerHTML =
            "<p>No workouts recorded yet.</p>";

        return;
    }

    workoutList.innerHTML =
        workouts
            .map(workout => `
                <div class="workout-item">

                    <strong>
                        ${workout.exercise}
                    </strong>

                    <p>
                        Date: ${workout.workout_date}
                    </p>

                    <p>
                        ${workout.sets} sets ×
                        ${workout.reps} reps @
                        ${workout.weight} lbs
                    </p>

                    <p>
                        Volume:
                        ${workout.volume} lbs
                    </p>

                    <button
                        onclick="editWorkout(${workout.id})"
                        class="edit-button">
                        Edit
                    </button>

                    <button
                        onclick="deleteWorkout(${workout.id})"
                        class="delete-button">
                        Delete
                    </button>

                </div>
            `)
            .join("");
}

// =========================
// WORKOUT CALENDAR
// =========================

function displayCalendarWorkouts(workouts) {

    const calendarDate =
        document.getElementById("calendar-date").value;

    const calendarWorkouts =
        document.getElementById("calendar-workouts");

    if (!calendarDate) {
        calendarWorkouts.innerHTML =
            "<p>Select a date to view workouts.</p>";
        return;
    }

    const selectedWorkouts =
        workouts.filter(
            workout => workout.workout_date === calendarDate
        );

    if (selectedWorkouts.length === 0) {
        calendarWorkouts.innerHTML =
            "<p>No workouts recorded for this date.</p>";
        return;
    }

    calendarWorkouts.innerHTML =
        selectedWorkouts.map(workout => `
            <div class="workout-item">
                <strong>${workout.exercise}</strong>
                <p>
                    ${workout.sets} sets ×
                    ${workout.reps} reps @
                    ${workout.weight} lbs
                </p>
                <p>Volume: ${workout.volume} lbs</p>
            </div>
        `).join("");
}


// =========================
// MONTHLY CALENDAR
// =========================

let calendarDisplayedMonth = new Date();

function renderMonthlyCalendar(workouts) {

    const calendarGrid =
        document.getElementById("calendar-grid");

    const monthLabel =
        document.getElementById("calendar-month-label");

    const selectedDateInput =
        document.getElementById("calendar-date");

    const year = calendarDisplayedMonth.getFullYear();
    const month = calendarDisplayedMonth.getMonth();

    monthLabel.textContent =
        calendarDisplayedMonth.toLocaleDateString(
            "en-US",
            {
                month: "long",
                year: "numeric"
            }
        );

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const workoutDates = new Set(
        workouts.map(workout => workout.workout_date)
    );

    calendarGrid.innerHTML = "";

    // Empty spaces before the first day
    for (let i = 0; i < firstDay; i++) {
        const blank = document.createElement("div");
        blank.className = "calendar-empty";
        calendarGrid.appendChild(blank);
    }

    // Create each day of the month
    for (let day = 1; day <= daysInMonth; day++) {

        const dateString =
            `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "calendar-day";
        button.textContent = day;

        if (workoutDates.has(dateString)) {
            button.classList.add("has-workout");
            button.title = "Workout recorded";
        }

        if (selectedDateInput.value === dateString) {
            button.classList.add("selected-day");
        }

        button.addEventListener("click", function () {
            selectedDateInput.value = dateString;
            displayCalendarWorkouts(workouts);
            renderMonthlyCalendar(workouts);
        });

        calendarGrid.appendChild(button);
    }
}

// =========================
// DELETE WORKOUT
// =========================

async function deleteWorkout(workoutId) {

    const token =
        localStorage.getItem("token");

    if (!token) {
        return;
    }

    const confirmed =
        confirm(
            "Are you sure you want to delete this workout?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `${API_URL}/workouts/${workoutId}`,
            {
                method: "DELETE",

                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to delete workout."
            );
        }

        await loadDashboard();

    } catch (error) {

        console.error(error);

        alert(error.message);
    }
}


// =========================
// AI RECOMMENDATION
// =========================

const aiButton =
    document.getElementById("ai-button");

const aiResult =
    document.getElementById("ai-result");

aiButton.addEventListener(
    "click",
    getAIRecommendation
);


async function getAIRecommendation() {

    const token =
        localStorage.getItem("token");

    if (!token) {

        aiResult.innerHTML =
            "<p>Please log in first.</p>";

        return;
    }

    aiResult.innerHTML =
        "<p>Analyzing your workouts...</p>";

    try {

        const response = await fetch(
            `${API_URL}/ai/recommendation/mock`,
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to get recommendation."
            );
        }

        aiResult.innerHTML = `
            <p>
                <strong>Analysis:</strong>
                ${data.analysis}
            </p>

            <p>
                <strong>
                    Positive Observation:
                </strong>
                ${data.positive_observation}
            </p>

            <p>
                <strong>
                    Recommendation:
                </strong>
                ${data.recommendation}
            </p>
        `;

    } catch (error) {

        console.error(error);

        aiResult.innerHTML =
            "<p>Unable to get AI recommendation.</p>";
    }
}


// =========================
// ADD WORKOUT
// =========================

const addWorkoutButton =
    document.getElementById(
        "add-workout-button"
    );

const workoutMessage =
    document.getElementById(
        "workout-message"
    );

addWorkoutButton.addEventListener(
    "click",
    addWorkout
);


async function addWorkout() {

    const exercise =
        document.getElementById("exercise").value;

    const sets =
        Number(
            document.getElementById("sets").value
        );

    const reps =
        Number(
            document.getElementById("reps").value
        );

    const weight =
        Number(
            document.getElementById("weight").value
        );

    const dateInput = document.getElementById("coach-workout-date");

    dateInput.onchange = function() {
        alert("New date: " + this.value);
    };

    dateInput.addEventListener("change", () => {
        console.log("Date changed to:", dateInput.value);
    });

    console.log("Date input:", dateInput);
    console.log("Date value:", dateInput.value);

    const workoutDate = dateInput.value;

    alert("Date value: [" + workoutDate + "]");

    if (
        !exercise ||
        !sets ||
        !reps ||
        weight < 0
    ) {

        workoutMessage.textContent =
            "Please enter all workout information.";

        return;
    }

    const token =
        localStorage.getItem("token");

    if (!token) {

        workoutMessage.textContent =
            "Please log in first.";

        return;
    }

    // Check if we are editing an existing workout
    const editingId =
        document.getElementById(
            "add-workout-button"
        ).dataset.editingId;

    try {

        let response;

        if (editingId) {

            // UPDATE existing workout
            response = await fetch(
                `${API_URL}/workouts/${editingId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({
                        exercise: exercise,
                        sets: sets,
                        reps: reps,
                        weight: weight,
                        workout_date: workoutDate || null
                    })
                }
            );

        } else {

            // ADD new workout
            response = await fetch(
                `${API_URL}/workouts`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({
                        exercise: exercise,
                        sets: sets,
                        reps: reps,
                        weight: weight,
                        workout_date: workoutDate || null
                    })
                }
            );
        }

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to save workout."
            );
        }

        if (editingId) {

            workoutMessage.textContent =
                "Workout updated successfully!";

        } else {

            workoutMessage.textContent =
                "Workout added successfully!";
        }

        // Clear the form
        document.getElementById(
            "exercise"
        ).value = "";

        document.getElementById(
            "sets"
        ).value = "";

        document.getElementById(
            "reps"
        ).value = "";

        document.getElementById(
            "weight"
        ).value = "";

        document.getElementById(
        "workout-date"
        ).value = "";

        // Reset button
        const button =
            document.getElementById(
                "add-workout-button"
            );

        button.textContent =
            "Add Workout";

        delete button.dataset.editingId;

        // Refresh dashboard
        await loadDashboard();

    } catch (error) {

        console.error(error);

        workoutMessage.textContent =
            error.message;
    }
}


// =========================
// EDIT WORKOUT
// =========================

window.editWorkout = async function(workoutId) {

    const token =
        localStorage.getItem("token");

    if (!token) {
        alert("Please log in first.");
        return;
    }

    try {

        // Get the workout information
        const response = await fetch(
            `${API_URL}/workouts/history`,
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            throw new Error(
                "Unable to load workout."
            );
        }

        const workouts =
            await response.json();

        const workout =
            workouts.find(
                item => Number(item.id) === Number(workoutId)
            );

        if (!workout) {
            alert("Workout not found.");
            return;
        }

        // Put workout information into the form
        document.getElementById(
            "exercise"
        ).value = workout.exercise;

        document.getElementById(
            "sets"
        ).value = workout.sets;

        document.getElementById(
            "reps"
        ).value = workout.reps;

        document.getElementById(
            "weight"
        ).value = workout.weight;

        document.getElementById(
        "workout-date"
        ).value = workout.workout_date;
        
        document.getElementById(
            "add-workout-button"
        ).dataset.editingId = workoutId;

        document.getElementById(
            "add-workout-button"
        ).textContent = "Update Workout";

        document.getElementById(
            "workout-message"
        ).textContent =
            "Edit the workout information and click Update Workout.";
    } catch (error) {

        console.error(error);

        alert(
            error.message ||
            "Unable to edit workout."
        );
    }
};

// =========================
// PROGRESS CHART
// =========================

let progressChart = null;

function updateProgressChart(workouts) {

    const chart =
        document.getElementById("progress-chart");

    const exerciseSelect =
        document.getElementById("exercise-select");

    exerciseSelect.innerHTML =
        '<option value="">Select an exercise</option>';

    
    const exercises = [
        ...new Set(workouts.map(workout => workout.exercise))
    ];

    exercises.forEach(exercise => {

        const option = document.createElement("option");

        option.value = exercise;
        option.textContent = exercise;

        exerciseSelect.appendChild(option);
    });


    exerciseSelect.onchange = function() {

        const selectedExercise =
            exerciseSelect.value;

        const selectedWorkouts =
            workouts.filter(
                workout =>
                    workout.exercise ===
                    selectedExercise
            );

        const labels =
            selectedWorkouts.map(
                (workout, index) =>
                    `Workout ${index + 1}`
            );

        const volumes =
            selectedWorkouts.map(
                workout => workout.volume
            );

        if (progressChart) {
            progressChart.destroy();
        }

        progressChart = new Chart(chart, {

            type: "line",

            data: {
                labels: labels,

                datasets: [{
                    label:
                        `${selectedExercise} Volume (lbs)`,

                    data: volumes,

                    borderWidth: 2,

                    tension: 0.3
                }]
            },

            options: {
                responsive: true,

                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    };
}

document.getElementById("calendar-date").addEventListener(
    "change",
    function () {
        loadDashboard();
    }
);

// Previous month button
document.getElementById("prev-month").addEventListener(
    "click",
    function () {
        calendarDisplayedMonth.setMonth(
            calendarDisplayedMonth.getMonth() - 1
        );

        loadDashboard();
    }
);

// Next month button
document.getElementById("next-month").addEventListener(
    "click",
    function () {
        calendarDisplayedMonth.setMonth(
            calendarDisplayedMonth.getMonth() + 1
        );

        loadDashboard();
    }
);

document.getElementById("save-weekly-goal")
    .addEventListener("click", saveWeeklyGoal);


// =========================
// COACH DASHBOARD
// =========================

async function loadCoachDashboard() {

    const token = localStorage.getItem("token");

    const response = await fetch(
        `${API_URL}/teams`,
        {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        throw new Error("Unable to load teams.");
    }

    const teams = await response.json();

    const teamsContainer =
        document.getElementById("coach-teams");

    teamsContainer.innerHTML = "";

    if (teams.length === 0) {
        teamsContainer.textContent =
            "You haven't created any teams yet.";
        return;
    }

    teams.forEach(team => {

        const teamCard = document.createElement("div");

        teamCard.innerHTML = `
            <h4>${team.name}</h4>
            <p>Athletes: ${team.athlete_count}</p>
            <p>Members: ${team.athletes.join(", ")}</p>
            <button>View Team</button>
        `;

teamCard.querySelector("button").addEventListener("click", () => {
    viewTeam(team.id);
});

        teamsContainer.appendChild(teamCard);

    });
}


async function viewTeam(teamId) {

    const token = localStorage.getItem("token");

    const response = await fetch(
        `${API_URL}/teams/${teamId}/workouts`,
        {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        throw new Error("Unable to load team workouts.");
    }

    const workouts = await response.json();

    const detailsContainer =
        document.getElementById("team-details");

    detailsContainer.innerHTML = `
        <h3>Team Workouts</h3>

        <h3>Assign New Workout</h3>

        <form id="assign-workout-form">

            <input type="text" id="workout-exercise"
                placeholder="Exercise name" required>

            <input type="number" id="workout-sets"
                placeholder="Sets" min="1" required>

            <input type="number" id="workout-reps"
                placeholder="Reps" min="1" required>

            <input type="number" id="workout-weight"
                placeholder="Target weight (lbs)" min="0" required>

            <input
                type="text"
                id="coach-workout-date"
                placeholder="YYYY-MM-DD"
                required
            >

            <textarea id="workout-notes"
                placeholder="Workout notes (optional)"></textarea>

            <button type="submit">Assign Workout</button>

        </form>
    `;

const dateInput = document.getElementById("coach-workout-date");

const today = new Date();

const localDate = new Date(
    today.getTime() - today.getTimezoneOffset() * 60000
).toISOString().split("T")[0];

if (!dateInput.value) {
    dateInput.value = localDate;
}

dateInput.addEventListener("input", () => {
    console.log("Date picker input:", dateInput.value);
});

console.log("Date after defaulting:", dateInput.value);

    // Handle workout assignment
    const assignForm =
        document.getElementById("assign-workout-form");

    assignForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        const dateElement = document.getElementById("coach-workout-date");

        const workoutDate = dateElement.value;

        alert("Displayed date: " + dateElement.value);

        if (!workoutDate) {
            alert("Please select a workout date.");
            return;
        }

        const workoutData = {
            exercise: document.getElementById("workout-exercise").value,
            sets: Number(document.getElementById("workout-sets").value),
            reps: Number(document.getElementById("workout-reps").value),
            target_weight: Number(document.getElementById("workout-weight").value),
            scheduled_date: workoutDate,
            notes: document.getElementById("workout-notes").value
        };

        const assignResponse = await fetch(
            `${API_URL}/teams/${teamId}/workouts`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(workoutData)
            }
        );

        if (!assignResponse.ok) {
            const errorDetails = await assignResponse.text();

            alert("Error: " + errorDetails);

            console.log("Assignment error:", errorDetails);

            return;
        }

        alert("Workout assigned successfully!");

        await viewTeam(teamId);

    });

    // Display assigned workouts
    if (workouts.length === 0) {
        const message = document.createElement("p");
        message.textContent = "This team has no assigned workouts yet.";
        detailsContainer.appendChild(message);
        return;
    }

    for (const workout of workouts) {

        const workoutCard = document.createElement("div");

        workoutCard.innerHTML = `
            <h4>${workout.exercise}</h4>
            <p>Target: ${workout.sets} sets x ${workout.reps} reps</p>
            <p>Scheduled Date: ${workout.scheduled_date}</p>
            <p>Loading completion status...</p>
        `;

        detailsContainer.appendChild(workoutCard);

        const deleteButton = document.createElement("button");

    deleteButton.textContent = "Delete Assignment";

    deleteButton.style.backgroundColor = "#dc2626";
    deleteButton.style.color = "white";
    deleteButton.style.border = "none";
    deleteButton.style.padding = "8px 12px";
    deleteButton.style.borderRadius = "6px";
    deleteButton.style.cursor = "pointer";

    deleteButton.addEventListener("click", async () => {

        const confirmed = confirm(
            `Are you sure you want to delete ${workout.exercise}?`
        );

        if (!confirmed) {
            return;
        }

        const deleteResponse = await fetch(
            `${API_URL}/team-workouts/${workout.id}`,
            {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`
            }
        }
    );

    if (!deleteResponse.ok) {
        alert("Unable to delete workout.");
        return;
    }

    alert("Workout assignment deleted!");

    await viewTeam(teamId);
});

workoutCard.appendChild(deleteButton);

        const completionResponse = await fetch(
            `${API_URL}/team-workouts/${workout.id}/completions`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!completionResponse.ok) {
            throw new Error("Unable to load completion status.");
        }

        const completionData = await completionResponse.json();

        const status = document.createElement("div");

        status.innerHTML = `
            <p>Completed: ${completionData.completed_count} / ${completionData.athlete_count}</p>
        `;

        completionData.athletes.forEach(athlete => {

            const athleteInfo = document.createElement("p");

            if (athlete.completed) {
                athleteInfo.textContent =
                    `${athlete.athlete}: Completed - ${athlete.completed_sets} sets x ${athlete.completed_reps} reps at ${athlete.actual_weight} lbs`;
            } else {
                athleteInfo.textContent =
                    `${athlete.athlete}: Not completed`;
            }

            status.appendChild(athleteInfo);

        });

        workoutCard.appendChild(status);
    }
}