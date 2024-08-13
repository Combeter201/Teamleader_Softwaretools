import json
import holidays
from datetime import datetime, timedelta
from urllib.parse import urlencode
import requests
from flask import session
from holidays.countries import Germany
from typing import Dict, List, Tuple, Optional, Any

# Konstanten
TEAMLEADER_API_BASE_URL = "https://api.focus.teamleader.eu"
TEAMLEADER_OAUTH_BASE_URL = "https://app.teamleader.eu/oauth2"


def get_teamleader_token(client_id: str, redirect_uri: str, client_secret: str = None, code: str = None) -> Dict[
    str, Any]:
    """
    Holt oder aktualisiert das Teamleader-Token.

    Args:
        client_id (str): Die Client-ID für die Teamleader-API.
        redirect_uri (str): Die Redirect-URI für die OAuth-Authentifizierung.
        client_secret (str, optional): Das Client-Secret für die Teamleader-API.
        code (str, optional): Der Autorisierungscode für den Token-Austausch.

    Returns:
        Dict[str, Any]: Das Token-Response oder die Autorisierungs-URL.
    """
    if code:
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }
        try:
            response = requests.post(f"{TEAMLEADER_OAUTH_BASE_URL}/access_token", headers=headers, data=body)
            response.raise_for_status()
            token_data = response.json()
            session["refresh_token"] = token_data["refresh_token"]
            return token_data
        except requests.RequestException as e:
            print(f"Fehler beim Token-Abruf: {e}")
            return {"error": str(e)}
    else:
        params = {
            "client_id": client_id,
            "redirect_uri": f"{redirect_uri}/oauth/callback",
            "response_type": "code",
        }
        return f"{TEAMLEADER_OAUTH_BASE_URL}/authorize?{urlencode(params)}"


def refresh_teamleader_token(client_id: str, client_secret: str, refresh_token: str) -> Dict[str, Any]:
    """
    Aktualisiert das Teamleader-Token mit einem Refresh-Token.

    Args:
        client_id (str): Die Client-ID für die Teamleader-API.
        client_secret (str): Das Client-Secret für die Teamleader-API.
        refresh_token (str): Das Refresh-Token zur Aktualisierung des Access-Tokens.

    Returns:
        Dict[str, Any]: Die aktualisierten Token-Daten.
    """
    headers = {"content-type": "application/x-www-form-urlencoded"}
    body = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        response = requests.post(f"{TEAMLEADER_OAUTH_BASE_URL}/access_token", headers=headers, data=body)
        response.raise_for_status()
        token_data = response.json()
        session["access_token"] = token_data["access_token"]
        session["refresh_token"] = token_data["refresh_token"]
        return token_data
    except requests.RequestException as e:
        print(f"Fehler beim Token-Refresh: {e}")
        return {"error": str(e)}


def get_all_users(access_token: str) -> Optional[List[Dict[str, Any]]]:
    """
    Holt eine Liste aller aktiven Benutzer von Teamleader.

    Args:
        access_token (str): Das Access-Token für die Teamleader-API.

    Returns:
        Optional[List[Dict[str, Any]]]: Eine Liste von Benutzerinformationen oder None bei einem Fehler.
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {
            "filter": {"status": ["active"]},
            "sort": [{"field": "first_name"}],
            "page": {"size": 80, "number": 1},
        }

        response = requests.post(f"{TEAMLEADER_API_BASE_URL}/users.list", headers=headers, json=body)
        response.raise_for_status()

        data = response.json()["data"]

        user_list = [
            {
                "employee": f'{user["first_name"]} {user["last_name"]}',
                "id": user["id"],
                "role": user["function"],
            }
            for user in data
        ]

        # Lade die Whitelist-Daten
        with open("static/data/whitelist.json", "r", encoding="utf-8") as f:
            whitelist = json.load(f)

        # Füge Berechtigungen zu jedem Benutzer hinzu
        for user in user_list:
            user_id = user["id"]
            whitelist_entry = next((entry for entry in whitelist if entry["id"] == user_id), None)
            if whitelist_entry:
                user.update({
                    "upload_times": whitelist_entry.get("upload_times", "false"),
                    "manage_times": whitelist_entry.get("manage_times", "false"),
                    "absence": whitelist_entry.get("absence", "false"),
                    "birthday": whitelist_entry.get("birthday", "false"),
                    "authorizations": whitelist_entry.get("authorizations", "false"),
                })

        return user_list

    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Benutzer: {e}")
        return None
    except KeyError as e:
        print(f"Fehler beim Parsen der JSON-Daten: {e}")
        return None


def get_teamleader_user(access_token: str) -> Dict[str, str]:
    """
    Holt Informationen über den aktuellen Benutzer von Teamleader.

    Args:
        access_token (str): Das Access-Token für die Teamleader-API.

    Returns:
        Dict[str, str]: Ein Dictionary mit Benutzerinformationen.
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{TEAMLEADER_API_BASE_URL}/users.me", headers=headers)
        response.raise_for_status()
        data = response.json()["data"]
        return {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "id": data["id"],
        }
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Benutzerinformationen: {e}")
        return {"error": str(e)}


