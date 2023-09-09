import streamlit as st
import gspread
import pandas as pd
from google.oauth2 import service_account

sheet_name = "Student Record Manager"

# Names must match worksheet names
batch_sessions = ["Practical", "SGD"]

# Keys must match possible batch names
dataframes = ["D2:GU52", "D55:GU105", "D108:GU158", "D161:GU211", "D214:GU264"]
theory_frame = "D1:GU251"

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


def df_with_header(data):
    df = pd.DataFrame(data=data[1:], columns=data[0])
    return df


def load_attendance_data():
    try:
        client = authorize_client()
        theory_sheet = client.open(sheet_name).worksheet('Theory')
        theory_data = theory_sheet.get(theory_frame)
        st.session_state.theory = df_with_header(theory_data)
        for batch in batch_sessions:
            dataframes_sheet = client.open(sheet_name).worksheet(batch)
            dataframes_data = dataframes_sheet.batch_get(dataframes)
            st.session_state[batch] = []
            for data in dataframes_data:
                st.session_state[batch] += [df_with_header(data)]
        return True
    except:
        return False
    

def render_theory(roll_number):
    theory = st.session_state.theory
    att_str = ''
    abs_str = f'Absent on [ s.no. - (dd-mm | time) ] : '
    total = 0
    attended = 0
    errors = 0

    for date in list(theory.columns):
        if theory[date][roll_number-1] == 'P':
            total += 1
            attended += 1
            att_str += f'✅'
        elif theory[date][roll_number-1] == 'A':
            total += 1
            att_str += f'🆎'
            abs_str += f' [ {total} - ({date}) ] '
        else:
            errors += 1
    
    if total == attended:
        abs_str = 'No absences!'

    if total > 0:
        st.write(f"Theory : {attended} / {total} - ( {round(100 * attended / total,2)} % ) ( cutoff - 75 % )")
        st.text(att_str, help=f'{abs_str}')
    else:
        st.warning('No records found for theory', icon="⚠️")
    
    if errors > 0:
        st.error(f'{errors} errors detected in theory records. Kindly notify the department office', icon="⚠️")


def render_attendance(roll_number):
    for batch in batch_sessions:
        data = st.session_state[batch][(roll_number-1) // 50]
        att_str = ''
        abs_str = f'Absent on [ s.no. - (dd-mm | time) ] : '
        total = 0
        attended = 0
        errors = 0
        
        for date in list(data.columns):
            if data[date][(roll_number-1) % 50] == 'P':
                total += 1
                attended += 1
                att_str += f'✅'
            elif data[date][(roll_number-1) % 50] == 'A':
                total += 1
                att_str += f'🆎'
                abs_str += f' [ {total} - ({date}) ] '
            else:
                errors += 1

        if total == attended:
            abs_str = 'No absences!'

        if total > 0:
            st.write(f"{batch} : {attended} / {total} - ( {round(100 * attended / total,2)} % ) ( cutoff - 75 % )")
            st.text(att_str, help=f'{abs_str}')
        else:
            st.warning(f'No records found for {batch}', icon="⚠️")

        if errors > 0:
            st.error(f'{errors} errors detected in {batch} records. Kindly notify the department office', icon="⚠️")


def signatures():
    sign1, sign2 = st.columns([2,1])

    with sign1:
        st.success(" Developed by Dr Suraj", icon="🌟")
    with sign2:
        st.info(" Version 1.1", icon="ℹ️")


def disclaimers():
    st.write('''** Please note that these records are provided provisionally for your reference, by the Physiology department. 
            All the records are for the subject of Physiology only. ''')

    st.write('''** The records are not guaranteed to be completely accurate.
            In case of any inconsistencies with our physical records, the physical records shall be considered final.
            If you notice any discrepancies, please notify the department office immediately.''')

    st.write('''** Eligibility criteria for appearing in the final examination 
            is based on the attendance and formative assessment scores. Not fulfilling the criteria will result in disqualification.''')
    
    st.write('''** Version 1.1 displays only Attendance records for Theory, Practical and SGD sessions.
            Support for other sessions and formative assessment scores will be added soon. ''')
    
    st.write('''** Developer's Note - Thank you for using my app! I hope you find it helpful. 
             I would really appreciate your valuable feedback. 
             Please reach out to me if you have any suggestions, queries or error reports. ''')

    st.write('''** - Your friendly neighborhood Web Developer, Dr Suraj (not Spider-man, unfortunately)''')

