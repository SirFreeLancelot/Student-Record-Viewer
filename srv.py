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
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'theory_attendance' not in st.session_state:
    st.session_state.theory_attendance = 0
if 'Practical_attendance' not in st.session_state:
    st.session_state.practical_attendance = 0
if 'AETCOM_attendance' not in st.session_state:
    st.session_state.AETCOM_attendance = 0
if 'student_scores' not in st.session_state:
    st.session_state.student_scores = 0


# Title of the app
st.title('The House of Mirrors')


# Ask for password
if not st.session_state.authenticated:
    st.image('images/You shall not pass.jpg')
    password = st.text_input("Passphrase")
    st.warning(''' To reflect on your reflections, say the magic words. ''', icon="🧙‍♂️")
    # Check if password is correct
    if password.strip().lower() == st.secrets['password']:
        st.session_state.authenticated = True
        st.rerun()
    else:
        signatures()
        st.stop()


# Fetch data
if not st.session_state.data_pulled:
    signatures()
    support_the_app()
    developers_note()
    with st.spinner(''' 🪄 Casting Accio on student records. Please be patient. This may take a few seconds. '''):
        try:
            load_data = load_student_data()
            if not load_data or not st.session_state.data_pulled:
                raise Exception
            st.session_state.data_date = date.today().strftime("%d/%m/%Y")
        except:
            failed_to_fetch()
            st.stop() 
    st.rerun()


# Roll Number input and space for warning
rno, warn = st.columns([1,5])
with rno:
    roll_number = st.text_input("Roll Number")
with st.expander(' 💝 Support the App '):
    support_the_app()
with st.expander(" 💌 Send Feedback "):
    developers_note()
st.write(' ↔️ swipe through tabs to see more ↔️ ')


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
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([" 👨‍⚕️ Profile ", " 🏠 House ", 
                                            " 🔮 Divination ", " 🙋‍♂️ Attendance ", 
                                            " 💯 Scores ", " 📜 Disclaimers "])

    with tab1:
        eligibility_banner = st.empty()
        render_profile(roll_number)
    
    with tab2:
        render_house_leaderboard(roll_number)

    with tab3:
        magic_crystal_ball = st.empty()

    with tab4: 
        attendance_eligibility_criteria()
        render_theory(roll_number)
        render_attendance(roll_number)

    with tab5:
        render_scores(roll_number)

    with tab6:
        disclaimers()


signatures()
support_the_app()
developers_note()


if st.session_state.valid_roll_number and st.session_state.data_pulled:
    with eligibility_banner.container():
        render_eligibility()
    with magic_crystal_ball.container():
        render_divination()

