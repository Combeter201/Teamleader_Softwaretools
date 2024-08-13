import csv
from collections import defaultdict
from datetime import datetime
from io import StringIO
from typing import Any, Dict, List, Optional

from .date_utils import calculate_total_hours, get_german_weekday


def parse_csv(csv_content: str) -> Optional[List[Dict[str, str]]]:
    """
    Parst den CSV-Inhalt und gibt eine Liste von Dictionaries zurück.

    Args:
        csv_content (str): Der zu parsende CSV-Inhalt.

    Returns:
        Optional[List[Dict[str, str]]]: Eine Liste von Dictionaries mit den CSV-Daten,
                                        oder None im Fehlerfall.

    Raises:
        csv.Error: Bei Fehlern während des CSV-Parsings.
        ValueError: Bei ungültigen Datumsformaten.
    """
    try:
        csv_content = csv_content.lstrip("\ufeff")  # Entfernt BOM, falls vorhanden
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file, delimiter=";")

        csv_data = []
        for row in reader:
            if any(value.strip() for value in row.values()):
                # Validiere das Datumsformat
                datetime.strptime(row["Datum"], "%d.%m.%Y")
                csv_data.append(row)

        csv_data.sort(key=lambda x: datetime.strptime(x["Datum"], "%d.%m.%Y"))
        return csv_data

    except csv.Error as e:
        print(f"CSV-Parsing-Fehler: {e}")
    except ValueError as e:
        print(f"Ungültiges Datumsformat: {e}")
    except Exception as e:
        print(f"Unerwarteter Fehler beim Parsen des CSV: {e}")

    return None


def group_by_date(csv_data: List[Dict[str, str]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Gruppiert die CSV-Daten nach Datum.

    Args:
        csv_data (List[Dict[str, str]]): Die zu verarbeitenden CSV-Daten.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Ein Dictionary mit nach Datum gruppierten Daten.

    Raises:
        ValueError: Bei ungültigen Zeit- oder Datumsformaten.
    """
    grouped_data = defaultdict(list)

    for row in csv_data:
        try:
            date_str = row["Datum"]
            german_weekday = get_german_weekday(date_str)
            if german_weekday is None:
                raise ValueError(f"Ungültiges Datum: {date_str}")

            formatted_date = f"{german_weekday}, {date_str}"
            total_hours = calculate_total_hours(row["Von"], row["Bis"])
            if total_hours is None:
                raise ValueError(
                    f"Ungültige Zeitangaben: Von {row['Von']} bis {row['Bis']}"
                )

            time_entry = {
                "Von": row["Von"],
                "Bis": row["Bis"],
                "Typ": row["Typ"],
                "Kunde": row["Kunde"],
                "Phase": row["Phase"],
                "Projekt": row["Projekt"],
                "Abrechenbar": row["Abrechenbar"],
                "Beschreibung": row["Beschreibung"],
            }

            existing_entry = next(
                (
                    item
                    for item in grouped_data[formatted_date]
                    if item["Datum"] == date_str
                ),
                None,
            )

            if existing_entry:
                existing_entry["Gesamtstunden"] += total_hours
                existing_entry["Zeiten"].append(time_entry)
            else:
                new_entry = row.copy()
                new_entry["Gesamtstunden"] = total_hours
                new_entry["Zeiten"] = [time_entry]
                grouped_data[formatted_date].append(new_entry)

        except ValueError as e:
            print(f"Fehler bei der Verarbeitung der Zeile: {e}")
            continue

    return grouped_data
