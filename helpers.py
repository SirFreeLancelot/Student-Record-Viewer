import streamlit as st
import gspread
import pandas as pd
from google.oauth2 import service_account

sheet_name = "Student Record Manager"

# Names must match worksheet names
batch_sessions = ["Practical", "AETCOM"]
cutoff = {"Theory": 75 ,"Practical": 80, "AETCOM": 75}

# Frames must match possible batch ranges
dataframes = ["D2:GU52", "D55:GU105", "D108:GU158", "D161:GU211", "D214:GU264"]
theory_frame = "D1:GU251"
scores_frame = "B2:Z253"
scores_columns = ['Aggregate','Theory Total','Theory IA','Theory FA','Theory 1','Theory 2','Theory 3',
                  'Viva 1','Viva 2','MCQ 1','MCQ 2','MCQ 3','Seminar','Th Professionalism',
                  'Practical Total','Practical IA','Practical FA','Practical 1','Practical 2','Practical 3',
                  'Record','Skill Certification','ECE','Assignment','Pr Professionalism']
theory_scores = ['Theory 1','Theory 2','Theory 3','Viva 1','Viva 2',
                 'MCQ 1','MCQ 2','MCQ 3','Seminar','Th Professionalism']
practical_scores = ['Practical 1','Practical 2','Practical 3','Record',
                    'Skill Certification','ECE','Assignment','Pr Professionalism']


# Cache google sheet credentials
@st.cache_resource
def load_google_sheets_credentials():
    google_sheets_credentials = st.secrets["google_sheets_credentials"]
    return google_sheets_credentials


# Cache gspread
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


# Convert dataframes to pandas dataframes with first row as column names
def df_with_header(data):
    df = pd.DataFrame(data=data[1:], columns=data[0])
    return df


# Load student data into session state variables
def load_student_data():
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
        scores_sheet = client.open(sheet_name).worksheet('Scores')
        scores_data = scores_sheet.get(scores_frame)
        st.session_state.scores = df_with_header(scores_data)
        return True
    except:
        return False
    

# Display eligibility criteria for attendance
def attendance_eligibility_criteria():
    with st.expander("Eligibility Criteria"):
        st.write(f''' 1. Theory Attendance must be at least {cutoff['Theory']}%. 
                    This includes only theory classes. ''')
        st.write(f''' 2. Practical Attendance must be at least {cutoff['Practical']}%. 
                    This includes lab sessions, SGDs, ECEs, Skill Certifications.
                    Each session is worth 2 hours, except ECE which is worth 3 hours. ''')
        st.write(f''' 3. AETCOM Attendance must be at least {cutoff['AETCOM']}%. 
                    This includes only AETCOM sessions, each worth 2 hours. ''')
        st.write(f''' Key: SGD - Small Group Discussions; ECE - Early Clinical Exposure; 
                      AETCOM - Attitude, Ethics and Communication. ''')
        

# Display eligibility criteria for scores
def scores_eligibility_criteria():
    with st.expander("Eligibility Criteria"):
        st.write(f''' 1. Theory Total must be at least 40%. 
                    This includes average of the three theory internal scores scaled to 80, 
                    and other formative scores scaled to 20. ''')
        st.write(f''' 2. Practical Total must be at least 40%. 
                    This includes average of the three practical internal scores scaled to 80,
                    and other formative scores scaled to 20. ''')
        st.write(f''' 3. Aggregate Score must be at least 50%. 
                    This is the average of the theory and practical scores. ''')
    with st.expander("Scoring Criteria"):
        st.write(f''' 1. Aggregate Score (max. 100) = (Theory Total + Practical Total) / 2 ''')
        st.write(f''' 2. Theory Total (max. 100) = Theory IA + Theory FA ''')
        st.write(f''' 3. Practical Total (max. 100) = Practical IA + Practical FA ''')
        st.write(f''' 4. Theory IA (max. 80) = (Theory 1 + Theory 2 + Theory 3) / 3 .
                         All three scores Theory 1, 2 and 3 are scaled to 80. ''')
        st.write(f''' 5. Practical IA (max. 80) = (Practical 1 + Practical 2 + Practical 3) / 3 .
                         All three scores Practical 1, 2 and 3 are scaled to 80. ''')
        st.write(f''' 6. Theory FA (max. 20) = (Viva 1 + Viva 2 + MCQ 1 + MCQ 2 + MCQ 3 + Seminar + Th Professionalism) 
                         scaled to 20.''')
        st.write(f''' 7. Practical FA (max. 20) = (Record + Skill Certification + ECE + Assignment + Pr Professionalism) 
                         scaled to 20.''')
        st.write(f''' Key: IA - Internal Assessment; FA - Formative Assessment; MCQ - Multiple Choice Questions''')


# Render theory attendance
def render_theory(roll_number):
    theory = st.session_state.theory
    date_columns = list(theory.columns)
    if date_columns[0] == 'E':
        st.write(f"Theory : No theory classes conducted yet")
        return
    att_str = ''
    abs_list = [f'(s.no. | dd-mm | time)']
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
            abs_list += [f'{total} | {date}']
        else:
            errors += 1
    
    if total == attended:
        abs_list = [' :green[No absences! Keep it up!] ']

    if total > 0:
        percentage = round(100 * attended / total,2)
        if percentage < cutoff['Theory']:
            eligibility = '🔴 :red[Not Eligible]'
            st.session_state.eligible = False
        else:
            eligibility = '🟢 :green[Eligible]'
        st.write(f"Theory : {attended} / {total} - ( {percentage} % ) ( {eligibility} )")
        st.write(att_str)
        with st.expander("Theory Absences"):
            for absence in abs_list:
                st.write(absence)            
    else:
        st.error('No records found for theory', icon="⚠️")
    
    if errors > 0:
        st.error(f'{errors} errors detected in theory records. Kindly notify the department office', icon="⚠️")


