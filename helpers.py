import streamlit as st
import gspread
import pandas as pd
from google.oauth2 import service_account
import random
import re
import google.generativeai as genai
from streamlit_card import card
import base64

sheet_name = st.secrets['sheet_name']

# Names must match worksheet names
batch_sessions = ["Practical", "AETCOM"]
cutoff = {"Theory": 75 ,"Practical": 80, "AETCOM": 75}

# Frames must match possible batch ranges
dataframes = ["D2:GU52", "D55:GU105", "D108:GU158", "D161:GU211", "D214:GU264"]
name_frame = "B1:D251"
house_frames = ["A1:F6", "A11:M261", "A266:H316", "J266:Q316", "S266:Z316", "AB266:AI316", "AK266:AR316"]
theory_frame = "D1:GU251"
scores_frames = ["B2:AC253", "B255"]
scores_columns = ['Aggregate','Theory Total','Theory IA','Theory FA','Theory 1','Theory 2','Theory 3',
                  'Viva 1','Viva 2','MCQ 1','MCQ 2','MCQ 3','Seminar','Th Professionalism',
                  'Practical Total','Practical IA','Practical FA','Practical 1','Practical 2','Practical 3',
                  'Class Test 1', 'Class Test 2', 'Class Test 3',
                  'Record','Skill Certification','ECE','Assignment','Pr Professionalism']
theory_scores = ['Theory 1','Theory 2','Theory 3','Viva 1','Viva 2',
                 'MCQ 1','MCQ 2','MCQ 3','Seminar','Th Professionalism']
practical_scores = ['Practical 1','Practical 2','Practical 3',
                    'Class Test 1', 'Class Test 2', 'Class Test 3',
                    'Record', 'Skill Certification','ECE','Assignment','Pr Professionalism']

# List of houses
houses_list = ['Blackburn', 'Adelbert', 'Langendorff', 'Landsteiner', 'Sherrington']
global_leaderboard_columns = ['Roll No.', 'Attnd (%)', 'Att Rank', 'Tot Score', 'Score Rank']
house_leaderboard_columns = ['Roll No.', 'Attnd (%)', 'Att Rnk Glb', 'Att Rnk Hs', 
                             'Tot Scr', 'Scr Rnk Glb', 'Scr Rnk Hs']

# Scientists and their wikipedia pages 
scientists = {
    "Elizabeth Blackburn": "https://en.wikipedia.org/wiki/Elizabeth_Blackburn",
    "Adelbert Ames Jr.": "https://en.wikipedia.org/wiki/Adelbert_Ames_Jr.",
    "Oskar Langendorff": "https://en.wikipedia.org/wiki/Oskar_Langendorff",
    "Karl Landsteiner": "https://en.wikipedia.org/wiki/Karl_Landsteiner",
    "Charles Scott Sherrington": "https://en.wikipedia.org/wiki/Charles_Scott_Sherrington"
}

# AI response word limit
word_limits = {'long': '300 to 400', 'medium': '200 to 300', 'short': '100 to 200' }

medals = {'1': '🏅🥇🥇🥇🏅', '2': '🏅🥈🥈🏅', '3': '🏅🥉🏅', '4': '🏅🏅', '5': '🏅'}

# Cache google sheet credentials
@st.cache_resource
def load_google_sheets_credentials(account):
    google_sheets_credentials = st.secrets[account]
    return google_sheets_credentials


# Cache gspread
@st.cache_resource
def authorize_client(account):
    google_sheets_credentials = load_google_sheets_credentials(account)
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


