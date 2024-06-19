import json

import requests
from urllib.parse import urlencode


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
        return response.json()
    else:
        params = {
            'client_id': client_id,
            'redirect_uri': f'{redirect_uri}/oauth/callback',
            'response_type': 'code',
        }
        auth_url = f"https://app.teamleader.eu/oauth2/authorize?{urlencode(params)}"
        return auth_url


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
