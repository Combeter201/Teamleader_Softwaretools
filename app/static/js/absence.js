function getISOWeek(date) {
	var januaryFourth = new Date(date.getFullYear(), 0, 4);
	return Math.ceil((((date - januaryFourth) / 86400000) + januaryFourth.getDay() + 1) / 7);
}

function changeView() {
	var today = new Date();
	var currentYear = today.getFullYear();
	var currentMonth = (today.getMonth() + 1).toString().padStart(2, '0');
	var currentDay = today.getDate().toString().padStart(2, '0');
	const viewSelect = document.getElementById("viewSelect");
	var selectedOption = viewSelect.options[viewSelect.selectedIndex].value;
	var dateInput = document.getElementById("date");

	switch (selectedOption) {
		case "day":
			dateInput.type = "date";
			dateInput.value = `${currentYear}-${currentMonth}-${currentDay}`;
			break;
		case "week":
			dateInput.type = "week";
			dateInput.value = `${currentYear}-W${String(getISOWeek(today)).padStart(2, '0')}`;
			break;
		case "month":
			dateInput.type = "month";
			dateInput.value = `${currentYear}-${currentMonth}`;
			break;
		default:
			dateInput.type = "date"; // Default to 'date' if no match (optional)
			dateInput.value = `${currentYear}-${currentMonth}-${currentDay}`;
			break;
	}
}

function showCurrentDay(selectedDay) {
	const selDate = new Date(selectedDay);
	const dayNames = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
	const currentDayName = dayNames[selDate.getDay()]; // getDay() liefert den Wochentag als Zahl von 0-6

	const days = document.querySelectorAll('.day');
	days.forEach(day => {
		if (day.id !== currentDayName) {
			day.style.display = "none";
		} else {
			day.style.display = "block";
		}
	});
}

function showCurrentWeek() {
	const days = document.querySelectorAll('.day');
	days.forEach(day => {
		day.style.display = "block";
	});
}

function checkAbsenceforDate() {
	const loader = document.getElementById('loader');
	loader.className = "loading";
	const table = document.getElementById('calendar');
	table.className = 'hidden';
	const confirmButton = document.getElementById('confirmbutton');
	confirmButton.disabled = true;
	const date = document.getElementById('date');
	const dateValue = date.value;
	const dateInput = document.getElementById("date");
	var inputType = dateInput.type;

	fetch('/absence.html', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				date: dateValue,
				inputType: inputType
			})
		})
		.then(response => {
			if (!response.ok) {
				throw new Error('Network response was not ok');
			}
			return response.text();
		})
		.then(data => {
			document.body.innerHTML = data; // Dies ersetzt den aktuellen Inhalt durch den Antwortinhalt
		})
		.catch(error => {
			console.error('Error:', error);
		});
}

function setDateForward() {
    const dateInput = document.getElementById('date');
    const selectedOption = viewSelect.options[viewSelect.selectedIndex].value;
    let currentDate = new Date(dateInput.value);

    if (/^\d{4}-W\d{2}$/.test(dateInput.value)) {
        // ISO week format handling
        const [year, week] = dateInput.value.split('-W').map(Number);
        currentDate = new Date(year, 0, (week - 1) * 7 + 1);
        if (currentDate.getDay() <= 4) {
            currentDate.setDate(currentDate.getDate() - currentDate.getDay() + 1);
        } else {
            currentDate.setDate(currentDate.getDate() + 8 - currentDate.getDay());
        }

        if (selectedOption === "week") {
            currentDate.setDate(currentDate.getDate() + 7);
        } else {
            currentDate.setDate(currentDate.getDate() + 1);
        }

        const target = new Date(currentDate);
        const dayNr = (currentDate.getDay() + 6) % 7;
        target.setDate(target.getDate() - dayNr + 3);
        const firstThursday = target.valueOf();
        target.setMonth(0, 1);
        if (target.getDay() !== 4) {
            target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
        }
        const weekNum = 1 + Math.ceil((firstThursday - target) / 604800000);
        dateInput.value = `${currentDate.getFullYear()}-W${('0' + weekNum).slice(-2)}`;
    } else {
        // Date format YYYY-MM-DD handling
        if (selectedOption === "week") {
            currentDate.setDate(currentDate.getDate() + 7);
        } else {
            currentDate.setDate(currentDate.getDate() + 1);
        }
        dateInput.value = currentDate.toISOString().split('T')[0];
    }
    checkAbsenceforDate();
}

function setDateBackward() {
    const dateInput = document.getElementById('date');
    const selectedOption = viewSelect.options[viewSelect.selectedIndex].value;
    let currentDate = new Date(dateInput.value);

    if (/^\d{4}-W\d{2}$/.test(dateInput.value)) {
        // ISO week format handling
        const [year, week] = dateInput.value.split('-W').map(Number);
        currentDate = new Date(year, 0, (week - 1) * 7 + 1);
        if (currentDate.getDay() <= 4) {
            currentDate.setDate(currentDate.getDate() - currentDate.getDay() + 1);
        } else {
            currentDate.setDate(currentDate.getDate() + 8 - currentDate.getDay());
        }

        if (selectedOption === "week") {
            currentDate.setDate(currentDate.getDate() - 7);
        } else {
            currentDate.setDate(currentDate.getDate() - 1);
        }

        const target = new Date(currentDate);
        const dayNr = (currentDate.getDay() + 6) % 7;
        target.setDate(target.getDate() - dayNr + 3);
        const firstThursday = target.valueOf();
        target.setMonth(0, 1);
        if (target.getDay() !== 4) {
            target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
        }
        const weekNum = 1 + Math.ceil((firstThursday - target) / 604800000);
        dateInput.value = `${currentDate.getFullYear()}-W${('0' + weekNum).slice(-2)}`;
    } else {
        // Date format YYYY-MM-DD handling
        if (selectedOption === "week") {
            currentDate.setDate(currentDate.getDate() - 7);
        } else {
            currentDate.setDate(currentDate.getDate() - 1);
        }
        dateInput.value = currentDate.toISOString().split('T')[0];
    }
    checkAbsenceforDate();
}