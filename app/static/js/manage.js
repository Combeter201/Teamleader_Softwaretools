function downloadCSV() {
    window.location.href = '/download-csv';
}

function sendSelectedIdToPython() {
    const loader = document.getElementById('loader');
	loader.className = "loading";
	const confirmButton = document.getElementById('confirmbutton');
	confirmButton.disabled = true;

    try {
    const membersTable = document.getElementById('membersTable');
    if (membersTable) {
        membersTable.className = 'hidden';
    }
    } catch (error) {}

    // Alle Buttons mit der Klasse "download-button" finden
    const downloadButtons = document.querySelectorAll('button.download-button');

    // Über alle gefundenen Buttons iterieren und sie deaktivieren
    downloadButtons.forEach(button => {
        button.disabled = true;
    });

    const teamSelect = document.getElementById('teamSelect');
    const selectedOption = teamSelect.options[teamSelect.selectedIndex];
    const team_name = selectedOption.innerHTML;
    const selectedId = selectedOption.getAttribute('id');

    const inputMonth = document.getElementById('month');
    const monthValue = inputMonth.value;

    // Das Monatsdatum aus dem inputMonth-Element extrahieren und in das gewünschte Format konvertieren
    const firstBlockDate = new Date(monthValue + "-01T00:00:00+02:00");

    // Funktion, um Tage zu einem Datum hinzuzufügen
    function addDays(date, days) {
        const result = new Date(date);
        result.setDate(result.getDate() + days);
        return result;
    }

    // secondBlockDate ist 10 Tage nach dem initialDate
    const secondBlockDate = addDays(firstBlockDate, 10);

    // thirdBlockDate ist 20 Tage nach dem initialDate
    const thirdBlockDate = addDays(firstBlockDate, 20);

    const first_tmstmp = firstBlockDate.toISOString().slice(0, 19) + "+02:00"; // Startzeitstempel im gewünschten Format mit +02:00
    const second_tmstmp = secondBlockDate.toISOString().slice(0, 19) + "+02:00"; // Startzeitstempel im gewünschten Format mit +02:00
    const third_tmstmp = thirdBlockDate.toISOString().slice(0, 19) + "+02:00"; // Startzeitstempel im gewünschten Format mit +02:00

    // Überprüfen, ob der Monat 31 Tage hat
    const nextMonthDate = new Date(firstBlockDate);
    nextMonthDate.setMonth(nextMonthDate.getMonth() + 1);

    const end_tmstmp = nextMonthDate.toISOString().slice(0, 19) + "+02:00"; // Endzeitstempel im gewünschten Format mit +02:00

    let fourth_tmstmp = null;

    // Überprüfen, ob der ausgewählte Monat 31 Tage hat (Jan, März, Mai, Jul, Aug, Okt, Dez)
    if ([0, 2, 4, 6, 7, 9, 11].includes(firstBlockDate.getMonth())) {
        fourth_tmstmp = new Date(monthValue + "-31T00:00:00+02:00").toISOString().slice(0, 19) + "+02:00";
    }

    fetch('/manage-times.html', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            selectedId: selectedId,
            selectedOption: selectedOption.value,
            team_name: team_name,
            selectedMonth: monthValue,
            first_tmstmp: first_tmstmp,
            second_tmstmp: second_tmstmp,
            third_tmstmp: third_tmstmp,
            end_tmstmp: end_tmstmp,
            fourth_tmstmp: fourth_tmstmp  // Nur hinzufügen, wenn fourth_tmstmp definiert ist
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.text();
    })
    .then(data => {
        document.body.innerHTML = data;  // Dies ersetzt den aktuellen Inhalt durch den Antwortinhalt
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function setDateForward() {
    const dateInput = document.getElementById('month');
    const teamSelect = document.getElementById('teamSelect');
    const selectedOption = teamSelect.options[teamSelect.selectedIndex];
    const team_name = selectedOption.innerHTML;
    const inputValue = dateInput.value;

    // Check if the input is in the "YYYY-MM" format
    if (/^\d{4}-\d{2}$/.test(inputValue)) {
        const [year, month] = inputValue.split('-').map(Number);
        let currentDate = new Date(year, month - 1, 1);

        // Add one month
        currentDate.setMonth(currentDate.getMonth() + 1);

        const newYear = currentDate.getFullYear();
        const newMonth = ('0' + (currentDate.getMonth() + 1)).slice(-2);
        dateInput.value = `${newYear}-${newMonth}`;
    } else {
        console.error('Invalid date format. Expected YYYY-MM.');
    }
    if(team_name != "Team auswählen"){
        sendSelectedIdToPython();
    }
}


function setDateBackward() {
    const dateInput = document.getElementById('month');
    const teamSelect = document.getElementById('teamSelect');
    const selectedOption = teamSelect.options[teamSelect.selectedIndex];
    const team_name = selectedOption.innerHTML;
    const inputValue = dateInput.value;

    // Check if the input is in the "YYYY-MM" format
    if (/^\d{4}-\d{2}$/.test(inputValue)) {
        const [year, month] = inputValue.split('-').map(Number);
        let currentDate = new Date(year, month - 1, 1);

        // Subtract one month
        currentDate.setMonth(currentDate.getMonth() - 1);

        const newYear = currentDate.getFullYear();
        const newMonth = ('0' + (currentDate.getMonth() + 1)).slice(-2);
        dateInput.value = `${newYear}-${newMonth}`;
    } else {
        console.error('Invalid date format. Expected YYYY-MM.');
    }
    if(team_name != "Team auswählen"){
        sendSelectedIdToPython();
    }
}

function toggleConfirmButton() {
            const teamSelect = document.getElementById('teamSelect');
            const date = document.getElementById('month');

            const confirmButton = document.getElementById('confirmbutton');
            // Check if an option other than the placeholder is selected
            if (teamSelect.value && date.value) {
                confirmButton.disabled = false;
            } else {
                confirmButton.disabled = true;
            }
        }