def get_user_absence(
        access_token: str,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        week: Optional[int] = None,
        week_dates: Optional[List[str]] = None
) -> List[str]:
    """
    Holt Abwesenheitsinformationen für einen Benutzer in einem bestimmten Zeitraum.

    Args:
        access_token (str): Das Access-Token für die Teamleader-API.
        user_id (str): Die ID des Benutzers.
        start_date (datetime): Das Startdatum des Zeitraums.
        end_date (datetime): Das Enddatum des Zeitraums.
        week (Optional[int]): Die Wochennummer (falls anwendbar).
        week_dates (Optional[List[str]]): Eine Liste von Datumswerten für die Woche.

    Returns:
        List[str]: Eine Liste von Abwesenheitsinformationen.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    body = {
        "id": user_id,
        "filter": {
            "starts_after": start_date.isoformat(),
            "ends_before": end_date.isoformat(),
        },
    }

    try:
        response = requests.post(f"{TEAMLEADER_API_BASE_URL}/users.listDaysOff", headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        # Lade die Typen der freien Tage
        with open("static/data/day_off_type.json", "r", encoding="utf-8") as f:
            day_off_types = json.load(f)
        day_off_type_dict = {item["id"]: item["type"] for item in day_off_types}

        # Erstelle ein holidays-Objekt für Bayern
        bavarian_holidays = Germany(prov="BY", years=start_date.year, language='de')

        absence_info = []

        if week and week_dates:
            for date_str in week_dates:
                date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()

                # Prüfe auf Feiertage
                if date_obj in bavarian_holidays:
                    absence_info.append(bavarian_holidays.get(date_obj))
                    continue

                entry_found = False
                if "data" in data and data["data"]:
                    for entry in data["data"]:
                        entry_date = datetime.strptime(entry["starts_at"], "%Y-%m-%dT%H:%M:%S%z").date()
                        if entry_date == date_obj:
                            leave_type = day_off_type_dict.get(entry["leave_type"]["id"], "Office")
                            if leave_type in ["Urlaub", "Unbezahlter Urlaub", "Urlaubsdokus_Studis", "Sonderurlaub",
                                              "Resturlaub"]:
                                status_icon = "✅ " if entry["status"] == "approved" else "❌ "
                                leave_type = status_icon + leave_type
                            absence_info.append(leave_type)
                            entry_found = True
                            break

                if not entry_found:
                    absence_info.append("Office")

            return absence_info
        else:
            today = start_date + timedelta(days=1)
            if today in bavarian_holidays:
                return [bavarian_holidays.get(today)]

            if "data" in data and data["data"]:
                leave_type = day_off_type_dict.get(data["data"][0]["leave_type"]["id"], "Office")
                status = data["data"][0]["status"]
                if leave_type in ["Urlaub", "Unbezahlter Urlaub", "Urlaubsdokus_Studis", "Sonderurlaub", "Resturlaub"]:
                    status_icon = "✅ " if status == "approved" else "❌ "
                    leave_type = status_icon + leave_type
                return [leave_type]
            else:
                return ["Office"]

    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Abwesenheitsinformationen: {e}")
        return ["Office"] * (5 if week else 1)
    except Exception as ex:
        print(f"Unerwarteter Fehler: {ex}")
        return ["Office"] * (5 if week else 1)


def get_teamleader_teams(access_token: str, team_id: str, team_id2: Optional[str] = None,
                         team_id3: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Holt Informationen über die jeweiligen Teams von Teamleader.

    Args:
        access_token (str): Das Access-Token für die Teamleader-API.
        team_id (str): Die ID des primären Teams.
        team_id2 (Optional[str]): Die ID eines zweiten Teams (optional).
        team_id3 (Optional[str]): Die ID eines dritten Teams (optional).

    Returns:
        Optional[List[Dict[str, Any]]]: Eine Liste von Team-Informationen oder None bei einem Fehler.
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        if team_id == "-1":
            body = {"filter": {}}
        elif team_id2 is not None and team_id3 is not None:
            body = {"filter": {"ids": [team_id, team_id2, team_id3]}}
        else:
            body = {"filter": {"ids": [team_id]}}

        response = requests.post(f"{TEAMLEADER_API_BASE_URL}/teams.list", headers=headers, json=body)
        response.raise_for_status()

        return response.json()["data"]

    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Teams: {e}")
        return None
    except KeyError as e:
        print(f"Fehler beim Parsen der JSON-Daten: {e}")
        return None


def get_teamleader_user_info(access_token: str, member_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Holt detaillierte Informationen über einen Benutzer von Teamleader.

    Args:
        access_token (str): Das Access-Token für die Teamleader-API.
        member_id (str): Die ID des Benutzers.

    Returns:
        Tuple[Optional[str], Optional[str]]: Ein Tupel mit Vorname und Nachname des Benutzers oder (None, None) bei einem Fehler.
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {"id": member_id}

        response = requests.post(f"{TEAMLEADER_API_BASE_URL}/users.info", headers=headers, json=body)
        response.raise_for_status()

        data = response.json()["data"]
        return data.get("first_name", ""), data.get("last_name", "")

    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Benutzerinformationen: {e}")
        return None, None
    except KeyError as e:
        print(f"Fehler beim Parsen der JSON-Daten: {e}")
        return None, None


def get_number_of_absence_days(access_token: str, member_id: str, start_date: str, end_date: str) -> int:
    """
    Berechnet die Anzahl der Abwesenheitstage für einen Benutzer in einem bestimmten Zeitraum.

    Args:
        access_token (str): Das Access-Token für die Teamleader-API.
        member_id (str): Die ID des Benutzers.
        start_date (str): Das Startdatum des Zeitraums.
        end_date (str): Das Enddatum des Zeitraums.

    Returns:
        int: Die Anzahl der Abwesenheitstage.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    body = {
        "id": member_id,
        "filter": {"starts_after": start_date, "ends_before": end_date}
    }
    try:
        response = requests.post(f"{TEAMLEADER_API_BASE_URL}/users.listDaysOff", headers=headers, json=body)
        response.raise_for_status()

        data = response.json()

        # Lade die IDs für relevante Abwesenheitstypen
        with open("static/data/day_off_type.json", "r", encoding="utf-8") as f:
            day_off_types = json.load(f)

        relevant_ids = [
            item["id"] for item in day_off_types
            if item["type"] in [
                "Urlaub", "Krankheit", "Berufsschule/FH/Uni", "Elternzeit",
                "Kind krank", "Überstunden", "Mutterschutz", "Kurzarbeit",
                "Resturlaub", "Sonderurlaub", "Unbezahlter Urlaub", "Urlaubsdoku_Studis"
            ]
        ]

        return sum(1 for item in data["data"] if item["leave_type"]["id"] in relevant_ids)

    except requests.RequestException as e:
        print(f"HTTP-Fehler aufgetreten: {e}")
        return 0
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return 0