# Load student data into session state variables. Log operations into status
def load_student_data():
    # Reader accounts - make sure read access is granted
    accounts = ['Reader_1', 'Reader_2', 'Reader_3', 'Reader_4', 
                'Reader_5', 'Reader_6', 'Reader_7', 'Reader_8', 'Reader_9', 
                'Reader_10', 'Reader_11', 'Reader_12', 'Reader_13', 'Reader_14', 
                'Reader_15', 'Reader_16', 'Reader_17', 'Reader_18', 'Reader_19']
    number_of_accounts = len(accounts)
    shuffles = random.randint(2, 10)
    for i in range(shuffles):
        random.shuffle(accounts)
    i = 1
    fetched = 0
    with st.status(f":blue[Fetched {fetched} / 6 records. Trying Reader {i} / {number_of_accounts}]", expanded=False) as status:
        while i <= number_of_accounts and st.session_state.data_pulled == False:
            account = accounts[i-1]
            try:
                st.write(f':blue[Authorizing {account}]')
                client = authorize_client(account)
                st.write(f'Trying to fetch records using {account}')
                if 'houses' not in st.session_state:
                    house_sheet = client.open(sheet_name).worksheet('Houses')
                    st.write("Leaderboard worksheet found")
                    house_data = house_sheet.batch_get(house_frames)
                    st.write("Leaderboard data downloaded")
                    leaderboard_dataframes = []
                    for data in house_data:
                        leaderboard_dataframes.append(df_with_header(data))
                    st.write("Leaderboard data formatted")
                    st.session_state.houses = leaderboard_dataframes
                    st.write(f':green[Fetched House records using {account}]')
                    fetched += 1
                    status.update(label=f":blue[Fetched {fetched} / 6 records. Trying Reader {i} / {number_of_accounts}]")
                if 'names' not in st.session_state:
                    name_sheet = client.open(sheet_name).worksheet('Eligibility')
                    st.write("Name worksheet found")
                    name_data = name_sheet.get(name_frame)
                    st.write("Name data downloaded")
                    name_dataframe = df_with_header(name_data)
                    st.write("Name data formatted")
                    st.session_state.names = name_dataframe
                    st.write(f':green[Fetched Name records using {account}]')
                    fetched += 1
                    status.update(label=f":blue[Fetched {fetched} / 6 records. Trying Reader {i} / {number_of_accounts}]")
                if 'theory' not in st.session_state:
                    theory_sheet = client.open(sheet_name).worksheet('Theory')
                    st.write("Theory worksheet found")
                    theory_data = theory_sheet.get(theory_frame)
                    st.write("Theory data downloaded")
                    theory_dataframe = df_with_header(theory_data)
                    st.write("Theory data formatted")
                    st.session_state.theory = theory_dataframe
                    st.write(f':green[Fetched Theory records using {account}]')
                    fetched += 1
                    status.update(label=f":blue[Fetched {fetched} / 6 records. Trying Reader {i} / {number_of_accounts}]")
                for batch in batch_sessions:
                    if batch not in st.session_state:
                        dataframes_sheet = client.open(sheet_name).worksheet(batch)
                        st.write(f'{batch} worksheet found')
                        dataframes_data = dataframes_sheet.batch_get(dataframes)
                        st.write(f'{batch} data downloaded')
                        batch_dataframes = []
                        for data in dataframes_data:
                            batch_dataframes += [df_with_header(data)]
                        st.write(f'{batch} data formatted')
                        st.session_state[batch] = batch_dataframes
                        st.write(f':green[Fetched {batch} records using {account}]')
                        fetched += 1
                        status.update(label=f":blue[Fetched {fetched} / 6 records. Trying Reader {i} / {number_of_accounts}]")
                if 'scores' not in st.session_state or 'score_news_update' not in st.session_state:
                    scores_sheet = client.open(sheet_name).worksheet('Scores')
                    st.write('Scores worksheet found')
                    scores_data = scores_sheet.batch_get(scores_frames)
                    st.write('Scores data downloaded')
                    scores_dataframe = df_with_header(scores_data[0])
                    score_news_update = scores_data[1][0][0]
                    st.write('Scores data formatted')
                    st.session_state.scores = scores_dataframe
                    st.session_state.score_news_update = score_news_update
                    st.write(f':green[Fetched Scores records using {account}]')
                    fetched += 1
                    status.update(label=f":blue[Fetched {fetched} / 6 records. Trying Reader {i} / {number_of_accounts}]")
                st.session_state.data_pulled = True
                status.update(label=f":green[Fetched 6 / 6 records! Click to see status log]", state="complete", expanded=False)
                return True
            except:
                i += 1
                st.write(f':red[Could not fetch records using {account}]')
                status.update(label=f":blue[Fetched {fetched} / 6 records. Trying Reader {i} / {number_of_accounts}]")
                continue
    status.update(label=f":red[Failed to fetch all records. Fetched {fetched} / 6 records. Click to see error log]", state="error", expanded=False)
    return False
    

