import csv
from io import StringIO
from datetime import datetime
from collections import defaultdict
from .date_utils import calculate_total_hours, day_mapping

def parse_csv(csv_content):
    try:
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file, delimiter=';')
        csv_data = [row for row in reader]
        csv_data.sort(key=lambda x: datetime.strptime(x['Datum'], '%d.%m.%Y'))
        return csv_data
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return None

def sort_and_group_by_date(csv_data):
    sorted_data = defaultdict(list)
    for row in csv_data:
        datum = row['Datum']
        date_obj = datetime.strptime(datum, '%d.%m.%Y')
        weekday = date_obj.strftime('%a')
        weekday = day_mapping.get(weekday, weekday)
        formatted_date = date_obj.strftime(', %d.%m.%Y')
        total_hours = calculate_total_hours(row['Von'], row['Bis'])

        existing_entry = next((item for item in sorted_data[f"{weekday}{formatted_date}"] if item['Datum'] == datum), None)
        if existing_entry:
            existing_entry['Gesamtstunden'] += total_hours
            existing_entry['Zeiten'].append(
                {'Von': row['Von'], 'Bis': row['Bis'], 'Typ': row['Typ'], 'Kunde': row['Kunde'],
                 'Phase': row['Phase'], 'Projekt': row['Projekt'], 'Abrechenbar': row['Abrechenbar']})
        else:
            row['Gesamtstunden'] = total_hours
            row['Zeiten'] = [{'Von': row['Von'], 'Bis': row['Bis'], 'Typ': row['Typ'], 'Kunde': row['Kunde'],
                              'Phase': row['Phase'], 'Projekt': row['Projekt'], 'Abrechenbar': row['Abrechenbar']}]
            sorted_data[f"{weekday}{formatted_date}"].append(row)
    return sorted_data
