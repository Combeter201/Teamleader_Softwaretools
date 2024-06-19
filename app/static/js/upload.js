function downloadTemplate() {
    window.location.href = '/download-template';
}

function submitForm() {
    document.getElementById('uploadForm').submit();
}

function redirectToTeamleader() {
        window.location.href = '/authorize-teamleader'; // Hier leitest du zur Autorisierungsseite weiter
}

function uploadtoTeamleader() {
        window.location.href = '/upload-to-teamleader'; // Hier leitest du zur Autorisierungsseite weiter
}

function clearData() {
    fetch('/clear-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Leert das csvContent-Div, um die Tabelle auszublenden
            var csvContentDiv = document.getElementById('csvContent');
            csvContentDiv.innerHTML = '';

            // Setzt das Datei-Upload-Input zurück
            var fileInput = document.getElementById('csvFile');
            fileInput.value = '';

            // Buttons deaktivieren
            var clearButton = document.querySelector('.clear-button');
            var uploadButton = document.getElementById('uploadButton');
            clearButton.disabled = true;
            uploadButton.disabled = true;

            // Reset des Formulars
            document.getElementById('uploadForm').reset();
        } else {
            console.error('Fehler beim Löschen der Daten:', data.message);
        }
    })
    .catch(error => console.error('Fehler:', error));
}

function openModal() {
    var modal = document.getElementById('myModal');
    modal.style.display = 'flex';
}

function closeModal() {
    var modal = document.getElementById('myModal');
    modal.style.display = 'none';
}

function uploadTimes() {
    clearData();
    closeModal();
    var csvContentDiv = document.getElementById('csvContent');
    csvContentDiv.innerHTML = '<p class="success-message">Die Zeiten wurden erfolgreich hochgeladen!</p>';
}

function checkTableVisibility() {
    var csvContentDiv = document.getElementById('csvContent');
    var tableExists = csvContentDiv.querySelector('table') !== null;
    var clearButton = document.querySelector('.clear-button');
    var uploadButton = document.getElementById('uploadButton');

    if (tableExists) {
        clearButton.disabled = false;
        uploadButton.disabled = false;
    } else {
        clearButton.disabled = true;
        uploadButton.disabled = true;
    }
}
