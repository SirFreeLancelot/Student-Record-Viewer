import streamlit as st
from helpers import *
from datetime import date

# Title of the app
st.title('Student Record Viewer Physiology 2023-24')

# Instructions
st.info(''' Enter your Roll Number''', icon="ℹ️")

# Initialize session state variables
if 'valid_roll_number' not in st.session_state:
    st.session_state.valid_roll_number = False
if 'data_pulled' not in st.session_state:
    st.session_state.data_pulled = False
if 'data_date' not in st.session_state:
    st.session_state.data_date = ''
if 'eligible' not in st.session_state:
    st.session_state.eligible = False

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

# Fetch data
if st.session_state.valid_roll_number and not st.session_state.data_pulled:
    with st.spinner(''' Fetching student records. This happens only once and may take a few seconds.
                    Once the data is fetched, your subsequent checks will be instantaneous. '''):
        try:
            load_data = load_student_data()
            if not load_data or not st.session_state.data_pulled:
                raise Exception
            st.session_state.data_date = date.today().strftime("%d/%m/%Y")
        except:
            failed_to_fetch()

# Columns for flashing messages
info1, info2 = st.columns([1,1])

# Success message if data pulled
if st.session_state.data_pulled:
    with info1:
        st.success(f' Fetched records as on {st.session_state.data_date}', icon="✅")

# Show student record for roll number
if st.session_state.valid_roll_number and st.session_state.data_pulled:
    with info2:
        st.info(f' Showing records for roll number {roll_number}', icon="ℹ️")
    st.session_state.eligible = True
    
    # Attendance block
    st.warning('##### Attendance') 
    attendance_eligibility_criteria()
    render_theory(roll_number)
    render_attendance(roll_number)
     
    # Scores block
    st.warning('##### Scores')
    # Scores update news
    st.write(f'''###### {st.session_state.score_news_update} ''')
    scores_eligibility_criteria()
    render_scores(roll_number)

    # Celebrate if eligible
    #if st.session_state.eligible:
      #  with warn:
       #     st.success('All eligibility criteria met! All the best for the exam!', icon="🌟")
      #  st.balloons()
   # else:
      #  pass
        #with warn:
           # st.warning('You do not fulfil certain eligibility criteria', icon="⚠️")
       

signatures()

disclaimers()

developers_note()