# Display eligibility criteria for attendance
def attendance_eligibility_criteria():
    # Attendance tab
    st.warning('##### 🙋‍♂️ Attendance')
    with st.expander(" 📜 Eligibility Criteria"):
        st.write(f''' 1. Theory Attendance must be at least {cutoff['Theory']}%. 
                    This includes only theory classes, each worth 1 hour. ''')
        st.write(f''' 2. Practical Attendance must be at least {cutoff['Practical']}%. 
                    This includes lab sessions, SGDs, ECEs, Skill Certifications.
                    Each session is worth 2 hours, except ECE which is worth 3 hours. ''')
        st.write(f''' 3. AETCOM Attendance must be at least {cutoff['AETCOM']}%. 
                    This includes only AETCOM modules, each worth 1 hour. ''')
        st.write(f''' Key: SGD - Small Group Discussions; ECE - Early Clinical Exposure; 
                      AETCOM - Attitude, Ethics and Communication. ''')
        

# Display eligibility criteria for scores
def scores_eligibility_criteria():
    with st.expander(" 📜 Eligibility Criteria"):
        st.write(f''' 1. Theory Total must be at least 40%. 
                    This includes average of the three theory internal scores scaled to 80, 
                    and other formative scores scaled to 20. ''')
        st.write(f''' 2. Practical Total must be at least 40%. 
                    This includes average of the three practical internal scores scaled to 80,
                    and other formative scores scaled to 20. ''')
        st.write(f''' 3. Aggregate Score must be at least 50%. 
                    This is the average of the theory and practical scores. ''')
    with st.expander(" 📜 Scoring Criteria"):
        st.write(f''' 1. Aggregate Score (max. 100) = (Theory Total + Practical Total) / 2 ''')
        st.write(f''' 2. Theory Total (max. 100) = Theory IA + Theory FA ''')
        st.write(f''' 3. Practical Total (max. 100) = Practical IA + Practical FA ''')
        st.write(f''' 4. Theory IA (max. 80) = (Theory 1 + Theory 2 + Theory 3) / 3 .
                         All three scores Theory 1, 2 and 3 are scaled to 80. ''')
        st.write(f''' 5. Practical IA (max. 80) = (Practical 1 + Practical 2 + Practical 3) / 3 .
                         All three scores Practical 1, 2 and 3 are scaled to 80. ''')
        st.write(f''' 6. Theory FA (max. 20) = (Viva 1 + Viva 2 + MCQ 1 + MCQ 2 + MCQ 3 + Seminar + Th Professionalism) 
                         scaled to 20.''')
        st.write(f''' 7. Practical FA (max. 20) = (Class Test 1 + Class Test 2 + Class Test 3 + Record + Skill Certification + ECE + Assignment + Pr Professionalism) 
                         scaled to 20.''')
        st.write(f''' Key: IA - Internal Assessment; FA - Formative Assessment; MCQ - Multiple Choice Questions''')


