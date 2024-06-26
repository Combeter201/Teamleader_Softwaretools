import json

import requests
from urllib.parse import urlencode

from flask import session


def get_teamleader_token(client_id, redirect_uri, client_secret=None, code=None):
    if code:
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        body = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post('https://app.teamleader.eu/oauth2/access_token', headers=headers, data=body)
        session['refresh_token'] = response.json()['refresh_token']
        return response.json()
    else:
        params = {
            'client_id': client_id,
            'redirect_uri': f'{redirect_uri}/oauth/callback',
            'response_type': 'code',
        }
        auth_url = f"https://app.teamleader.eu/oauth2/authorize?{urlencode(params)}"
        return auth_url


def refresh_teamleader_token(client_id, client_secret, refresh_token):
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    body = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post('https://app.teamleader.eu/oauth2/access_token', headers=headers, data=body)
    session['access_token'] = response.json()['access_token']
    session['refresh_token'] = response.json()['refresh_token']
    return response.json()


def get_all_users(access_token):
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        body = json.dumps({
            "filter": {
                "status": [
                    "active"
                ]
            },
            "sort": [
                {
                    "field": "first_name"
                }
            ],
            "page": {
                "size": 80,
                "number": 1
            }
        })

        response = requests.post('https://api.focus.teamleader.eu/users.list', headers=headers, data=body)
        response.raise_for_status()

        data = response.json()['data']

        user_list = []
        for user in data:
            user_info = {
                'employee': f'{user["first_name"]} {user["last_name"]}',
                'id': user['id'],
                'role': user['function']
            }
            user_list.append(user_info)

        with open('static/data/whitelist.json', 'r') as f:
            whitelist = json.load(f)

        for user in user_list:
            user_id = user['id']
            # Suche nach dem Benutzer in der whitelist.json
            for entry in whitelist:
                if entry['id'] == user_id:
                    # Füge die Berechtigungen zum Benutzer hinzu
                    user['upload_times'] = entry.get('upload_times', 'false')
                    user['manage_times'] = entry.get('manage_times', 'false')
                    user['authorizations'] = entry.get('authorizations', 'false')
                    break  # Wenn der Benutzer gefunden wurde, beende die Suche

        return user_list

    except requests.exceptions.RequestException as e:
        print(f"Error fetching teams: {e}")
        return None
    except KeyError as e:
        print(f"Error parsing JSON data: {e}")
        return None


def get_teamleader_user(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.focus.teamleader.eu/users.me', headers=headers)
    response.raise_for_status()
    data = response.json()['data']
    return {
        'first_name': data['first_name'],
        'last_name': data['last_name'],
        'id': data['id']
    }


def get_teamleader_teams(access_token, team_id):
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        body = json.dumps({
            "filter": {
                "ids": [
                    team_id
                ]
            }
        })

        response = requests.post('https://api.focus.teamleader.eu/teams.list', headers=headers, data=body)
        response.raise_for_status()

        data = response.json()['data']

        return data  # Oder eine andere gewünschte Rückgabe

    except requests.exceptions.RequestException as e:
        print(f"Error fetching teams: {e}")
        return None
    except KeyError as e:
        print(f"Error parsing JSON data: {e}")
        return None


def get_teamleader_user_info(access_token, member_id):
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        body = json.dumps({
            "id": member_id
        })

        response = requests.post('https://api.focus.teamleader.eu/users.info', headers=headers, data=body)
        response.raise_for_status()

        data = response.json()['data']
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        return first_name, last_name

    except requests.exceptions.RequestException as e:
        print(f"Error fetching user info: {e}")
        return None, None
    except KeyError as e:
        print(f"Error parsing JSON data: {e}")
        return None, None


def get_teamleader_user_times(access_token, member_id, first_tmstmp, second_tmstmp, third_tmstmp, end_tmstmp, fourth_tmstmp=None):
    try:
        headers = {'Authorization': f'Bearer {access_token}'}

        # Bestimme die Zeitintervalle basierend auf fourth_tmstmp
        if fourth_tmstmp is None:
            time_intervals = [
                {"started_after": first_tmstmp, "ended_before": second_tmstmp},
                {"started_after": second_tmstmp, "ended_before": third_tmstmp},
                {"started_after": third_tmstmp, "ended_before": end_tmstmp}
            ]
        else:
            time_intervals = [
                {"started_after": first_tmstmp, "ended_before": second_tmstmp},
                {"started_after": second_tmstmp, "ended_before": third_tmstmp},
                {"started_after": third_tmstmp, "ended_before": fourth_tmstmp},
                {"started_after": fourth_tmstmp, "ended_before": end_tmstmp}
            ]

        all_work_entries = []

        for interval in time_intervals:
            body = {
                "filter": {
                    "user_id": member_id,
                    "started_after": interval["started_after"],
                    "ended_before": interval["ended_before"],
                    "sort": [{"field": "starts_on"}]
                }
            }

            response = requests.post('https://api.focus.teamleader.eu/timeTracking.list', headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and data['data']:  # Überprüfen, ob 'data' existiert und nicht leer ist
                all_work_entries.extend(data['data'])

        if not all_work_entries:  # Wenn all_work_entries leer ist, Fehler auslösen
            raise ValueError("Keine Arbeitszeiten gefunden.")

        total_duration = summarize_work_entries(all_work_entries)
        return total_duration

    except requests.exceptions.RequestException as e:
        return None
    except (KeyError, ValueError) as e:
        return None


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
        invoiceable_percentage = ((invoiceable_duration_seconds - overtime_hours * 3600) / total_duration_seconds) * 100
    else:
        invoiceable_percentage = 0

    # Convert total duration to hours and minutes
    total_hours = total_duration_seconds // 3600
    total_minutes = (total_duration_seconds % 3600) // 60

    return {
        "total_duration": f"{total_hours},{total_minutes:02}",
        "invoiceable_duration": f"{invoiceable_duration_seconds // 3600},{(invoiceable_duration_seconds % 3600) // 60:02}",
        "non_invoiceable_duration": f"{non_invoiceable_duration_seconds // 3600},{(non_invoiceable_duration_seconds % 3600) // 60:02}",
        "total_days": total_days,
        "invoiceable_percentage": round(invoiceable_percentage, 2),
        "overtime_hours": round(overtime_hours, 2)
    }
