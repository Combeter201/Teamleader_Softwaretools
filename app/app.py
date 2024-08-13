import csv
import io
import json
import locale
import os
import tempfile
import time
from datetime import date, datetime, timedelta

import requests
from config import Config
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
)
from utils.csv_utils import parse_csv, group_by_date
from utils.date_utils import calculate_total_hours
from utils.teamleader_utils import (
    get_all_users,
    get_number_of_absence_days,
    get_teamleader_teams,
    get_teamleader_token,
    get_teamleader_user,
    get_teamleader_user_info,
    get_teamleader_user_times,
    get_user_absence,
    refresh_teamleader_token, get_contact_info,
)

app = Flask(__name__)
app.secret_key = (
    Config.SECRET_KEY
)  # Setze einen geheimen Schlüssel für die Sitzungsverwaltung
locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")


def handle_token_refresh():
    username = session.get("username")
    initials = session.get("initials")
    try:
        refresh_teamleader_token(
            Config.CLIENT_ID, Config.CLIENT_SECRET, session.get("refresh_token")
        )
    except Exception as e:
        error_message = "Token ist abgelaufen. Melden Sie sich erneut an."
        return render_template(
            "error.html",
            error_message=error_message,
            username=username,
            initials=initials,
        )
    return None


def load_whitelist():
    with open("static/data/whitelist.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_worktype():
    with open("static/data/worktype.json", "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def home():
    user_id = session.get("userId")

    if user_id:
        username = session.get("username")
        initials = session.get("initials")
        whitelist = load_whitelist()
        user_permissions = next(
            (user for user in whitelist if user["id"] == user_id), None
        )
        session["user_permissions"] = user_permissions

        if user_permissions:
            return render_template(
                "index.html",
                username=user_permissions["name"],
                upload_times=user_permissions["upload_times"],
                manage_times=user_permissions["manage_times"],
                absence=user_permissions["absence"],
                birthday=user_permissions["birthday"],
                authorizations=user_permissions["authorizations"],
                initials=initials,
            )

    return render_template("index.html")


@app.route("/authorizations.html")
def authorizations():
    error_redirect = handle_token_refresh()
    if error_redirect:
        return error_redirect

    username = session.get("username")
    initials = session.get("initials")
    access_token = session.get("access_token")

    user_permissions = session.get("user_permissions", {})
    if not user_permissions.get("authorizations", False):
        return render_template("error.html", username=username, initials=initials)

    user_list = get_all_users(access_token)

    return render_template(
        "authorizations.html", username=username, initials=initials, user_list=user_list
    )


@app.route("/error.html")
def error():
    username = session.get("username")
    initials = session.get("initials")
    return render_template("error.html", username=username, initials=initials)


@app.route("/birthday.html")
def birthday():
    username = session.get("username")
    initials = session.get("initials")
    access_token = session.get("access_token")
    date = datetime.today().date().strftime("%d.%m.%Y")
    user_permissions = session.get("user_permissions", {})
    members = get_contact_info(access_token)

    if not user_permissions.get("birthday", False):
        return render_template("error.html", username=username, initials=initials)
    return render_template(
        "birthday.html",
        username=username,
        initials=initials,
        date=date,
        members=members,
    )

@app.route("/absence.html", methods=["POST", "GET"])
def absence():
    error_redirect = handle_token_refresh()
    if error_redirect:
        return error_redirect

    access_token = session.get("access_token")
    username = session.get("username")
    initials = session.get("initials")
    userId = session.get("userId")
    outputType = "date"
    week_dates = []
    selected_date = ""

    holidays = set([
        "Neujahr", "Heilige Drei Könige", "Karfreitag", "Ostermontag",
        "Tag der Arbeit", "Christi Himmelfahrt", "Pfingstmontag",
        "Fronleichnam", "Mariä Himmelfahrt", "Tag der Deutschen Einheit",
        "Allerheiligen", "1. Weihnachtstag", "2. Weihnachtstag"
    ])

    try:
        request_data = request.get_json()
        inputType = request_data.get("inputType")
        outputType = inputType
        date_param = request_data.get("date")

        if inputType == "date":
            date_requested = datetime.strptime(date_param, "%Y-%m-%d").date()
            startDate = date_requested - timedelta(days=1)
            endDate = date_requested + timedelta(days=1)

            week_dates.clear()
            day = startDate + timedelta(days=1)
            formatted_day = day.strftime("%d.%m.%Y")
            week_dates.append(formatted_day)

        elif inputType == "week":
            selected_date = date_param
            year, week = date_param.split("-W")
            date_requested = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w").date()
            startDate = date_requested - timedelta(days=date_requested.weekday())
            endDate = startDate + timedelta(days=5)

            week_dates.clear()
            for i in range(5):  # Montag bis Freitag
                day = startDate + timedelta(days=i)
                formatted_day = day.strftime("%d.%m.%Y")
                week_dates.append(formatted_day)

        else:
            raise ValueError("Invalid inputType")

    except Exception as e:
        date_requested = datetime.today().date()
        week_dates.clear()
        week_dates.append(date_requested.strftime("%d.%m.%Y"))
        startDate = date_requested - timedelta(days=1)
        endDate = date_requested + timedelta(days=1)

    # Loading whitelist data from whitelist.json
    with open("static/data/whitelist.json", "r", encoding="utf-8") as f:
        whitelist = json.load(f)

    # Searching whitelist for userId and determining team_id
    team_id = None
    team_id2 = None
    team_id3 = None
    for user_info in whitelist:
        if user_info["id"] == userId:
            team_id = user_info["team_id"]
            if userId == "ef0efb7d-1c27-0226-a158-66dd19366408":
                team_id2 = "f49c6b93-b930-044d-be5d-2e9a7a22bfad"
                team_id3 = "0ed1261b-cde1-07af-ba56-315561d3082d"
            break

    if not team_id:
        return "Unauthorized", 401

    if team_id2 is not None and team_id3 is not None:
        response = get_teamleader_teams(access_token, team_id, team_id2, team_id3)
    else:
        # Calling function to retrieve team leader's teams
        response = get_teamleader_teams(access_token, team_id)

    try:
        ids = [member["id"] for team in response for member in team["members"]]
    except Exception as e:
        error_message = (
            f"Dein Token ist abgelaufen, melde dich erneut an um den Token zu erneuern"
        )
        return render_template(
            "absence.html",
            error_message=error_message,
            username=username,
            initials=initials,
            holidays=holidays
        )

    # Prepare list for absences
    absences_list = []

    # Fetch absences for authorized users based on whitelist
    for user_info in whitelist:
        if user_info["id"] in ids:
            # Finding user's name
            for team in response:
                for member in team["members"]:
                    if member["id"] == user_info["id"]:
                        name = user_info["name"]
                        break
                else:
                    continue
                break
            else:
                name = "Unknown"

            if outputType == "date":
                absence_info = get_user_absence(
                    access_token, user_info["id"], startDate, endDate
                )
                absences_list.append(
                    {
                        "name": name,
                        "absence": absence_info,  # Assuming get_user_absence returns absence information
                    }
                )
            elif outputType == "week":
                absence_info = get_user_absence(
                    access_token,
                    user_info["id"],
                    startDate - timedelta(days=1),
                    endDate,
                    True,
                    week_dates,
                )
                # Check if the user is already in the absences_list
                user_found = False
                for entry in absences_list:
                    if entry["name"] == name:
                        entry["absence"] = absence_info
                        user_found = True
                        break
                if not user_found:
                    absences_list.append(
                        {
                            "name": name,
                            "absence": absence_info,  # Start a new list with the first absence info
                        }
                    )

    if outputType == "date":
        selected_date = date_requested.strftime("%Y-%m-%d")

    day_of_week = date_requested.strftime("%A")

    # Rendering the 'absence.html' template and passing data
    return render_template(
        "absence.html",
        username=username,
        initials=initials,
        absences=absences_list,
        today=selected_date,
        view=outputType,
        day=day_of_week,
        date=week_dates,
        holidays=holidays
    )



@app.route("/upload-times.html")
def zeiten_hochladen():
    username = session.get("username")
    initials = session.get("initials")
    user_permissions = session.get("user_permissions", {})
    if not user_permissions.get("upload_times", False):
        return render_template("error.html", username=username, initials=initials)

    return render_template("upload-times.html", username=username, initials=initials)


@app.route("/manage-times.html")
def zeiten_verwalten():
    username = session.get("username")
    userId = session.get("userId")
    initials = session.get("initials")
    user_permissions = session.get("user_permissions", {})
    selectedMonth = datetime.today().strftime("%Y-%m")

    if not user_permissions.get("manage_times", False):
        return render_template("error.html", username=username, initials=initials)
    return render_template("manage-times.html", username=username, initials=initials, team_id="",
                           selectedMonth=selectedMonth)


@app.route("/manage-times.html", methods=["POST"])
def get_teams():
    error_redirect = handle_token_refresh()
    if error_redirect:
        return error_redirect

    username = session.get("username")
    initials = session.get("initials")
    access_token = session.get("access_token")
    request_data = request.get_json()
    selectedMonth = request_data.get("selectedMonth")

    # Umwandlung in ein Datum (wir nehmen den ersten Tag des Monats)
    selected_date = datetime.strptime(selectedMonth + "-01", "%Y-%m-%d")

    # Berechnung des ersten und letzten Tags des Monats
    beginofMonth = (selected_date - timedelta(days=1)).strftime("%Y-%m-%d")
    # Finde den letzten Tag des Monats durch den ersten Tag des nächsten Monats
    next_month = selected_date.replace(day=28) + timedelta(
        days=4
    )  # Gehe einen Monat weiter
    endofMonth = (
            (next_month - timedelta(days=next_month.day)) + timedelta(days=1)
    ).strftime("%Y-%m-%d")
    selected_id = request_data.get("selectedId")
    selectedOption = request_data.get("selectedOption")
    team_name = request_data.get("team_name")
    first_tmstmp = request_data.get("first_tmstmp")
    second_tmstmp = request_data.get("second_tmstmp")
    third_tmstmp = request_data.get("third_tmstmp")
    end_tmstmp = request_data.get("end_tmstmp")
    fourth_tmstmp = request_data.get("fourth_tmstmp")

    # Initialisiere die Zählvariable für Arbeitstage
    workdays_count = 0

    # Schleife durch alle Tage des Monats und zähle die Arbeitstage
    current_day = selected_date
    while current_day <= (
            datetime.strptime(endofMonth, "%Y-%m-%d") - timedelta(days=1)
    ):
        # Prüfe, ob der aktuelle Tag ein Arbeitstag ist (Montag bis Freitag)
        if current_day.weekday() < 5:  # Montag (0) bis Freitag (4)
            workdays_count += 1
        # Gehe zum nächsten Tag
        current_day += timedelta(days=1)

    response = get_teamleader_teams(access_token, selected_id)

    members_info = []

    for team in response:
        members = team.get("members", [])
        for member in members:
            member_id = member.get("id")
            first_name, last_name = get_teamleader_user_info(access_token, member_id)

            try:
                days_of_absence = get_number_of_absence_days(
                    access_token, member_id, beginofMonth, endofMonth
                )

                times_data = get_teamleader_user_times(
                    access_token,
                    member_id,
                    first_tmstmp,
                    second_tmstmp,
                    third_tmstmp,
                    end_tmstmp,
                    fourth_tmstmp,
                )

                members_info.append(
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                        "total_duration": times_data["total_duration"].replace(".", ","),
                        "invoiceable_duration": times_data["invoiceable_duration"].replace(".", ","),
                        "non_invoiceable_duration": times_data["non_invoiceable_duration"].replace(".", ","),
                        "total_days": workdays_count - days_of_absence,
                        "invoiceable_percentage": "{:.2f}".format(
                            float(times_data["invoiceable_duration"].replace(",", "."))
                            / ((workdays_count - days_of_absence) * 8)
                        ).replace(".", ","),
                        "overtime_hours": "{:.2f}".format(
                            float(times_data["total_duration"].replace(",", "."))
                            - (workdays_count - days_of_absence) * 8
                        ).replace(".", ","),
                    }
                )

            except Exception as e:
                error_message = (
                    f"Dir fehlen die Berechtigung, um dieses Team anzuschauen"
                )
                return render_template(
                    "manage-times.html",
                    error_message=error_message,
                    username=username,
                    initials=initials,
                    selectedMonth=selectedMonth,
                    team_id=selected_id,
                    selectedOption=selectedOption,
                    team_name=team_name
                )

    session["members_info"] = members_info
    return render_template(
        "manage-times.html",
        members_info=members_info,
        username=username,
        initials=initials,
        selectedMonth=selectedMonth,
        team_id=selected_id,
        selectedOption=selectedOption,
        team_name=team_name
    )


@app.route("/download-template")
def download_template():
    return send_from_directory(
        directory="static/data", path="template.csv", as_attachment=True
    )


@app.route("/upload-times.html", methods=["GET", "POST"])
def upload():
    temp_dir = tempfile.gettempdir()
    username = session.get("username")
    initials = session.get("initials")

    if "csvFile" not in request.files:
        return render_template(
            "upload-times.html",
            error_message="Keine Datei ausgewählt!",
            username=username,
            initials=initials,
        )

    file = request.files["csvFile"]
    if file.filename == "":
        return render_template(
            "upload-times.html",
            error_message="Keine Datei ausgewählt!",
            username=username,
            initials=initials,
        )

    if file and file.filename.endswith(".csv"):
        try:
            csv_content = file.stream.read().decode("utf-8")
        except UnicodeDecodeError:
            return render_template(
                "upload-times.html",
                error_message="Fehlerhafte Exceldatei!",
                username=username,
                initials=initials,
            )
        csv_data = parse_csv(csv_content)
        temp_csv_path = os.path.join(temp_dir, "temp_upload.csv")
        if csv_data is None:
            return render_template(
                "upload-times.html",
                error_message="Fehler beim Parsen der CSV-Datei!",
                username=username,
                initials=initials,
            )

        try:
            with open(temp_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(
                    list(csv_data[0].keys())
                )  # Schreibe die Kopfzeile in die CSV-Datei
                for row in csv_data:
                    writer.writerow(
                        list(row.values())
                    )  # Schreibe die Datenzeilen in die CSV-Datei
        except Exception as e:
            return render_template(
                "upload-times.html",
                error_message="Ungültiger Dateityp!",
                username=username,
                initials=initials,
            )

        sorted_data = group_by_date(csv_data)
        return render_template(
            "upload-times.html",
            sorted_data=sorted_data,
            username=username,
            initials=initials,
        )

    return render_template(
        "upload-times.html",
        error_message="Ungültiger Dateityp!",
        username=username,
        initials=initials,
    )


@app.route("/authorize-teamleader")
def authorize_teamleader():
    session["previous_url"] = request.referrer or "/"
    auth_url = get_teamleader_token(Config.CLIENT_ID, Config.REDIRECT_URI)
    return redirect(auth_url)


@app.route("/logout")
def logout_teamleader():
    session.clear()
    time.sleep(1)
    return redirect("/")


@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    try:
        token_response = get_teamleader_token(
            Config.CLIENT_ID,
            f"{Config.REDIRECT_URI}/oauth/callback",
            Config.CLIENT_SECRET,
            code,
        )
        if "access_token" in token_response:
            session["access_token"] = token_response["access_token"]
            return redirect("/login")
        else:
            error_message = token_response.get(
                "error_description", "Autorisierungsfehler"
            )
            return render_template("error.html", error_message=error_message)
    except requests.exceptions.RequestException as e:
        return render_template("error.html", error_message=str(e))


@app.route("/login")
def login():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(request.url)

    try:
        user_info = get_teamleader_user(access_token)
        session["username"] = f"{user_info['first_name']} {user_info['last_name']}"
        session["initials"] = f"{user_info['first_name'][0]}{user_info['last_name'][0]}"
        session["userId"] = user_info["id"]
        return redirect(session.get("previous_url", "/"))
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)})


