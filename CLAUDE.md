# Project Context

## What This Project Is
A Streamlit web app that helps GIX students submit complete purchase requests on the first try, reducing back-and-forth with the Program Coordinator.

## Tech Stack
- Python 3.12+
- Streamlit for the web interface
- Plotly for interactive charts
- Pandas for data manipulation

## Project Structure
- app.py — Main application entry point
- wayfinder_app.py — Alternative main app
- data/ — Data files

## Development Commands
- Run the app: python -m streamlit run app.py
- Install dependencies: pip install -r requirements.txt

## Coding Standards
- Follow PEP 8 style guidelines
- Use type hints on all function signatures
- Write Google-style docstrings for all functions
- Handle errors gracefully with st.error() or st.warning()
- Never hardcode sensitive data

## Important Notes
- This is a course project for TECHIN 510 at UW GIX
- Target users: GIX students submitting purchase requests
- Always verify the app still runs after making changes
