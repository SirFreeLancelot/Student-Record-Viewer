import streamlit as st
import gspread
import pandas as pd
import hashlib
from gspread_dataframe import set_with_dataframe
from google.oauth2 import service_account

sheet_name = "Student Record Manager"

# Names must match worksheet names
session_types = ["Theory", "Practical", "SGD", "Seminar", "ECE", "AETCOM", "Skill Cert"]

class_slots = ["9-10", "10-11", "11-12", "11-1", "2-4", "12-1"]

batches = {"All": {"start": 1, "end": 250, 'row': 1} ,"A": {"start": 1, "end": 50, 'row': 2}, 
           "B": {"start": 51, "end": 100, 'row': 55}, "C": {"start": 101, "end": 150, 'row': 108}, 
           "D": {"start": 151, "end": 200, 'row': 161}, "E": {"start": 201, "end": 250, 'row': 214}}

# Keys must match possible batch names
dataframes = {"All": "D1:GU251", "A": "D2:GU52", "B": "D55:GU105", "C": "D108:GU158", "D": "D161:GU211", "E": "D214:GU264"}


@st.cache_resource
def load_google_sheets_credentials():
    google_sheets_credentials = st.secrets["google_sheets_credentials"]
    return google_sheets_credentials


@st.cache_resource
def authorize_client():
    google_sheets_credentials = load_google_sheets_credentials()
    scopes = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    credentials = service_account.Credentials.from_service_account_info(
        google_sheets_credentials,
        scopes=scopes
    )
    return gspread.authorize(credentials)


def load_attendance_data(session_type, batch):
    client = authorize_client()
    gsheet = client.open(sheet_name).worksheet(session_type)
    return gsheet.get(dataframes[batch])


def save_attendance_data(session_type, batch, data):
    client = authorize_client()
    gsheet = client.open(sheet_name).worksheet(session_type)
    set_with_dataframe(gsheet, data, batches[batch]['row'], 4)


def df_with_header(data):
    df = pd.DataFrame(data=data[1:], columns=data[0])
    return df


def df_to_hash(data):
    data_str = data.to_string(index=False)
    data_hash = hashlib.sha256(data_str.encode()).hexdigest()
    return data_hash


def mark_attendance(roll_num, start, end, attendance):
    attendance_list = st.session_state.attendance_list
    attendance_list[(roll_num-1)%(end-start+1)] = attendance