@app.route("/upload-to-teamleader")
def fetch_teamleader_data():
    username = session.get("username")
    initials = session.get("initials")
    temp_dir = tempfile.gettempdir()
    temp_csv_path = os.path.join(temp_dir, "temp_upload.csv")
    # Lade Daten aus der temporären CSV-Datei
    with open(temp_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        csv_data = list(reader)

    error_redirect = handle_token_refresh()
    if error_redirect:
        return error_redirect

    access_token = session.get("access_token")
    if not access_token:
        return redirect(session.get("previous_url", "/"))

    headers = {"Authorization": f"Bearer {access_token}"}

    for entry in csv_data:
        datum = entry["Datum"]
        von = entry["Von"]
        bis = entry["Bis"]
        abrechenbar = entry["Abrechenbar"] == "Ja"
        description = entry["Beschreibung"]

        # Datum und Zeit in das gewünschte Format konvertieren
        date_time_str = f"{datum} {von}"
        started_at = (
                datetime.strptime(date_time_str, "%d.%m.%Y %H:%M").isoformat() + "+02:00"
        )

        # Dauer berechnen
        duration_seconds = calculate_total_hours(von, bis) * 3600

        worktype = load_worktype()
        worktype_id = next(
            (wktype for wktype in worktype if wktype["type"] == entry["Typ"]), None
        )

        body = {
            "work_type_id": worktype_id["id"],
            "started_at": started_at,
            "duration": duration_seconds,
            "description": description,
            "subject": worktype_id["subject"],
            "invoiceable": abrechenbar,
            "user_id": session.get("userId"),
        }

        try:
            response = requests.post(
                "https://api.focus.teamleader.eu/timeTracking.add",
                headers=headers,
                data=json.dumps(body),
            )
            response.raise_for_status()
            if response.status_code != 201:
                error_message = "Fehler beim Hochladen der Daten in Teamleader."
                return render_template(
                    "upload-times.html",
                    error_message=error_message,
                    username=username,
                    initials=initials,
                )
        except requests.exceptions.RequestException as e:
            return render_template(
                "upload-times.html",
                error_message=str(e),
                username=username,
                initials=initials,
            )

    success_message = "Die Zeiten wurden erfolgreich hochgeladen!"
    return render_template(
        "upload-times.html",
        success_message=success_message,
        username=username,
        initials=initials,
    )


@app.route("/clear-data", methods=["POST"])
def clear_data():
    temp_dir = tempfile.gettempdir()
    # Routenfunktion zum Löschen der temporären CSV-Daten
    temp_csv_path = os.path.join(temp_dir, "temp_upload.csv")
    if os.path.exists(temp_csv_path):
        os.remove(temp_csv_path)

    return jsonify({"status": "success", "message": "Daten erfolgreich gelöscht"})


@app.route("/download-csv")
def download_csv():
    # Rufe die Mitgliederinformationen ab
    members_info = session.get("members_info")

    # Erstelle einen IO-Stream für die CSV-Datei
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")  # Nutze ; als Trennzeichen

    # Schreibe die Kopfzeile in die CSV-Datei
    writer.writerow(
        [
            "Vorname",
            "Nachname",
            "Erfasste Zeit",
            "Abrechenbar",
            "Nicht Abrechenbar",
            "Arbeitstage",
            "Fakuraquote",
            "Überstunden",
        ]
    )

    # Schreibe die Mitgliederinformationen in die CSV-Datei
    for member in members_info:
        writer.writerow(
            [
                member["first_name"],
                member["last_name"],
                member["total_duration"],
                member["invoiceable_duration"],
                member["non_invoiceable_duration"],
                member["total_days"],
                member["invoiceable_percentage"],
                member["overtime_hours"],
            ]
        )

    # Setze den Cursor des IO-Streams auf den Anfang
    output.seek(0)

    # Speichere die CSV-Datei temporär auf dem Server
    csv_filename = "static/data/Zeitübersicht.csv"  # Beispiel: Temporärer Pfad

    # Schreibe den Inhalt in die CSV-Datei mit newline=''
    with open(csv_filename, "w", newline="", encoding='utf-8') as f:
        f.write('\ufeff')
        f.write(output.getvalue())

    # Sende die Datei als Download
    return send_from_directory(
        directory="static/data", path="Zeitübersicht.csv", as_attachment=True, mimetype="text/csv; charset=utf-8"
    )



@app.route("/save_changes", methods=["POST"])
def save_changes():
    changes = request.get_json()
    try:
        with open("static/data/whitelist.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        for user in data:
            employee = user["name"]
            if employee in changes:
                for permission, value in changes[employee].items():
                    if permission in user:
                        user[permission] = value

        with open("static/data/whitelist.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# Dummy setup for session for testing purposes
app.secret_key = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"

if __name__ == "__main__":
    app.run(debug=True)