# Render house leaderboard
def render_leaderboard():
    
    houses = st.session_state.houses
    
    tab1, tab2, tab3, tab4 = st.tabs([" ⌛ Hourglasses ", " 🏘️ House Leaderboard ", 
                                      " 📊 Global Leaderboard ", " 📜 Disclaimers "])

    with tab1:
        st.warning('Hourglasses', icon="⌛")
        house_leaderboard = houses[0]
        sorted_by_rank = house_leaderboard.sort_values(by=['Rank'], ascending=True)
        for i in range(5):
            render_house_card(sorted_by_rank, i)
    
    with tab2:
        st.warning('House Leaderboard', icon="📊")
        st.dataframe(houses[0], hide_index=True)
        with st.expander(" 📜 Scoring Criteria"):
            st.write(f''' Each house will be assigned a score, maximum being 1000, calculated as follows: ''')
            st.write(f''' Total = Attendance + Scores + Bonus ''')
            st.write(f''' 1. The Attendance component is calculated as the average attendance 
                    of all 50 students of the house, in all the sessions. This can be a maximum of 400. ''')
            st.write(f''' 2. The Scores component is calculated as the average score 
                    of all 50 students of the house, in all the assessments. This can be a maximum of 400. ''')
            st.write(f''' 3. The Bonus component is awarded in recognition of achievements of the house members 
                    or deducted as disciplinary action at the discretion of the department. 
                    100 points are given to every house at the beginning. This can be a maximum of 200. ''')
        st.image('images/Common.png')
        
    with tab3:
        st.warning('Global Leaderboard', icon="📊")
        with st.expander(" 📜 How to read the global leaderboard?"):
            st.write(''' You can interact with the table by scrolling.
                    Clicking on the column heads lets you sort through the leaderboard on that column. ''')
            st.write(''' The Ranking is based on relative individual attendance 
                    and internals scores of all 250 students. See you at the top! ''')
            st.write(f''' The columns are as follows:''')
            st.write(f''' 1. Roll No. - Roll number of the student. ''')
            st.write(f''' 2. Attnd (%) - Average attendance of the student, in percentage,
                    across all the sessions. ''')
            st.write(f''' 3. Att Rank - Ranking of the student out of 250, based on average attendance. ''')
            st.write(f''' 4. Tot Score - Total score of the student across all internal assessments. ''')
            st.write(f''' 5. Score Rank - Ranking of the student out of 250, based on total score. ''')
        leaderboard = houses[1]
        for column in global_leaderboard_columns:
            leaderboard[column] = pd.to_numeric(leaderboard[column])
        st.dataframe(leaderboard.loc[:, global_leaderboard_columns], hide_index=True)
    
    with tab4:
        disclaimers()

    with st.expander(" 📜 The Scientists That Inspired The House Names"):
        for scientist, url in scientists.items():
            st.markdown(f"[{scientist}]({url})")


# Render student profile
def render_profile(roll_number):
    # Profile tab
    st.warning('##### 👨‍⚕️ Student Profile')
    names = st.session_state.names
    name = names['Name'][roll_number-1]
    reg_no = names['Reg No'][roll_number-1]
    st.write(f' 👋 Hi, {name.title()} !')
    st.write(f' ⚕️ University Reg. No. - {reg_no}')
    st.write(f' 🩺 Roll No. - {roll_number}')
    st.warning('##### 🪄 Wizard Pass')
    index_hash = ((roll_number - 1) % 50) // 10
    house = houses_list[index_hash]
    data = format_image_file(f"images/{house}.png")
    card(
        title=f' {roll_number} ',
        text=[f'{name.title()}', f"{reg_no}"],
        image=data
        )
    

# Render house leaderboard
def render_house_leaderboard(roll_number):
    houses = st.session_state.houses
    index_hash = ((roll_number - 1) % 50) // 10
    house = houses_list[index_hash]
    st.image(f'images/{house}.png')
    leaderboard = houses[index_hash + 2]
    leaderboard['Tot Att'] = pd.to_numeric(leaderboard['Tot Att'])
    leaderboard['Tot Class'] = pd.to_numeric(leaderboard['Tot Class'])
    leaderboard['Attnd (%)'] = round(leaderboard['Tot Att'] * 100 / leaderboard['Tot Class'], 2).astype(float)
    for column in house_leaderboard_columns:
        leaderboard[column] = pd.to_numeric(leaderboard[column])
    
    st.warning('House Leaderboard', icon="📊")
    with st.expander(" 📜 How to read the house leaderboard?"):
        st.write(''' You can interact with the table by scrolling.
                 Clicking on the column heads lets you sort through the leaderboard. ''')
        st.write(''' The Ranking is based on relative individual attendance 
                 and internals scores of the 50 students in the house. 
                 The leaderboard indicates both the global and intra-house rankings. 
                 See you at the top! ''')
        st.write(f''' The columns are as follows:''')
        st.write(f''' 1. Roll No. - Roll number of the student. ''')
        st.write(f''' 2. Attnd (%) - Average attendance of the student, in percentage,
                 across all the sessions. ''')
        st.write(f''' 3. Att Rnk Glb - Global Ranking of the student out of 250, based on average attendance. ''')
        st.write(f''' 4. Att Rnk Hs - Intra-House Ranking of the student out of 50, based on average attendance. ''')
        st.write(f''' 5. Tot Scr - Total score of the student across all internal assessments. ''')
        st.write(f''' 6. Scr Rnk Glb - Global Ranking of the student out of 250, based on total score. ''')
        st.write(f''' 7. Scr Rnk Hs - Intra-House Ranking of the student out of 50, based on total score. ''')
    st.dataframe((houses[index_hash + 2]).loc[:, house_leaderboard_columns], hide_index=True)