# Render Practical and AETCOM attendance
def render_attendance(roll_number):
    for batch in batch_sessions:        
        data = st.session_state[batch][(roll_number-1) // 50]
        date_columns = list(data.columns)
        if date_columns[0] == 'E':
            st.write(f"{batch} : No {batch} sessions conducted yet")
            continue
        att_str = ''
        abs_list = ['(s.no. | dd-mm | time)']
        if batch == 'Practical':
            abs_list = ['(s.no. | dd-mm | time | session)']
        total = 0
        attended = 0
        errors = 0
        
        for date in date_columns:
            if data[date][(roll_number-1) % 50] == 'P':
                total += 1
                attended += 1
                att_str += f'✅'
            elif data[date][(roll_number-1) % 50] == 'A':
                total += 1
                att_str += f'🆎'
                abs_list += [f'{total} | {date}']
            else:
                errors += 1

        if total == attended:
            abs_list = [' :green[No absences! Keep it up!] ']

        total = total * 2
        attended = attended * 2

        if batch == 'Practical':
            for date in date_columns:
                if date[-3:] == 'ECE':
                    if data[date][(roll_number-1) % 50] == 'P':
                        total += 1
                        attended += 1
                    elif data[date][(roll_number-1) % 50] == 'A':
                        total += 1
                    else:
                        errors += 1

        if total > 0:
            percentage = round(100 * attended / total,2)
            if percentage < cutoff[batch]:
                eligibility = '🔴 :red[Not Eligible]'
                st.session_state.eligible = False
            else:
                eligibility = '🟢 :green[Eligible]'
            st.write(f"{batch} : {attended} / {total} - ( {percentage} % ) ( {eligibility} )")
            st.write(att_str)
            with st.expander(f"{batch} Absences"):
                for absence in abs_list:
                    st.write(absence)
        else:
            st.warning(f'No records found for {batch}', icon="⚠️")

        if errors > 0:
            st.error(f'{errors} errors detected in {batch} records. Kindly notify the department office', icon="⚠️")


# Render scores
def render_scores(roll_number):
    scores = st.session_state.scores
    
    # Load formatted scores of student into dictionary
    student_scores = {}
    for column in scores_columns:
        student_scores[column] = f'{scores[column][roll_number-1]} / {scores[column][250]}'
    
    # Check eligibility
    if int(scores['Aggregate'][roll_number-1]) < 50:
        st.session_state.eligible = False
        aggregate_eligibility = '🔴 :red[Not Eligible]'
    else:
        aggregate_eligibility = '🟢 :green[Eligible]'
    if int(scores['Theory Total'][roll_number-1]) < 40:
        st.session_state.eligible = False
        theory_eligibility = '🔴 :red[Not Eligible]'
    else:
        theory_eligibility = '🟢 :green[Eligible]'
    if int(scores['Practical Total'][roll_number-1]) < 40:
        st.session_state.eligible = False
        practical_eligibility = '🔴 :red[Not Eligible]'
    else:
        practical_eligibility = '🟢 :green[Eligible]'

    # Show eligibility at the year end
    #st.write(f"1. Theory Total : {student_scores['Theory Total']} ( {theory_eligibility} )")
    #st.write(f"2. Practical Total : {student_scores['Practical Total']} ( {practical_eligibility} )")
    #st.write(f"3. Aggregate Score : {student_scores['Aggregate']} ( {aggregate_eligibility} )")

    # Display final scores
    with st.expander("Final Scores for Eligibility"):
        st.write("1. Theory Total : TBD")
        st.write("2. Practical Total : TBD")
        st.write("3. Aggregate Score : TBD")
    
    # Display theory scores
    with st.expander("Theory Scores"):
        for column in theory_scores:
            zeroes = scores[column].tolist().count('0')
            if zeroes == 250:
                st.write(f"{column} : TBD")
            else:
                st.write(f"{column} : {student_scores[column]}")
    
    # Display practical scores
    with st.expander("Practical Scores"):
        for column in practical_scores:
            zeroes = scores[column].tolist().count('0')
            if zeroes == 250:
                st.write(f"{column} : TBD")
            else:
                st.write(f"{column} : {student_scores[column]}")


# Render signatures
def signatures():
    sign1, sign2 = st.columns([2,1])

    with sign1:
        st.success(" Developed by Dr Suraj", icon="🌟")
    with sign2:
        st.info(" Version 1.4", icon="ℹ️")


# Render disclaimers
def disclaimers():
    st.write('''** Please note that these records are provided provisionally 
             for your reference, by the Department of Physiology. 
             All the records are for the subject of Physiology only. ''')

    st.write('''** The records are not guaranteed to be completely accurate.
             In case of any inconsistencies with our physical records, the physical records shall be considered final.
             If you notice any discrepancies, please notify the department office immediately.''')

    st.write('''** Eligibility criteria for appearing in the final examination 
             are based on the attendance and formative assessment scores. 
             You will be allowed to write the examination only after fulfilling the eligibility criteria.
             Not fulfilling the criteria will result in disqualification.''')


# Developer's Note
def developers_note():
    st.write('''** Developer's Note - Thank you for using my app! I hope you find it helpful. 
             I would really appreciate your valuable feedback. Anything you would like to tell me is welcome!
             Please reach out to me if you have any messages, suggestions, comments, queries or error reports. 
             You can write to me anonymously using this google form : https://forms.gle/yCE9FAEyyQ5iDEgR8 ''')

    st.write('''** - Dr Suraj, your friendly neighborhood Web Developer (not Spider-Man, unfortunately)''')

