import streamlit as st

st.set_page_config(page_title="GIX Career Services Eligibility Checker", layout="centered")

st.title("🎓 GIX Career Services Eligibility Checker")

st.markdown("Check which Career Services events you qualify for based on your status.")

# --- Inputs ---
program = st.selectbox(
    "Select your program:",
    ["MSTI", "Other"]
)

graduation_quarter = st.selectbox(
    "Select your graduation quarter:",
    [
        "Spring 2025",
        "Summer 2025",
        "Autumn 2025",
        "Winter 2026",
        "Spring 2026",
        "Summer 2026",
        "Autumn 2026",
        "Winter 2027"
    ]
)

cpt_status = st.toggle("Do you have CPT authorization?")

st.divider()

# --- Eligibility Logic ---
eligible_events = []

# Example rule logic (simple + reasonable assumptions)
# You can tweak this later if needed

# Mock Interviews → MSTI students only
if program == "MSTI":
    eligible_events.append("Mock Interviews")

# Resume Reviews → everyone qualifies
eligible_events.append("Resume Reviews")

# Employer Panels → requires CPT
if cpt_status:
    eligible_events.append("Employer Panels")

# Networking Nights → MSTI OR graduating soon (2026+)
if program == "MSTI" or "2026" in graduation_quarter or "2027" in graduation_quarter:
    eligible_events.append("Networking Nights")

# --- Display Results ---
st.subheader("Your Eligible Events:")

all_events = [
    "Mock Interviews",
    "Resume Reviews",
    "Employer Panels",
    "Networking Nights"
]

qualified_count = 0

for event in all_events:
    if event in eligible_events:
        st.success(f"✅ {event}")
        qualified_count += 1
    else:
        st.warning(f"⚠️ {event}")

# --- No eligibility case ---
if qualified_count == 0:
    st.error("You do not qualify for any events at this time.")