# Render theory attendance
def render_theory(roll_number):
    theory = st.session_state.theory
    date_columns = list(theory.columns)
    if date_columns[0] == 'E':
        st.write(f"###### Theory : No theory classes conducted yet")
        st.session_state.theory_attendance = 'No theory classes conducted yet'
        return
    att_str = ''
    abs_list = [f'(s.no. | yyyy-mm-dd | hh-hh)']
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
        st.write(f"###### Theory : ( {attended} / {total} ) - ( {percentage} % ) - ( {eligibility} )")
        st.session_state.theory_attendance = percentage
        with st.expander(" 🙋‍♂️ Theory Overview"):
            st.write(att_str)
        with st.expander(" 🆎 Theory Absence Details"):
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
            st.write(f"###### {batch} : No {batch} sessions conducted yet")
            st.session_state[f'{batch}_attendance'] = f'No {batch} sessions conducted yet'
            continue
        att_str = ''
        if batch == 'AETCOM':
            abs_list = ['(s.no. | yyyy-mm-dd | module)']
        if batch == 'Practical':
            abs_list = ['(s.no. | yyyy-mm-dd | hh-hh | session)']
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

        if batch == 'Practical':
            total = total * 2
            attended = attended * 2
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
            st.write(f"###### {batch} : ( {attended} / {total} ) - ( {percentage} % ) - ( {eligibility} )")
            st.session_state[f'{batch}_attendance'] = percentage
            with st.expander(f' 🙋‍♂️ {batch} Overview'):
                st.write(att_str)
            with st.expander(f" 🆎 {batch} Absences"):
                for absence in abs_list:
                    st.write(absence)
        else:
            st.warning(f'No records found for {batch}', icon="⚠️")

        if errors > 0:
            st.error(f'{errors} errors detected in {batch} records. Kindly notify the department office', icon="⚠️")


