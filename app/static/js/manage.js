function activateTeams() {
    const teamSelect = document.getElementById('teamSelect');
    const confirmButton = document.getElementById('confirmbutton');
    const monthSelect = document.getElementById('month');

    // Überprüfen, ob das Team-Auswahlfeld leer ist oder nicht ausgewählt wurde
    if (teamSelect.value === "" || teamSelect.selectedIndex === 0) {
        confirmButton.disabled = true;
    } else {
        // Überprüfen, ob das Monatsfeld nicht ausgewählt ist
        if (!monthSelect.value) {
            confirmButton.disabled = true;
        } else {
            confirmButton.disabled = false;
        }
    }
}


// Funktion zum Senden der ID an Python mit Datum
function sendSelectedIdToPython() {
    const teamSelect = document.getElementById('teamSelect');
    const selectedOption = teamSelect.options[teamSelect.selectedIndex];
    const selectedId = selectedOption.getAttribute('id');

    const inputMonth = document.getElementById('month');

    // Das Monatsdatum aus dem inputMonth-Element extrahieren und in das gewünschte Format konvertieren
    const selectedDate = new Date(inputMonth.value + "-01T00:00:00+02:00");

    const start_tmstmp = selectedDate.toISOString().slice(0, 19) + "+02:00"; // Startzeitstempel im gewünschten Format mit +02:00
    const nextMonthDate = new Date(selectedDate);
    nextMonthDate.setMonth(nextMonthDate.getMonth() + 1);

    const end_tmstmp = nextMonthDate.toISOString().slice(0, 19) + "+02:00"; // Endzeitstempel im gewünschten Format mit +02:00

    console.log(start_tmstmp)
    console.log(end_tmstmp)

    fetch('/manage-times.html', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ selectedId: selectedId, start_tmstmp: start_tmstmp, end_tmstmp: end_tmstmp })
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
