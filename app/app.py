from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, session
import json
import requests
from config import Config
from utils.csv_utils import parse_csv, sort_and_group_by_date
from utils.teamleader_utils import get_teamleader_token, get_teamleader_user, get_teamleader_teams, \
    get_teamleader_user_info

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY  # Setze einen geheimen Schlüssel für die Sitzungsverwaltung


@app.route('/')
def home():
    username = session.get('username')
    return render_template('index.html', username=username)


@app.route('/error.html')
def errror():
    username = session.get('username')
    return render_template('error.html', username=username)


@app.route('/upload-times.html')
def zeiten_hochladen():
    username = session.get('username')
    return render_template('upload-times.html', username=username)


@app.route('/manage-times.html')
def zeiten_verwalten():
    username = session.get('username')
    return render_template('manage-times.html', username=username)


@app.route('/manage-times.html', methods=['POST'])
def get_teams():
    username = session.get('username')
    access_token = session.get('access_token')
    request_data = request.get_json()
    selected_id = request_data.get('selectedId')

    response = get_teamleader_teams(access_token, selected_id)

    members_info = []  # List to store member information

    for team in response:
        members = team.get('members', [])
        for member in members:
            member_id = member.get('id')
            first_name, last_name = get_teamleader_user_info(access_token, member_id)
            members_info.append({
                'first_name': first_name,
                'last_name': last_name
            })

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
    access_token = session.get('access_token')
    if not access_token:
        return redirect(session.get('previous_url', '/'))

    headers = {'Authorization': f'Bearer {access_token}'}
    body = json.dumps({
        "work_type_id": "26c1ee6e-0553-01b1-9455-753aa291e575",
        "started_at": "2024-06-18T10:00:00+02:00",
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


if __name__ == '__main__':
    app.run(debug=True)