# Render scores
def render_scores(roll_number):
    # Scores tab
    st.warning('##### 💯 Scores')
    # Scores update news
    st.write(f'''###### 🥳 {st.session_state.score_news_update} ''')
    
    scores = st.session_state.scores
    
    # Load formatted scores of student into dictionary
    student_scores = {}
    for column in scores_columns:
        student_scores[column] = f'{scores[column][roll_number-1]} / {scores[column][250]}'

    news = st.session_state.score_news_update

    # Extract elements within parentheses using regular expression
    matches = re.findall(r'\(([^)]+)\)', news)

    # Separate the matches into two lists
    if len(matches) >= 2:
        theory_list = matches[0].split(', ')
        practical_list = matches[1].split(', ')
    else:
        # Handle the case where there are not enough matches
        theory_list = []
        practical_list = []
    
    # Force columns on phone screens - must probably change every time the code changes
    st.write('''<style>
                .st-emotion-cache-keje6w {
                    width: calc(50% - 1rem) !important;
                    flex: 1 1 calc(50% - 1rem) !important;
                    min-width: calc(50% - 1rem) !important;
                }
                </style>''', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    try:
        if len(theory_list) > 0:
            theory_dict = {'Theory': [], 'Score': []}
            for match in theory_list:
                theory_dict['Theory'].append(match)
                theory_dict['Score'].append(student_scores[match])
            theory_df = pd.DataFrame(theory_dict)
            with col1:
                st.dataframe(theory_df, hide_index=True)
    except:
        pass

    try:
        if len(practical_list) > 0:
            practical_dict = {'Practical': [], 'Score': []}
            for match in practical_list:
                practical_dict['Practical'].append(match)
                practical_dict['Score'].append(student_scores[match])
            practical_df = pd.DataFrame(practical_dict)
            with col2:
                st.dataframe(practical_df, hide_index=True)
    except:
        pass
    
    # Check eligibility
    if float(scores['Aggregate'][roll_number-1]) < 50:
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
    st.write(f"###### Theory Total : {student_scores['Theory Total']} ( {theory_eligibility} )")
    st.write(f"###### Practical Total : {student_scores['Practical Total']} ( {practical_eligibility} )")
    st.write(f"###### Aggregate Score : {student_scores['Aggregate']} ( {aggregate_eligibility} )")
    
    # Display theory scores
    with st.expander(" 💯 Your Theory Scores"):
        theory_scores_dict = {'Assessment': [], 'Score': []}
        for column in theory_scores:
            theory_scores_dict['Assessment'].append(column)
            zeroes = scores[column].tolist().count('0')
            if zeroes == 250:
                theory_scores_dict['Score'].append('TBD')
                student_scores[column] = 'TBD'
            else:
                theory_scores_dict['Score'].append(student_scores[column])
        theory_scores_df = pd.DataFrame(theory_scores_dict)
        st.dataframe(theory_scores_df, hide_index=True)
    
    # Display practical scores
    with st.expander(" 💯 Your Practical Scores"):
        practical_scores_dict = {'Assessment': [], 'Score': []}
        for column in practical_scores:
            practical_scores_dict['Assessment'].append(column)
            zeroes = scores[column].tolist().count('0')
            if zeroes == 250:
                practical_scores_dict['Score'].append('TBD')
                student_scores[column] = 'TBD'
            else:
                practical_scores_dict['Score'].append(student_scores[column])
        practical_scores_df = pd.DataFrame(practical_scores_dict)
        st.dataframe(practical_scores_df, hide_index=True)
    
    st.session_state.student_scores = student_scores

    scores_eligibility_criteria()


# Render signatures
def signatures():
    sign1, sign2 = st.columns([2,1])

    with sign1:
        st.success(" Conjured by Dr Suraj ", icon="🪄")
    with sign2:
        st.info(" Version 3.1 ", icon="🪄")

    
# Render disclaimers
def disclaimers():
    st.warning('##### 📜 Disclaimers')
    st.write(''' 📜 House concept and emblems created by Dr Hudson ''')
    st.write(''' 📜 Please note that these records are made available provisionally 
             for your reference, by the Department of Physiology. 
             All the records are for the subject of Physiology and for the batch of 2023-24 only. ''')

    st.write(''' 📜 The records are not guaranteed to be completely accurate.
             In case of any inconsistencies with our physical records, the physical records shall be considered final.
             If you notice any discrepancies, please notify the department office immediately.''')

    st.write(''' 📜 Eligibility criteria for appearing in the final examination 
             are based on the attendance and formative assessment scores. 
             You will be allowed to write the examination only after fulfilling the eligibility criteria.
             Not fulfilling the criteria will result in disqualification.''')
    ai_disclaimers()

    
def ai_disclaimers():
    st.write(''' 📜 Divination is an experimental AI feature, using a third party AI model 
             to generate personalized feedback responses based on the student's performance. 
             The generated responses may not be accurate.
             They have the same limitations as any AI model. 
             The app developer does not take any responsibility for any such errors. ''')

    st.write(f''' 📜 If you find that the responses are being inaccurate most of the time, 
             please write to me so that I can tweak the prompts. Include the response, if possible.
             You can find my contact details in the developer's note below. ''' )

    st.write(''' 📜 Your attendance and scores are shared with the AI for generating the feedback.
             No sensitive personal information like your name or register number is shared. ''')


def support_the_app():
    phone_number = st.secrets['phone_number']
    upi_id = st.secrets['upi_id']
    st.write(f''' 💝 Donate / Buy Me A Coffee ! Thank you for your support ! ''' )
    st.write(f''' 💸 UPI ID: :green[{upi_id}] ''' )
    st.write(f''' 📱 GPay: :green[{phone_number}] ''' )


# Developer's Note
def developers_note():
    phone_number = st.secrets['phone_number']
    st.write(f''' 💌 Developer's Note - Thank you for using my app! I hope you find it helpful. 
             I would really appreciate your valuable feedback. Anything you would like to tell me is welcome!
             Please reach out to me if you have any messages, suggestions, comments, queries or error reports.
             You can text me on WhatsApp or send me an anonymous owl message using the google form below. ''')
    st.write(f''' 💬: :green[{phone_number}] ''' )
    st.write(f''' 🦉: https://forms.gle/yCE9FAEyyQ5iDEgR8 ''' )
    st.write(''' 🖊️ Dr Suraj, your friendly neighborhood Web Developer (not Spider-Man, unfortunately)''')
    

# Error message when failed to fetch records
def failed_to_fetch():
    phone_number = st.secrets['phone_number']
    st.error(' Could not fetch all the records', icon="⚠️")
    st.info(''' The most likely cause for this error is that the google server limits have been reached.
            The limits are refreshed every minute. 
            Please refresh the page and try again after a couple of minutes. ''', icon="ℹ️")
    st.info(''' The app supports a limited number of simultaneous users per minute. 
            If too many users try to fetch records over the same 60 seconds interval, 
            some users may fail to fetch some or all sets of records at the same time.
            You can review your error log to see which records failed to fetch. ''', icon="ℹ️")
    st.info(f''' If this error persists, or you encounter it very frequently, kindly notify me. 
            If possible, please include the error log above to help me debug.
            I will try to fix it or expand the limits on simultaneous users.
            My phone number is :green[{phone_number}]. You can text me on WhatsApp. 
            You can also write to me anonymously using this google form : 
            https://forms.gle/yCE9FAEyyQ5iDEgR8 ''', icon="ℹ️")
    st.info(''' Dr Suraj, your friendly neighborhood Web Developer (not Spider-Man, unfortunately) ''', icon="👨🏻‍💻")

# AI Query
def ai_query(limit):
    word_limit = word_limits[limit]
    theory_attendance = st.session_state.theory_attendance
    practical_attendance = st.session_state.Practical_attendance
    aetcom_attendance = st.session_state.AETCOM_attendance
    student_scores = st.session_state.student_scores
    scores_part_of_query = "The student's theory scores are - "
    theory_pending = []
    for assessment in theory_scores:
        if student_scores[assessment] != 'TBD':
            scores_part_of_query += f'{assessment} : {student_scores[assessment]}, '
        else:
            theory_pending.append(assessment)
    scores_part_of_query += f". The student's practical scores are - "
    practical_pending = []
    for assessment in practical_scores:
        if student_scores[assessment] != 'TBD':
            scores_part_of_query += f'{assessment} : {student_scores[assessment]}, '
        else:
            practical_pending.append(assessment)
    assessments_status = ""
    if theory_pending or practical_pending:
        assessments_status = ''' Some assessments have not been conducted yet.
                            The student must be consistent in his performance in the upcoming assessments
                            to get the required total marks to be eligible to write the university exams. '''
        if theory_pending:
            assessments_status += f''' Theory assessments not yet conducted are: {', '.join(theory_pending)}. '''
        if practical_pending:
            assessments_status += f''' Practical assessments not yet conducted are: {', '.join(practical_pending)}. '''
    else:
        assessments_status = ''' All assessments have been conducted. The theory total, practical total 
                            and aggregate scores have been calculated and finalized.
                            If the student is not eligible, he will have to attempt the remedial
                            assessments to be eligible to write the university exams. '''
    if ("Theory 3" not in theory_pending) and ("Practical 3" not in practical_pending):
        theory_total = student_scores["Theory Total"]
        practical_total = student_scores["Practical Total"]
        aggregate = student_scores["Aggregate"]
        scores_part_of_query += f'''. As most assessments have been conducted, the student's final scores 
                                have been calculated. The theory total is {theory_total}, 
                                the practical total is {practical_total}, and the aggregate score is {aggregate}. 
                                If the student is not eligible, he will have to attempt the remedial assessments 
                                to be eligible to write the university exams '''
    query = f'''You are a professor of Physiology. You teach 250 medical school students. 
            You manage the attendance and scores records of the students throughout the year (3 terms). 
            A student must fulfil all minimum eligibility criteria for attendance and internal assessment scores
            to be eligible to write the university exams.
            The criteria for attendance are:
            1. Theory - 75 %,
            2. Practical - 80 %,
            3. AETCOM - 75 %.
            The criteria for internal assessment scores are:
            1. Theory Total - 40 %,
            2. Practical Total - 40 %,
            3. Aggregate - 50 %.
            The internal assessment scores are calculated after considering 
            multiple internal assessments conducted throughout 3 terms, numbered 1 to 3 if applicable
            (for example, MCQ 1, MCQ 2, MCQ 3).
            So, a general rule of thumb is that a score of 50% or higher in each assessment is good.
            I will now tell you the attendance and scores of a particular student. 
            The attendances I provide will be a snapshot of 
            the current state and more classes may be taken, so an ineligibility can be recovered from.
            If there are no more classes, remedial classes will be conducted.
            I will provide the scores of assessments already conducted. 
            {assessments_status}.
            The student's attendance in percentages are - theory : {theory_attendance} , 
            practical : {practical_attendance} , AETCOM : {aetcom_attendance}. 
            {scores_part_of_query}.
            I want you to provide the student with
            feedback and insights or recommendations based on his performance. If possible, include comments
            on the trend in his performance over the terms (an assessment will have the term number after 
            its name if it is conducted multiple times).
            I want you to provide encouragement, feedback or caution to the student as is appropriate. 
            Please phrase your answer as though you are directly addressing the student. 
            Please do not include a greeting at the beginning or sign anything at the end. 
            Keep it a little informal. Keep the word limit of your response strictly between {word_limit} words. '''
    #st.write(f'''###### {query}''')
    return query


def ai_feedback(limit):
    api_keys = ['API_key_1', 'API_key_2', 'API_key_3', 'API_key_4']
    random_api_key = random.choice(api_keys)
    my_api_key = st.secrets[random_api_key]
    genai.configure(api_key=my_api_key)
    model = genai.GenerativeModel('gemini-pro')
    query = ai_query(limit)
    response = model.generate_content(query)
    return response


def ai_render(limit):
    with st.spinner(''' ##### 🔮 The all-seeing magic crystal ball is looking into you '''):
        try:
            ai_response = ai_feedback(limit)
            ai_success = True
        except:
            ai_success = False
        if ai_success:
            st.write(ai_response.text)
        else:
            st.write(" 🔮 The all-seeing magic crystal ball is dreaming. It will be back with you in a minute.")
            st.write(''' 😴 When the crystal ball is used too frequently, it overheats and goes to sleep.
                     But worry not, it will only take a short nap of 60 seconds. Please try again after a minute.  ''')


def render_divination():
    st.warning('##### 🔮 Divination')
    st.write('##### 🔮 The all-seeing magic crystal ball offers its divination services!')
    st.write('''<style>
                .st-emotion-cache-1r6slb0 {
                    width: calc(33.33% - 1rem) !important;
                    flex: 1 1 calc(33.33% - 1rem) !important;
                    min-width: calc(33.33% - 1rem) !important;
                }
                </style>''', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        short = st.button(" 🪄 Less! ")
    with col2:
        medium = st.button(" 🪄 Divine! ")
    with col3:
        long = st.button(" 🪄 More! ")
    if short:
        ai_render('short')
    elif long:
        ai_render('long')
    elif medium:
        ai_render('medium')
    else:
        st.write(''' 🪄 You can try generating your feedback multiple times by clicking on the buttons above, 
                based on how long you want your response to be. ''')
    with st.expander(" 📜 Disclaimers "):
        ai_disclaimers()


def format_image_file(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data)
    data = "data:image/png;base64," + encoded.decode("utf-8")
    return data


def render_house_card(leaderboard, index):
    house = leaderboard.loc[index,'House']
    total = leaderboard.loc[index,'Total']
    rank = leaderboard.loc[index,'Rank']
    data = format_image_file(f"images/{house}.png")
    card(
        title=f" ⌛ {total} ⌛ ",
        text=[medals[rank], f"Rank : {rank}"],
        image=data
        )


def render_eligibility():
    if st.session_state.eligible:
        st.balloons()
        st.success('''🎉 Congratulations, young wizard! You have completed your trials successfully. 
                   You are now ready for a bigger trial, the university examination!''')
    else:
        st.error('''Uh oh! Looks like you have fallen short of fulfilling some eligibility criteria.
                   Check your scores and attendance to see how you can remedy it!''')