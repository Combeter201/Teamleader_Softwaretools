// Funktion zum Senden der ID an Python
function sendSelectedIdToPython() {
    const teamSelect = document.getElementById('teamSelect');
    const selectedOption = teamSelect.options[teamSelect.selectedIndex];
    const selectedId = selectedOption.getAttribute('id');

    fetch('/manage-times.html', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ selectedId: selectedId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.text();
    })
    .then(data => {
        document.body.innerHTML = data;  // This line can replace the current content with the response content
    })
    .catch(error => {
        console.error('Error:', error);
    });

}