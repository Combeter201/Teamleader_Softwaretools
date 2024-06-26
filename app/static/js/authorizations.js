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

function filterTable() {
        var input, filter, table, tr, td, i, txtValue;
        input = document.getElementById("searchField");
        filter = input.value.toUpperCase();
        table = document.getElementById("userTable");
        tr = table.getElementsByTagName("tr");

        for (i = 0; i < tr.length; i++) {
            td = tr[i].getElementsByTagName("td")[0]; // Nur den ersten td für Mitarbeiter filtern
            if (td) {
                txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    }

    function clearSearch() {
        document.getElementById("searchField").value = "";
        filterTable(); // Tabelle zurücksetzen, um alle Einträge anzuzeigen
    }