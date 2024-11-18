# AI-agent-dashboard

This is a Flask-based web application designed to interact with a CSV file, process queries, extract information using web search and Gemini API, and display the results. The user can upload CSV files, input queries, and view the results or download them as CSV files.

## Features
1. **File Upload**: Users can upload a CSV file which will be processed and previewed.
2. **Dynamic Query Input**: Users can input a query and select an entity column to retrieve relevant data.
3. **Google Search**: The application uses SerpAPI to fetch search results based on the user's query.
4. **Gemini API**: The application uses the Gemini API (powered by Google) to process the search results and extract useful information.
5. **Results Display**: The application displays the extracted information on a separate page.

## Prerequisites
1. **Python 3.x** (preferably Python 3.7 or later)
2. **Flask**: Python web framework for building the application.
3. **Pandas**: For handling CSV data.
4. **SerpAPI**: For web search integration.
5. **Google Gemini API**: For content extraction.

## Installation
Install required dependencies:
pip install -r requirements.txt

You need to replace the placeholders for SerpAPI and Gemini API keys in app.py:
SerpAPI API key
Gemini API key

then run the application as:
python app.py
