from datetime import datetime

day_mapping = {
    'Mon': 'Mo',
    'Tue': 'Di',
    'Wed': 'Mi',
    'Thu': 'Do',
    'Fri': 'Fr',
    'Sat': 'Sa',
    'Sun': 'So'
}

def calculate_total_hours(start_time, end_time):
    try:
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')
        delta = end - start
        total_hours = delta.total_seconds() / 3600.0  # Convert seconds to hours
        return round(total_hours, 2)  # Round to two decimal places
    except ValueError:
        return 0.0  # Return 0 if there's an error in time format
