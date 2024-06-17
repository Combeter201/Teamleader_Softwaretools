from flask import Flask, render_template, request
import csv
from io import StringIO
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

# Mapping der englischen Wochentage auf deutsche Abkürzungen
day_mapping = {
    'Mon': 'Mo',
    'Tue': 'Di',
    'Wed': 'Mi',
    'Thu': 'Do',
    'Fri': 'Fr'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/zeiten-hochladen.html')
def zeiten_hochladen():
    return render_template('zeiten-hochladen.html')

@app.route('/zeiten-verwalten.html')
def zeiten_verwalten():
    return render_template('zeiten-verwalten.html')

@app.route('/zeiten-hochladen.html', methods=['POST'])
def upload():
    if 'csvFile' not in request.files:
        return render_template('zeiten-hochladen.html', message='Keine Datei ausgewählt!')

    file = request.files['csvFile']

    if file.filename == '':
        return render_template('zeiten-hochladen.html', message='Keine Datei ausgewählt!')

    if file and file.filename.endswith('.csv'):
        csv_content = file.stream.read().decode('utf-8')

        # Parse CSV content
        csv_data = parse_csv(csv_content)

        if csv_data is None:
            return render_template('zeiten-hochladen.html', message='Fehler beim Parsen der CSV-Datei!')

        # Sort and group CSV data by date
        sorted_data = sort_and_group_by_date(csv_data)
        return render_template('zeiten-hochladen.html', sorted_data=sorted_data)

    return render_template('zeiten-hochladen.html', message='Ungültiger Dateityp!')

def parse_csv(csv_content):
    try:
        # Remove BOM if present
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]

        # Use StringIO to simulate a file object from string
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file, delimiter=';')  # Specify delimiter as semicolon

        # Read CSV data and convert to list of dictionaries
        csv_data = [row for row in reader]

        # Sort CSV data by 'Datum' field (assuming 'Datum' is the date field)
        csv_data.sort(key=lambda x: datetime.strptime(x['Datum'], '%d.%m.%Y'))

        return csv_data

    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return None

def sort_and_group_by_date(csv_data):
    sorted_data = defaultdict(list)

    for row in csv_data:
        datum = row['Datum']
        # Convert Datum string to datetime object
        date_obj = datetime.strptime(datum, '%d.%m.%Y')
        # Get weekday name in English and map to German abbreviation
        weekday = date_obj.strftime('%a')
        if weekday in day_mapping:
            weekday = day_mapping[weekday]
        # Format with date
        formatted_date = date_obj.strftime(', %d.%m.%Y')
        # Calculate total hours worked for the day
        total_hours = calculate_total_hours(row['Von'], row['Bis'])

        # Check if entry already exists for the day
        existing_entry = next((item for item in sorted_data[f"{weekday}{formatted_date}"] if item['Datum'] == datum), None)
        if existing_entry:
            # Update existing entry with cumulative total hours
            existing_entry['Gesamtstunden'] += total_hours
            # Add current time block to existing entry
            existing_entry['Zeiten'].append({'Von': row['Von'], 'Bis': row['Bis'], 'Typ': row['Typ'], 'Kunde': row['Kunde'],
                                             'Phase': row['Phase'], 'Projekt': row['Projekt'], 'Abrechenbar': row['Abrechenbar']})
        else:
            # Add new entry with total hours and current time block
            row['Gesamtstunden'] = total_hours
            row['Zeiten'] = [{'Von': row['Von'], 'Bis': row['Bis'], 'Typ': row['Typ'], 'Kunde': row['Kunde'],
                              'Phase': row['Phase'], 'Projekt': row['Projekt'], 'Abrechenbar': row['Abrechenbar']}]
            sorted_data[f"{weekday}{formatted_date}"].append(row)

    return sorted_data

def calculate_total_hours(start_time, end_time):
    try:
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')
        delta = end - start
        total_hours = delta.total_seconds() / 3600.0  # Convert seconds to hours
        return round(total_hours, 2)  # Round to two decimal places
    except ValueError:
        return 0.0  # Return 0 if there's an error in time format

if __name__ == '__main__':
    app.run(debug=True)
