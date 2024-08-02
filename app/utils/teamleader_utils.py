import json
from datetime import datetime
from urllib.parse import urlencode

import requests
from flask import session


def get_teamleader_token(client_id, redirect_uri, client_secret=None, code=None):
    if code:
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }
        response = requests.post(
            "https://app.teamleader.eu/oauth2/access_token", headers=headers, data=body
        )
        session["refresh_token"] = response.json()["refresh_token"]
        return response.json()
    else:
        params = {
            "client_id": client_id,
            "redirect_uri": f"{redirect_uri}/oauth/callback",
            "response_type": "code",
        }
        auth_url = f"https://app.teamleader.eu/oauth2/authorize?{urlencode(params)}"
        return auth_url


def refresh_teamleader_token(client_id, client_secret, refresh_token):
    headers = {"content-type": "application/x-www-form-urlencoded"}
    body = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    response = requests.post(
        "https://app.teamleader.eu/oauth2/access_token", headers=headers, data=body
    )
    session["access_token"] = response.json()["access_token"]
    session["refresh_token"] = response.json()["refresh_token"]
    return response.json()


def get_all_users(access_token):
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        body = json.dumps(
            {
                "filter": {"status": ["active"]},
                "sort": [{"field": "first_name"}],
                "page": {"size": 80, "number": 1},
            }
        )

        response = requests.post(
            "https://api.focus.teamleader.eu/users.list", headers=headers, data=body
        )
        response.raise_for_status()

        data = response.json()["data"]

        user_list = []
        for user in data:
            user_info = {
                "employee": f'{user["first_name"]} {user["last_name"]}',
                "id": user["id"],
                "role": user["function"],
            }
            user_list.append(user_info)

        with open("static/data/whitelist.json", "r") as f:
            whitelist = json.load(f)

        for user in user_list:
            user_id = user["id"]
            # Suche nach dem Benutzer in der whitelist.json
            for entry in whitelist:
                if entry["id"] == user_id:
                    # Füge die Berechtigungen zum Benutzer hinzu
                    user["upload_times"] = entry.get("upload_times", "false")
                    user["manage_times"] = entry.get("manage_times", "false")
                    user["absence"] = entry.get("absence", "false")
                    user["authorizations"] = entry.get("authorizations", "false")
                    break  # Wenn der Benutzer gefunden wurde, beende die Suche

        return user_list

    except requests.exceptions.RequestException as e:
        print(f"Error fetching teams: {e}")
        return None
    except KeyError as e:
        print(f"Error parsing JSON data: {e}")
        return None


