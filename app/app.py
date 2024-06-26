import csv
import io
import json

import requests
from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, session

from config import Config
from utils.csv_utils import parse_csv, sort_and_group_by_date
from utils.teamleader_utils import get_teamleader_token, get_teamleader_user, get_teamleader_teams, \
    get_teamleader_user_info, get_teamleader_user_times, refresh_teamleader_token, get_all_users

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY  # Setze einen geheimen Schlüssel für die Sitzungsverwaltung


def handle_token_refresh():
    username = session.get('username')
    try:
        refresh_teamleader_token(Config.CLIENT_ID, Config.CLIENT_SECRET, session.get('refresh_token'))
    except Exception as e:
        error_message = "Token ist abgelaufen. Melden Sie sich erneut an."
        return render_template('error.html', error_message=error_message, username=username)
    return None


def load_whitelist():
    with open('static/data/whitelist.json', 'r') as f:
        return json.load(f)


@app.route('/')
def home():
    user_id = session.get('userId')
    if user_id:
        whitelist = load_whitelist()
        user_permissions = next((user for user in whitelist if user['id'] == user_id), None)
        session['user_permissions'] = user_permissions

        if user_permissions:

            return render_template('index.html',
                                   username=user_permissions['name'],
                                   upload_times=user_permissions['upload_times'],
                                   manage_times=user_permissions['manage_times'],
                                   authorizations=user_permissions['authorizations'])

    return render_template('index.html')


@app.route('/authorizations.html')
def authorizations():
    error_redirect = handle_token_refresh()
    if error_redirect:
        return error_redirect

    username = session.get('username')
    access_token = session.get('access_token')

    user_permissions = session.get('user_permissions', {})
    if not user_permissions.get('authorizations', False):
        return render_template('error.html', username=username)

    user_list = get_all_users(access_token)

    return render_template('authorizations.html', username=username, user_list=user_list)


@app.route('/error.html')
def errror():
    username = session.get('username')
    return render_template('error.html', username=username)


@app.route('/upload-times.html')
def zeiten_hochladen():
    username = session.get('username')
    user_permissions = session.get('user_permissions', {})
    if not user_permissions.get('upload_times', False):
        return render_template('error.html', username=username)

    return render_template('upload-times.html', username=username)


@app.route('/manage-times.html')
def zeiten_verwalten():
    username = session.get('username')
    user_permissions = session.get('user_permissions', {})
    if not user_permissions.get('manage_times', False):
        return render_template('error.html', username=username)
    return render_template('manage-times.html', username=username)


@app.route('/manage-times.html', methods=['POST'])
def get_teams():
    error_redirect = handle_token_refresh()
    if error_redirect:
        return error_redirect

    username = session.get('username')
    access_token = session.get('access_token')
    request_data = request.get_json()
    selected_id = request_data.get('selectedId')
    first_tmstmp = request_data.get('first_tmstmp')
    second_tmstmp = request_data.get('second_tmstmp')
    third_tmstmp = request_data.get('third_tmstmp')
    end_tmstmp = request_data.get('end_tmstmp')
    fourth_tmstmp = request_data.get('fourth_tmstmp')

    response = get_teamleader_teams(access_token, selected_id)

    members_info = []

    for team in response:
        members = team.get('members', [])
        for member in members:
            member_id = member.get('id')
            first_name, last_name = get_teamleader_user_info(access_token, member_id)
            try:

                times_data = get_teamleader_user_times(access_token, member_id, first_tmstmp, second_tmstmp,
                                                       third_tmstmp, end_tmstmp, fourth_tmstmp)
                members_info.append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'total_duration': times_data["total_duration"],
                    'invoiceable_duration': times_data["invoiceable_duration"],
                    'non_invoiceable_duration': times_data["non_invoiceable_duration"],
                    'total_days': times_data["total_days"],
                    'invoiceable_percentage': times_data["invoiceable_percentage"],
                    'overtime_hours': times_data["overtime_hours"]
                })

            except Exception as e:
                error_message = f"Dir fehlen die Berechtigung, um dieses Team anzuschauen"
                return render_template('manage-times.html', error_message=error_message, username=username)

    session['members_info'] = members_info
    return render_template('manage-times.html', members_info=members_info, username=username)


@app.route('/download-template')
def download_template():
    return send_from_directory(directory='static/data', path='template.csv', as_attachment=True)


