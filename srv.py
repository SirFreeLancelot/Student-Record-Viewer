import streamlit as st
from helpers import *
from datetime import date


# Initialize session state variables
if 'valid_roll_number' not in st.session_state:
    st.session_state.valid_roll_number = False
if 'data_pulled' not in st.session_state:
    st.session_state.data_pulled = False
if 'data_date' not in st.session_state:
    st.session_state.data_date = ''
if 'eligible' not in st.session_state:
    st.session_state.eligible = False


# Title of the app
st.title('The Physiology Archives')


# Fetch data
if not st.session_state.data_pulled:
    signatures()
    developers_note()
    with st.spinner(''' Fetching student records. Please be patient. This may take a few seconds. '''):
        try:
            load_data = load_student_data()
            if not load_data or not st.session_state.data_pulled:
                raise Exception
            st.session_state.data_date = date.today().strftime("%d/%m/%Y")
        except:
            failed_to_fetch()
            st.stop() 
    st.experimental_rerun()


# Roll Number input and space for warning
rno, warn = st.columns([1,5])
with rno:
    roll_number = st.text_input("Roll Number")


# Validate Roll Number
try:
    roll_number = int(roll_number)
    if roll_number not in range(1, 251):
        raise Exception
    st.session_state.valid_roll_number = True
except:
    with warn:
        st.warning(' Roll Number must be between 1 to 250', icon="⚠️")
    st.session_state.valid_roll_number = False


# Show leaderboard
if not st.session_state.valid_roll_number and st.session_state.data_pulled:
    render_leaderboard()


# Show student record for roll number
if st.session_state.valid_roll_number and st.session_state.data_pulled:
    st.session_state.eligible = True
    tab1, tab2, tab3 = st.tabs(["Profile", "Attendance", "Scores"])

    with tab1:
        # Profile tab
        st.warning('##### Student Profile')
        render_profile(roll_number)

    with tab2:
        # Attendance tab
        st.warning('##### Attendance') 
        attendance_eligibility_criteria()
        render_theory(roll_number)
        render_attendance(roll_number)

    with tab3:
        # Scores tab
        st.warning('##### Scores')
        # Scores update news
        st.write(f'''###### {st.session_state.score_news_update} ''')
        render_scores(roll_number)
        scores_eligibility_criteria()
       

signatures()

disclaimers()

developers_note()