def get_teamleader_user_times(
        access_token: str,
        member_id: str,
        first_tmstmp: str,
        second_tmstmp: str,
        third_tmstmp: str,
        end_tmstmp: str,
        fourth_tmstmp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Holt Zeiterfassungsdaten für einen Benutzer in mehreren Zeitintervallen.

    Args:
        access_token (str): Das Access-Token für die Teamleader-API.
        member_id (str): Die ID des Benutzers.
        first_tmstmp (str): Der Startzeitpunkt des ersten Intervalls.
        second_tmstmp (str): Der Startzeitpunkt des zweiten Intervalls.
        third_tmstmp (str): Der Startzeitpunkt des dritten Intervalls.
        end_tmstmp (str): Der Endzeitpunkt des letzten Intervalls.
        fourth_tmstmp (Optional[str]): Der Startzeitpunkt eines optionalen vierten Intervalls.

    Returns:
        Dict[str, Any]: Eine Zusammenfassung der Zeiterfassungsdaten.
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}

        time_intervals = [
            {"started_after": first_tmstmp, "ended_before": second_tmstmp},
            {"started_after": second_tmstmp, "ended_before": third_tmstmp},
            {"started_after": third_tmstmp, "ended_before": end_tmstmp if fourth_tmstmp is None else fourth_tmstmp},
        ]

        if fourth_tmstmp:
            time_intervals.append({"started_after": fourth_tmstmp, "ended_before": end_tmstmp})

        all_work_entries = []

        for interval in time_intervals:
            body = {
                "filter": {
                    "user_id": member_id,
                    "started_after": interval["started_after"],
                    "ended_before": interval["ended_before"],
                },
                "sort": [{"field": "starts_on"}],
                "page": {"size": 100, "number": 1},
            }

            response = requests.post(f"{TEAMLEADER_API_BASE_URL}/timeTracking.list", headers=headers, json=body)
            response.raise_for_status()

            data = response.json()
            if "data" in data and data["data"]:
                all_work_entries.extend(data["data"])

        if not all_work_entries:
            all_work_entries = [{"started_on": "", "duration": 0, "invoiceable": False}]

        return summarize_work_entries(all_work_entries)

    except requests.RequestException as e:
        return "Sie haben keine Berechtigung, dieses Team einzusehen"
    except (KeyError, ValueError) as e:
        return str(e)