@app.route('/upload-times.html', methods=['GET', 'POST'])
def upload():
    username = session.get('username')

    if 'csvFile' not in request.files:
        return render_template('upload-times.html', error_message='Keine Datei ausgewählt!', username=username)

    file = request.files['csvFile']
    if file.filename == '':
        return render_template('upload-times.html', error_message='Keine Datei ausgewählt!', username=username)

    if file and file.filename.endswith('.csv'):
        csv_content = file.stream.read().decode('utf-8')
        csv_data = parse_csv(csv_content)

        if csv_data is None:
            return render_template('upload-times.html', error_message='Fehler beim Parsen der CSV-Datei!',
                                   username=username)

        sorted_data = sort_and_group_by_date(csv_data)
        session['csv_data_storage'] = sorted_data  # Speichern der Daten in der Sitzung
        return render_template('upload-times.html', sorted_data=sorted_data, username=username)

    return render_template('upload-times.html', error_message='Ungültiger Dateityp!', username=username)


@app.route('/authorize-teamleader')
def authorize_teamleader():
    session['previous_url'] = request.referrer or '/'
    auth_url = get_teamleader_token(Config.CLIENT_ID, Config.REDIRECT_URI)
    return redirect(auth_url)


@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get('code')
    try:
        token_response = get_teamleader_token(Config.CLIENT_ID, f'{Config.REDIRECT_URI}/oauth/callback',
                                              Config.CLIENT_SECRET, code)
        if 'access_token' in token_response:
            session['access_token'] = token_response['access_token']
            return redirect('/login')
        else:
            error_message = token_response.get('error_description', 'Autorisierungsfehler')
            return render_template('error.html', error_message=error_message)
    except requests.exceptions.RequestException as e:
        return render_template('error.html', error_message=str(e))


@app.route('/login')
def login():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(request.url)

    try:
        user_info = get_teamleader_user(access_token)
        session['username'] = f"{user_info['first_name']} {user_info['last_name']}"
        session['userId'] = user_info['id']
        return redirect(session.get('previous_url', '/'))
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})


@app.route('/upload-to-teamleader')
def fetch_teamleader_data():
    error_redirect = handle_token_refresh()
    if error_redirect:
        return error_redirect

    access_token = session.get('access_token')
    if not access_token:
        return redirect(session.get('previous_url', '/'))

    headers = {'Authorization': f'Bearer {access_token}'}
    body = json.dumps({
        "work_type_id": "26c1ee6e-0553-01b1-9455-753aa291e575",
        "started_at": "2024-06-26T10:00:00+02:00",
        "duration": 3600,
        "subject": {"type": "company", "id": "3adb83c6-3584-0a90-a564-a6b479e18040"},
        "invoiceable": True,
        "user_id": session.get('userId')
    })

    try:
        response = requests.post('https://api.focus.teamleader.eu/timeTracking.add', headers=headers, data=body)
        response.raise_for_status()
        if response.status_code == 201:
            success_message = "Die Zeiten wurden erfolgreich hochgeladen!"
            return render_template('upload-times.html', success_message=success_message)
        else:
            error_message = "Fehler beim Hochladen der Daten in Teamleader."
            return render_template('upload-times.html', error_message=error_message)
    except requests.exceptions.RequestException as e:
        return render_template('upload-times.html', error_message=str(e))


@app.route('/clear-data', methods=['POST'])
def clear_data():
    session.pop('csv_data_storage', None)  # Löschen der gespeicherten CSV-Daten aus der Sitzung
    return jsonify({'status': 'success', 'message': 'Daten erfolgreich gelöscht'})


@app.route('/download-csv')
def download_csv():
    # Rufe die Mitgliederinformationen ab
    members_info = session.get("members_info")

    # Erstelle einen IO-Stream für die CSV-Datei
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')  # Nutze ; als Trennzeichen

    # Schreibe die Kopfzeile in die CSV-Datei
    writer.writerow(
        ['Vorname', 'Nachname', 'Erfasste Zeit', 'Abrechenbar', 'Nicht Abrechenbar', 'Arbeitstage', 'Fakuraquote',
         'Überstunden'])

    # Schreibe die Mitgliederinformationen in die CSV-Datei
    for member in members_info:
        writer.writerow([
            member['first_name'],
            member['last_name'],
            member['total_duration'],
            member['invoiceable_duration'],
            member['non_invoiceable_duration'],
            member['total_days'],
            member['invoiceable_percentage'],
            member['overtime_hours']
        ])

    # Setze den Cursor des IO-Streams auf den Anfang
    output.seek(0)

    # Speichere die CSV-Datei temporär auf dem Server
    csv_filename = 'static/data/Zeitübersicht.csv'  # Beispiel: Temporärer Pfad

    # Schreibe den Inhalt in die CSV-Datei mit newline=''
    with open(csv_filename, 'w', newline='') as f:
        f.write(output.getvalue())

    # Sende die Datei als Download
    return send_from_directory(directory='static/data', path='Zeitübersicht.csv', as_attachment=True)

# Dummy setup for session for testing purposes
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'

if __name__ == '__main__':
    # For the purpose of testing the route
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