def get_teamleader_user(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.focus.teamleader.eu/users.me", headers=headers)
    response.raise_for_status()
    data = response.json()["data"]
    return {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "id": data["id"],
    }


def get_user_absence(
        access_token, userId, startDate, endDate, week=None, week_dates=None
):
    headers = {"Authorization": f"Bearer {access_token}"}
    body = json.dumps(
        {
            "id": userId,
            "filter": {
                "starts_after": startDate.isoformat(),
                "ends_before": endDate.isoformat(),
            },
        }
    )

    try:
        response = requests.post(
            "https://api.focus.teamleader.eu/users.listDaysOff",
            headers=headers,
            data=body,
        )
        response.raise_for_status()  # Raise exception for HTTP errors (4xx or 5xx)

        data = response.json()
        absence_info = []

        if week and week_dates:
            # Load day_off_type.json
            with open("static/data/day_off_type.json", "r") as f:
                day_off_types = json.load(f)

            # Create a dictionary for quick lookup of day off types
            day_off_type_dict = {item["id"]: item["type"] for item in day_off_types}

            for date_str in week_dates:
                date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
                entry_found = False

                if "data" in data and len(data["data"]) > 0:
                    for entry in data["data"]:
                        entry_date = datetime.strptime(
                            entry["starts_at"], "%Y-%m-%dT%H:%M:%S%z"
                        ).date()
                        if entry_date == date_obj:
                            leave_type_id = entry["leave_type"]["id"]
                            absence_info.append(
                                day_off_type_dict.get(leave_type_id, "Office")
                            )
                            entry_found = True
                            break

                if not entry_found:
                    absence_info.append("Office")

            return absence_info
        else:
            if "data" in data and len(data["data"]) > 0:
                leave_type_id = data["data"][0]["leave_type"]["id"]

                # Load day_off_type.json
                with open("static/data/day_off_type.json", "r") as f:
                    day_off_types = json.load(f)

                # Find matching type
                for day_off_type in day_off_types:
                    if day_off_type["id"] == leave_type_id:
                        absence_info.append(day_off_type["type"])
                        return absence_info

                # If no match found, return default type
                absence_info.append("Office")
                return absence_info
            else:
                # If response is empty or does not contain 'data'
                absence_info.append("Office")
                return absence_info
    except requests.exceptions.RequestException as e:
        # Handle HTTP errors
        if week:
            return ["Office", "Office", "Office", "Office", "Office"]
        else:
            return ["Office"]

    except Exception as ex:
        # Handle other unexpected errors
        if week:
            return ["Office", "Office", "Office", "Office", "Office"]
        else:
            return ["Office"]


def get_teamleader_teams(access_token, team_id, team_id2=None, team_id3=None):
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        if team_id == "-1":
            body = json.dumps({"filter": {}})
        elif team_id2 != None and team_id3 != None:
            body = json.dumps({"filter": {"ids": [team_id, team_id2, team_id3]}})
        else:
            body = json.dumps({"filter": {"ids": [team_id]}})

        response = requests.post(
            "https://api.focus.teamleader.eu/teams.list", headers=headers, data=body
        )
        response.raise_for_status()

        data = response.json()["data"]

        return data  # Oder eine andere gewünschte Rückgabe

    except requests.exceptions.RequestException as e:
        print(f"Error fetching teams: {e}")
        return None
    except KeyError as e:
        print(f"Error parsing JSON data: {e}")
        return None


def get_teamleader_user_info(access_token, member_id):
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        body = json.dumps({"id": member_id})

        response = requests.post(
            "https://api.focus.teamleader.eu/users.info", headers=headers, data=body
        )
        response.raise_for_status()

        data = response.json()["data"]
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        return first_name, last_name

    except requests.exceptions.RequestException as e:
        print(f"Error fetching user info: {e}")
        return None, None
    except KeyError as e:
        print(f"Error parsing JSON data: {e}")
        return None, None


def get_number_of_absence_days(access_token, member_id, startDate, endDate):
    headers = {"Authorization": f"Bearer {access_token}"}
    body = json.dumps(
        {"id": member_id, "filter": {"starts_after": startDate, "ends_before": endDate}}
    )
    try:
        response = requests.post(
            "https://api.focus.teamleader.eu/users.listDaysOff",
            headers=headers,
            data=body,
        )
        response.raise_for_status()

        data = response.json()

        # Lese die IDs für "Urlaub" und "Krank" aus der day_off_type.json Datei
        with open("static/data/day_off_type.json", "r") as f:
            day_off_types = json.load(f)

        vacation_and_sick_ids = [
            item["id"]
            for item in day_off_types
            if item["type"]
               in [
                   "Urlaub",
                   "Krankheit",
                   "Berufsschule/FH/Uni",
                   "Elternzeit",
                   "Kind krank",
                   "Überstunden",
                   "Mutterschutz",
                   "Kurzarbeit",
                   "Resturlaub",
                   "Sonderurlaub",
                   "Unbezahlter Urlaub",
                   "Urlaubsdoku_Studis",
               ]
        ]
        target_count = 0

        # Iteriere durch die Daten und zähle die Vorkommen der Ziel-IDs
        for item in data["data"]:
            if item["leave_type"]["id"] in vacation_and_sick_ids:
                target_count += 1

        return target_count

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")


def get_teamleader_user_times(
        access_token,
        member_id,
        first_tmstmp,
        second_tmstmp,
        third_tmstmp,
        end_tmstmp,
        fourth_tmstmp=None,
):
    try:
        headers = {"Authorization": f"Bearer {access_token}"}

        # Bestimme die Zeitintervalle basierend auf fourth_tmstmp
        if fourth_tmstmp is None:
            time_intervals = [
                {"started_after": first_tmstmp, "ended_before": second_tmstmp},
                {"started_after": second_tmstmp, "ended_before": third_tmstmp},
                {"started_after": third_tmstmp, "ended_before": end_tmstmp},
            ]
        else:
            time_intervals = [
                {"started_after": first_tmstmp, "ended_before": second_tmstmp},
                {"started_after": second_tmstmp, "ended_before": third_tmstmp},
                {"started_after": third_tmstmp, "ended_before": fourth_tmstmp},
                {"started_after": fourth_tmstmp, "ended_before": end_tmstmp},
            ]

        all_work_entries = []

        for interval in time_intervals:
            body = {
                "filter": {
                    "user_id": member_id,
                    "started_after": interval["started_after"],
                    "ended_before": interval["ended_before"],
                    "sort": [{"field": "starts_on"}],
                },
                "page": {"size": 100, "number": 1},
            }

            response = requests.post(
                "https://api.focus.teamleader.eu/timeTracking.list",
                headers=headers,
                json=body,
            )
            response.raise_for_status()

            data = response.json()

            if (
                    "data" in data and data["data"]
            ):  # Überprüfen, ob 'data' existiert und nicht leer ist
                all_work_entries.extend(data["data"])

        if not all_work_entries:  # Wenn all_work_entries leer ist, Fehler auslösen
            all_work_entries = [{"started_on": "", "duration": 0, "invoiceable": False}]

        total_duration = summarize_work_entries(all_work_entries)
        return total_duration

    except requests.exceptions.RequestException as e:
        return "Dir fehlen die Berechtigung, um dieses Team anzuschauen"
    except (KeyError, ValueError) as e:
        return e


def summarize_work_entries(work_entries):
    total_duration_seconds = 0
    invoiceable_duration_seconds = 0
    non_invoiceable_duration_seconds = 0
    work_days = set()

    for entry in work_entries:
        duration_seconds = entry["duration"]
        total_duration_seconds += duration_seconds

        if entry["invoiceable"]:
            invoiceable_duration_seconds += duration_seconds
        else:
            non_invoiceable_duration_seconds += duration_seconds

        work_days.add(entry["started_on"])

    total_days = len(work_days)

    # Calculate overtime
    workdays_count = total_days
    workdays_hours = workdays_count * 8  # Assuming 8 hours per workday
    total_hours = total_duration_seconds / 3600

    overtime_hours = max(0, total_hours - workdays_hours)

    # Calculate invoiceable percentage
    if total_duration_seconds > 0:
        invoiceable_percentage = (
                                         (invoiceable_duration_seconds - overtime_hours * 3600)
                                         / total_duration_seconds
                                 ) * 100
    else:
        invoiceable_percentage = 0

    # Convert total duration to hours with decimal minutes
    total_hours_decimal = total_duration_seconds / 3600
    invoiceable_hours_decimal = invoiceable_duration_seconds / 3600
    non_invoiceable_hours_decimal = non_invoiceable_duration_seconds / 3600

    return {
        "total_duration": f"{total_hours_decimal:.2f}",
        "invoiceable_duration": f"{invoiceable_hours_decimal:.2f}",
        "non_invoiceable_duration": f"{non_invoiceable_hours_decimal:.2f}",
        "total_days": total_days,
        "invoiceable_percentage": round(invoiceable_percentage, 2),
        "overtime_hours": round(overtime_hours, 2),
    }
