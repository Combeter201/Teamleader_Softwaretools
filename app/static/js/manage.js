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


function sendSelectedIdToPython() {
    const teamSelect = document.getElementById('teamSelect');
    const selectedOption = teamSelect.options[teamSelect.selectedIndex];
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

document.addEventListener('DOMContentLoaded', function() {
    var progressBar = document.getElementById('progress');
    progressBar.style.display = 'flex'; // Verstecke die Fortschrittsleiste nach Abschluss der Animation
    progressBar.style.transition = 'width 10s linear';
    progressBar.style.width = '100%'; // Starte mit 100% Breite

    setTimeout(function() {
        var loadingBar = document.getElementById('loadingBar');
        loadingBar.style.display = 'none'; // Verstecke die Fortschrittsleiste nach Abschluss der Animation
    }, 10250); // 5000ms (5 Sekunden) für die Animation
});
