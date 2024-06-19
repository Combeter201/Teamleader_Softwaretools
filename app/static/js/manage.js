document.addEventListener('DOMContentLoaded', function() {
    const teams = [
        { label: 'GF', options: [
            { value: 'option1', text: 'René Ott' },
            { value: 'option2', text: 'Daniel Rösch' }
        ]},
        { label: 'HR', options: [
            { value: 'option3', text: 'Anja Rausch' }
        ]},
        { label: 'Development', options: [
            { value: 'option4', text: 'Fabian Hemberger' },
            { value: 'option5', text: 'Fabian Margraf' },
            { value: 'option6', text: 'Jörg Knaust' }
        ]},
        { label: 'Consulting', options: [
            { value: 'option7', text: 'Fabian Ott' },
            { value: 'option8', text: 'Jannis Schuhmann' },
            { value: 'option9', text: 'Tobias Droglauer' }
        ]},
        { label: 'AI', options: [
            { value: 'option10', text: 'Tillmann Richl' }
        ]},
        { label: 'Finance', options: [
            { value: 'option11', text: 'Valentin Böck' }
        ]},
        { label: 'Sonstige', options: [
            { value: 'option12', text: 'Wolfgang Stifter' }
        ]}
    ];

    const teamSelect = document.getElementById('teamSelect');

    teams.forEach(group => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = group.label;

        group.options.forEach(optionData => {
            const option = document.createElement('option');
            option.value = optionData.value;
            option.textContent = optionData.text;
            optgroup.appendChild(option);
        });

        teamSelect.appendChild(optgroup);
    });

    // Adding a disabled placeholder option
    const placeholderOption = document.createElement('option');
    placeholderOption.disabled = true;
    placeholderOption.selected = true;
    placeholderOption.hidden = true;
    placeholderOption.textContent = 'Choose Team';
    teamSelect.insertBefore(placeholderOption, teamSelect.firstChild);
});
