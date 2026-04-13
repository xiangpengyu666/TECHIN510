import streamlit as st

QUARTERS = [
    "Spring 2025",
    "Summer 2025",
    "Fall 2025",
    "Winter 2026",
    "Spring 2026",
    "Summer 2026",
    "Fall 2026",
    "Winter 2027",
]

SUMMER_2025_INDEX = QUARTERS.index("Summer 2025")
FALL_2025_INDEX = QUARTERS.index("Fall 2025")

st.title("GIX Career Services Event Eligibility Checker")

program = st.selectbox("Program", ["MSTI", "Other"])
graduation_quarter = st.selectbox("Graduation Quarter", QUARTERS)
cpt = st.toggle("CPT Status (Active CPT)")

is_msti = program == "MSTI"
grad_index = QUARTERS.index(graduation_quarter)
grad_summer_2025_or_later = grad_index >= SUMMER_2025_INDEX
grad_fall_2025_or_later = grad_index >= FALL_2025_INDEX

st.subheader("Your Eligibility Results")

eligible_count = 0

# Mock Interviews: eligible if MSTI or CPT
if is_msti or cpt:
    st.success("Mock Interviews — You are eligible.")
    eligible_count += 1
else:
    st.warning("Mock Interviews — You are not eligible (requires MSTI program or active CPT).")

# Resume Reviews: eligible if MSTI or CPT or graduation Summer 2025 or later
if is_msti or cpt or grad_summer_2025_or_later:
    st.success("Resume Reviews — You are eligible.")
    eligible_count += 1
else:
    st.warning("Resume Reviews — You are not eligible (requires MSTI, active CPT, or graduation Summer 2025 or later).")

# Employer Panels: eligible if (MSTI or CPT) and graduation Fall 2025 or later
if (is_msti or cpt) and grad_fall_2025_or_later:
    st.success("Employer Panels — You are eligible.")
    eligible_count += 1
else:
    st.warning("Employer Panels — You are not eligible (requires MSTI or active CPT, and graduation Fall 2025 or later).")

# Networking Nights: eligible if MSTI and CPT
if is_msti and cpt:
    st.success("Networking Nights — You are eligible.")
    eligible_count += 1
else:
    st.warning("Networking Nights — You are not eligible (requires both MSTI program and active CPT).")

if eligible_count == 0:
    st.error("You do not qualify for any events at this time.")
