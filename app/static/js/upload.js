// JavaScript für die Funktionalität der Seite

function submitForm() {
    document.getElementById('uploadForm').submit();
}

function clearData() {
    // Leert das csvContent-Div, um die Tabelle auszublenden
    var csvContentDiv = document.getElementById('csvContent');
    csvContentDiv.innerHTML = '';

    // Setzt das Datei-Upload-Input zurück
    var fileInput = document.getElementById('csvFile');
    fileInput.value = '';

    // Versteckt den Clear-Button wieder
    var clearButton = document.querySelector('.clear-button');
    clearButton.style.display = 'none';

    // Versteckt den Upload-Button
    var uploadButton = document.getElementById('uploadButton');
    uploadButton.style.display = 'none';
}

// Funktion zum Öffnen des Modals
function openModal() {
    var modal = document.getElementById('myModal');
    modal.style.display = 'flex';
}

// Funktion zum Schließen des Modals
function closeModal() {
    var modal = document.getElementById('myModal');
    modal.style.display = 'none';
}

// Funktion zum Hochladen der Zeiten (nur zur Demonstration, implementiere deine Logik hier)
function uploadTimes() {
    clearData();
    closeModal(); // Schließt das Modal nach dem Hochladen
    var csvContentDiv = document.getElementById('csvContent');
    csvContentDiv.innerHTML = '<p class="success-message" >Die Zeiten wurden erfolgreich hochgeladen!</p>';
}
