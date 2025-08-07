# 📊 app.py – Streamlit UI for TimeGuard

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, timedelta
import json

# --------------------
# 📦 Utility Functions
# --------------------

def time_overlap(start1, end1, start2, end2):
    return max(start1, start2) < min(end1, end2)

def parse_timesheet(df):
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['start'] = pd.to_datetime(df['start'], format="%H:%M").dt.time
    df['end'] = pd.to_datetime(df['end'], format="%H:%M").dt.time
    return df

def generate_mock_calendar(start_date: str, days: int = 7):
    import random
    calendar_data = {}
    base_date = datetime.strptime(start_date, "%Y-%m-%d")
    for i in range(days):
        current_date = (base_date + timedelta(days=i)).date().isoformat()
        events = []
        num_events = random.choice([1, 2])
        start_hour = 9
        for j in range(num_events):
            event_start = datetime(base_date.year, base_date.month, base_date.day + i, start_hour + j*2)
            event_end = event_start + timedelta(hours=1)
            events.append({
                "id": str(uuid.uuid4()),
                "title": f"Project Work {j+1}",
                "start": event_start.isoformat(),
                "end": event_end.isoformat()
            })
        calendar_data[current_date] = events
    return calendar_data

def validate_timesheet_against_calendar(timesheet_df, calendar_data):
    missing_entries = []
    extra_entries = []
    grouped_ts = timesheet_df.groupby('date')

    for day, events in calendar_data.items():
        cal_date = datetime.strptime(day, "%Y-%m-%d").date()
        ts_entries = grouped_ts.get_group(cal_date) if cal_date in grouped_ts.groups else pd.DataFrame(columns=timesheet_df.columns)
        matched_ts = [False] * len(ts_entries)
        matched_cal = [False] * len(events)

        for i, cal_event in enumerate(events):
            cal_start = datetime.fromisoformat(cal_event['start']).time()
            cal_end = datetime.fromisoformat(cal_event['end']).time()
            match_found = False
            for j, ts_row in ts_entries.iterrows():
                ts_start = ts_row['start']
                ts_end = ts_row['end']
                if time_overlap(cal_start, cal_end, ts_start, ts_end):
                    match_found = True
                    matched_ts[ts_entries.index.get_loc(j)] = True
                    matched_cal[i] = True
                    break
            if not match_found:
                missing_entries.append({
                    "date": cal_date.isoformat(),
                    "start": cal_start.isoformat(),
                    "end": cal_end.isoformat(),
                    "reason": "No matching timesheet entry"
                })

        for i, matched in enumerate(matched_ts):
            if not matched:
                row = ts_entries.iloc[i]
                extra_entries.append({
                    "date": row['date'].isoformat(),
                    "start": row['start'].isoformat(),
                    "end": row['end'].isoformat(),
                    "project": row['project'],
                    "reason": "No matching calendar event"
                })

    return {
        "missingEntries": missing_entries,
        "extraEntries": extra_entries
    }

# -----------------------
# 🖥️ Streamlit Dashboard
# -----------------------

st.set_page_config(page_title="TimeGuard – Timesheet Validator", layout="wide")
st.title("⏰ TimeGuard – Timesheet Validator")
st.markdown("Upload your timesheet and validate it against calendar events.")

uploaded_file = st.file_uploader("📁 Upload Timesheet CSV", type=["csv"])

if uploaded_file:
    ts_df = pd.read_csv(uploaded_file)
    ts_df = parse_timesheet(ts_df)

    st.subheader("📄 Parsed Timesheet")
    st.dataframe(ts_df)

    # Generate mock calendar
    calendar_data = generate_mock_calendar(start_date=ts_df['date'].min().isoformat(), days=7)

    # Run validation
    report = validate_timesheet_against_calendar(ts_df, calendar_data)

    # Display Results
    st.subheader("🚨 Missing Entries from Timesheet")
    if report["missingEntries"]:
        st.dataframe(pd.DataFrame(report["missingEntries"]).style.set_properties(**{'background-color': '#ffcccc'}))
    else:
        st.success("No missing entries 🎉")

    st.subheader("⚠️ Extra Entries in Timesheet")
    if report["extraEntries"]:
        st.dataframe(pd.DataFrame(report["extraEntries"]).style.set_properties(**{'background-color': '#fff3cd'}))
    else:
        st.success("No extra entries 🎉")
