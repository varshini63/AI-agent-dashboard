import os
import pandas as pd
from flask import Flask, request, render_template, send_file, session, jsonify
from googleapiclient.discovery import build
from google.auth.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from serpapi import GoogleSearch
import google.generativeai as genai  # Gemini API SDK
import csv
import json
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session to work

# API usage limit settings
API_LIMIT = 5
USAGE_FILE = "api_usage.json"

# Initialize or load API usage data
if not os.path.exists(USAGE_FILE):
    with open(USAGE_FILE, 'w') as file:
        json.dump({"date": str(datetime.now().date()), "count": 0}, file)


def check_api_limit():
    """Check if the API call limit has been reached."""
    with open(USAGE_FILE, 'r') as file:
        data = json.load(file)
    today = str(datetime.now().date())
    if data["date"] != today:
        # Reset count for a new day
        data = {"date": today, "count": 0}
    if data["count"] >= API_LIMIT:
        return False  # Limit reached
    return True


def increment_api_count():
    """Increment the API call count."""
    with open(USAGE_FILE, 'r') as file:
        data = json.load(file)
    data["count"] += 1
    with open(USAGE_FILE, 'w') as file:
        json.dump(data, file)


# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def get_google_sheets_data(spreadsheet_id):
    """Fetch data from a Google Sheet."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range="Sheet1").execute()
    values = result.get('values', [])
    return values


def get_search_results(query):
    """Search the web using SerpAPI."""
    if not check_api_limit():
        return {"error": "API call limit reached for today."}

    params = {
        "q": query,
        "api_key": "6a5e62df8d9824eae6ab1495fb09527312acead2fd00f7ff8125ca37b7ab6d4d"  # Replace with your SerpAPI key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    increment_api_count()
    return results


def extract_info_with_gemini(query, results):
    """Use Gemini API to extract information from search results."""
    if not check_api_limit():
        return "API call limit reached for today."
    
    # Configure Gemini API
    genai.configure(api_key="AIzaSyAB4NRiWZLvfZoER2_eBeDsZvjynMe6enk")  # Replace with your Gemini API key
    
    # Define the prompt for generation
    prompt = f"{query} : {results}"
    
    try:
        # Use the Gemini API to generate content
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        increment_api_count()
        return response.text if hasattr(response, 'text') else "No response from Gemini API."
    except Exception as e:
        return f"Error using Gemini API: {str(e)}"


@app.route("/", methods=["GET", "POST"])
def upload_file():
    """Handles file upload and preview."""
    if request.method == "POST":
        file = request.files.get('file')
        if file:
            try:
                df = pd.read_csv(file)
                session['data_columns'] = df.columns.tolist()
                session['data_preview'] = df.to_html()
                return render_template("index.html", data=session['data_preview'])
            except Exception as e:
                return render_template("index.html", data=None, error=f"Error reading file: {str(e)}")
    return render_template("index.html", data=None)


@app.route("/query", methods=["POST"])
def process_query():
    """Processes the dynamic query."""
    query = request.form.get('query')
    entity_column = request.form.get('entity_column')

    if not entity_column:
        return render_template("query_result.html", error="Entity column is required.")

    search_results = get_search_results(query)
    if "error" in search_results:
        return render_template("query_result.html", error=search_results["error"])
    
    extracted_info = extract_info_with_gemini(query, search_results)
    if extracted_info == "API call limit reached for today.":
        return render_template("query_result.html", error=extracted_info)
    
    session['query'] = query
    session['search_results'] = search_results
    session['extracted_info'] = extracted_info
    return render_template("query_result.html", query=query, entity_column=entity_column, extracted_info=extracted_info)


@app.route("/result", methods=["POST"])
def display_results():
    """Displays final results."""
    extracted_info = session.get('extracted_info', "No extracted information available.")
    return render_template("result.html", data=extracted_info)


@app.route("/download", methods=["GET"])
def download():
    """Downloads results as CSV."""
    extracted_info = session.get('extracted_info', "No extracted information available.")
    filename = "results.csv"
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Extracted Information"])
        writer.writerow([extracted_info])
    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