def summarize_work_entries(work_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fasst die Zeiterfassungseinträge zusammen.

    Args:
        work_entries (List[Dict[str, Any]]): Eine Liste von Zeiterfassungseinträgen.

    Returns:
        Dict[str, Any]: Eine Zusammenfassung der Zeiterfassungsdaten.
    """
    total_duration_seconds = sum(entry["duration"] for entry in work_entries)
    invoiceable_duration_seconds = sum(entry["duration"] for entry in work_entries if entry["invoiceable"])
    non_invoiceable_duration_seconds = total_duration_seconds - invoiceable_duration_seconds
    work_days = {entry["started_on"] for entry in work_entries}

    total_days = len(work_days)
    workdays_hours = total_days * 8  # Annahme: 8 Stunden pro Arbeitstag
    total_hours = total_duration_seconds / 3600

    overtime_hours = max(0, total_hours - workdays_hours)

    invoiceable_percentage = (
        ((invoiceable_duration_seconds - overtime_hours * 3600) / total_duration_seconds) * 100
        if total_duration_seconds > 0 else 0
    )

    return {
        "total_duration": f"{total_hours:.2f}",
        "invoiceable_duration": f"{invoiceable_duration_seconds / 3600:.2f}",
        "non_invoiceable_duration": f"{non_invoiceable_duration_seconds / 3600:.2f}",
        "total_days": total_days,
        "invoiceable_percentage": round(invoiceable_percentage, 2),
        "overtime_hours": round(overtime_hours, 2),
    }


def get_contact_info(access_token: str):

    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{TEAMLEADER_API_BASE_URL}/contacts.list", headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()

        birthday_contacts = []
        today = datetime.now().date()

        for contact in data.get('data', []):
            name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
            birthdate_str = contact.get('birthdate')

            if name and birthdate_str:
                birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()

                if birthdate.month == today.month and birthdate.day == today.day:
                    age = today.year - birthdate.year
                    birthday_contacts.append({
                        "name": name,
                        "age": age
                    })

        return birthday_contacts

    except requests.RequestException as e:
        print(f"Ein Fehler ist bei der Anfrage aufgetreten: {e}")
        return None