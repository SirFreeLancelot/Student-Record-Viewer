import streamlit as st
st.set_page_config(layout="wide")
from helpers import *


st.title('Student Record Manager - Admin')

col1, col2, col3, col4 = st.columns(4)

with col1:
    date = st.date_input("Date")

with col2:
    selected_class_slot = st.selectbox("Time", class_slots)

with col3:
    selected_session_type = st.selectbox("Session", session_types)

with col4:
    if selected_session_type == 'Theory':
        batches_allowed = ['All']
    else:
        batches_allowed = ['A', 'B', 'C', 'D', 'E']
    selected_batch = st.selectbox("Batch", batches_allowed)

if 'batch' not in st.session_state:
    st.session_state.batch = ''

if 'session_type' not in st.session_state:
    st.session_state.session_type = ''

if 'working_data' not in st.session_state:
    st.session_state.working_data = {}

if 'loaded_data_hash' not in st.session_state:
    st.session_state.loaded_data_hash = ''

if 'attendance_list' not in st.session_state:
    st.session_state.attendance_list = []

if 'column_name' not in st.session_state:
    st.session_state.column_name = ''

if 'session_changed' not in st.session_state:
    st.session_state.session_changed = False

if 'saved_to_google_sheets' not in st.session_state:
    st.session_state.saved_to_google_sheets = False

date_str = date.strftime('%d-%m')
column_name = f"{date_str} | {selected_class_slot}"

if selected_session_type != st.session_state.session_type or selected_batch != st.session_state.batch or st.session_state.session_changed:
    try:
        data = load_attendance_data(selected_session_type, selected_batch)
        df = df_with_header(data)
        data_hash = df_to_hash(df)
        st.session_state.loaded_data_hash = data_hash
        st.session_state.working_data = df
        st.session_state.session_type = selected_session_type
        st.session_state.batch = selected_batch
        st.session_state.session_changed = True
    except:
        st.warning('Something went wrong while loading the attendance data')

working_data = st.session_state.working_data

warn1, warn2 = st.columns([2,3])

with warn1:
    st.info(f'Marking attendance for : {selected_session_type} on {column_name} for {selected_batch} batch', icon="ℹ️") 

mark2, mark3 = st.columns(2)

with mark2:
    mark_all_present = st.button(":green[Mark All Present]")
if mark_all_present:
    st.session_state.attendance_list = ['P'] * len(working_data)

with mark3:
    mark_all_absent = st.button(":red[Mark All Absent]")
if mark_all_absent:
    st.session_state.attendance_list = ['A'] * len(working_data)

if st.session_state.column_name != column_name or st.session_state.session_changed:
    if column_name not in list(working_data.columns):
        attendance_list = ['A'] * len(working_data)
        st.session_state.attendance_list = attendance_list
    else:
        attendance_list = working_data[column_name].tolist()
        st.session_state.attendance_list = attendance_list
    st.session_state.column_name = column_name
    st.session_state.session_changed = False

start = batches[selected_batch]["start"]
end = batches[selected_batch]["end"]

ta1, ta2 = st.columns(2)

with ta1:
    present_numbers = st.text_area("Enter Present Student Numbers - one number per line")

present_errors = ''

present = present_numbers.split('\n')
for student_number in present:
    try:
        num = int(student_number)
        if num in range(start, end+1):
            mark_attendance(num, start, end, 'P')
        else:
            present_errors += f"('{student_number}')"
    except:
        present_errors += f"('{student_number}')"


if present_errors not in ['', "('')"]:
    st.error(f"Wrong inputs: {present_errors}. Advised to refresh, recheck and try again", icon="🚨")

with ta2:
    absent_numbers = st.text_area("Enter Absent Student Numbers - one number per line")

absent_errors = ''

absent = absent_numbers.split('\n')
for student_number in absent:
    try:
        num = int(student_number)
        if num in range(start, end+1):
            mark_attendance(num, start, end, 'A')
        else:
            absent_errors += f"('{student_number}')"
    except:
        absent_errors += f"('{student_number}')"


if absent_errors not in ['', "('')"]:
    st.error(f"Wrong inputs: {absent_errors}. Advised to refresh, recheck and try again", icon="🚨")

# Create a 25x10 grid layout for the student buttons
button_grid = st.columns(25)
strength = 0
for i, attendance in enumerate(st.session_state.attendance_list):
   with button_grid[i // 10]:
       if attendance == 'P':
           strength += 1
           st.write(f":green[{start+i}]")
       else:
           st.write(f":red[{start+i}]")

confirm1, confirm2, confirm3 = st.columns([1,1,2])

with confirm1:
    st.info(f"Total Strength: {strength} / {end-start+1}", icon="ℹ️")

with confirm2:
    save_to_google_sheets = st.button(":green[Save to Google Sheets]")

if save_to_google_sheets:
    try:
        prev_data = load_attendance_data(selected_session_type, selected_batch)
        prev_df = df_with_header(prev_data)
        prev_data_hash = df_to_hash(prev_df)
        if prev_data_hash != st.session_state.loaded_data_hash:
            with warn2:
                st.error('Change detected in Google Sheets. Loaded data outdated. Refresh and try again.', icon="🚨")
            with confirm3:
                st.error('Change detected in Google Sheets. Loaded data outdated. Refresh and try again.', icon="🚨")
            raise Exception("Data Integrity Test failed. Refresh the page and try again.")
        st.session_state.working_data[column_name] = st.session_state.attendance_list
        current_data_hash = df_to_hash(st.session_state.working_data)
        if current_data_hash == st.session_state.loaded_data_hash:
            with confirm3:
                st.success('No change detected in attendance data. Data synced with Google Sheets.', icon="✅")
            with warn2:
                st.success('No change detected in attendance data. Data synced with Google Sheets.', icon="✅")
            raise Exception("No change detected in data. Saving not required.")
        save_attendance_data(selected_session_type, selected_batch, st.session_state.working_data)
        saved_data = load_attendance_data(selected_session_type, selected_batch)
        saved_df = df_with_header(saved_data)
        saved_data_hash = df_to_hash(saved_df)
        if current_data_hash != saved_data_hash:
            with warn2:
                st.error('Save data corrupted. Advised to verify manually and compare with backup data.', icon="🚨")
            with confirm3:
                st.error('Save data corrupted. Advised to verify manually and compare with backup data.', icon="🚨")
            raise Exception("Save data corrupted. Verify manually.")
        st.session_state.session_changed = True
        st.session_state.saved_to_google_sheets = True
        st.session_state.loaded_data_hash = current_data_hash
        st.experimental_rerun()
    except:
        pass

if st.session_state.saved_to_google_sheets:
    with warn2:
        st.success('Attendance successfully saved!', icon="✅")
    with confirm3:
        st.success('Attendance successfully saved!', icon="✅")
    st.session_state.saved_to_google_sheets = False
    st.session_state.session_changed = False

with warn2:
    if column_name not in list(working_data.columns):
        st.warning(f'No corresponding data found. Temporary data added. Changes will be lost on page refresh unless saved', icon="⚠️")
    elif working_data[column_name].tolist() != st.session_state.attendance_list:
        st.warning(f'Attendance has been changed. Changes will be lost on page refresh unless saved', icon="⚠️")


sign1, sign2 = st.columns([2,1])

with sign1:
    st.success("Developed by Dr Suraj", icon="🌟")
with sign2:
    st.info("Version 1.1", icon="ℹ️")

