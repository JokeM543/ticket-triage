import streamlit as st
import pandas as pd
import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
from postgrest.exceptions import APIError
from supabase import create_client

# 1. Page Configuration
st.set_page_config(page_title="AI Triage Dashboard", page_icon="🎫", layout="wide")

# 2. Setup and Authentication
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def validate_supabase_url(url: str | None) -> str:
    if not url:
        st.error("SUPABASE_URL is missing from .env.")
        st.stop()

    parsed = urlparse(url)
    if parsed.path not in ("", "/"):
        st.error("SUPABASE_URL should be the Supabase Project URL only, without /rest/v1.")
        st.stop()

    return url


@st.cache_resource
def init_connection():
    if not SUPABASE_KEY:
        st.error("SUPABASE_KEY is missing from .env.")
        st.stop()

    return create_client(validate_supabase_url(SUPABASE_URL), SUPABASE_KEY)

supabase = init_connection()

st.title("🎫 Intelligent Support Ticket Triage")
st.markdown("Monitor and manage incoming support requests classified by our ML engine.")

submit_success = st.session_state.pop("ticket_submit_success", None)
if submit_success:
    st.success(submit_success)


def format_api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or f"Backend returned HTTP {response.status_code}."

    detail = payload.get("detail")
    if isinstance(detail, list):
        messages = []
        for item in detail:
            location = " -> ".join(str(part) for part in item.get("loc", []))
            message = item.get("msg", "Validation error")
            messages.append(f"{location}: {message}" if location else message)
        return "; ".join(messages)

    if detail:
        return str(detail)

    return payload.get("message") or f"Backend returned HTTP {response.status_code}."


def render_demo_ticket_form():
    st.subheader("Submit Demo Ticket")

    with st.form("demo_ticket_form"):
        customer_email = st.text_input("Customer Email", value="dev_ops_guy@enterprise.com")
        subject = st.text_input("Subject", value="API Webhooks failing signature verification")
        body = st.text_area(
            "Body",
            value=(
                "We updated to your latest package version, and now all incoming "
                "webhooks fail our SHA256 verification step. Did your signing key "
                "payload format change? Need documentation update or a fix."
            ),
            height=140,
        )
        submitted = st.form_submit_button("Submit Demo Ticket")

    if not submitted:
        return

    if not body.strip():
        st.error("Ticket body is required.")
        return

    payload = {
        "customer_email": customer_email.strip(),
        "subject": subject.strip(),
        "body": body.strip(),
    }
    endpoint = f"{API_BASE_URL}/api/v1/tickets/triage"

    with st.spinner("Submitting ticket through FastAPI..."):
        try:
            response = requests.post(endpoint, json=payload, timeout=60)
        except requests.exceptions.ConnectionError:
            st.error(
                f"Could not connect to FastAPI at {API_BASE_URL}. "
                "Start it with: pipenv run uvicorn app.main:app --reload"
            )
            return
        except requests.exceptions.Timeout:
            st.error("FastAPI did not respond before the request timed out.")
            return
        except requests.exceptions.RequestException as exc:
            st.error(f"Backend request failed: {exc}")
            return

    if not response.ok:
        st.error(f"Ticket submission failed: {format_api_error(response)}")
        return

    try:
        result = response.json()
    except ValueError:
        result = {}

    ticket = result.get("data") if isinstance(result, dict) else {}
    ticket_id = ticket.get("id") if isinstance(ticket, dict) else None
    if ticket_id:
        st.session_state["ticket_submit_success"] = (
            f"Ticket #{ticket_id} submitted and triaged successfully."
        )
    else:
        st.session_state["ticket_submit_success"] = "Ticket submitted and triaged successfully."

    st.rerun()


render_demo_ticket_form()
st.divider()

# 3. Fetch Data from Supabase
def fetch_tickets():
    # Fetch all tickets, ordered by newest first
    try:
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        return response.data
    except APIError as exc:
        st.error(f"Could not fetch tickets from Supabase: {exc}")
        st.stop()

tickets_data = fetch_tickets()

# 4. Render the Dashboard
if not tickets_data:
    st.info("No tickets found. Send a test ticket through your API first!")
else:
    df = pd.DataFrame(tickets_data)
    
    # KPIs / Metrics Row
    st.subheader("Live Operations Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    total_tickets = len(df)
    high_urgency = len(df[df['urgency_level'].isin(['High', 'Critical'])])
    negative = len(df[df['customer_sentiment'] == 'Negative'])
    unassigned = len(df[df['status'] == 'Unassigned'])
    
    col1.metric("Total Tickets", total_tickets)
    col2.metric("High/Critical Urgency", high_urgency)
    col3.metric("Negative Sentiment", negative)
    col4.metric("Unassigned", unassigned)
    
    st.divider()

    # The Agent View: Interactive Data Table
    st.subheader("Ticket Queue")
    
    # Reorganize columns to show the most important ML data first
    display_columns = [
        'id', 'urgency_level', 'customer_sentiment', 'predicted_category', 
        'subject', 'status', 'created_at'
    ]
    
    # Display the dataframe (Streamlit makes this sortable and filterable automatically)
    st.dataframe(df[display_columns], use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Deep Dive View
    st.subheader("🔍 Ticket Deep Dive")
    selected_id = st.selectbox("Select a Ticket ID to view details:", df['id'])
    
    if selected_id is not None:
        ticket_detail = df[df['id'] == selected_id].iloc[0]
        
        st.markdown(f"**Customer:** `{ticket_detail['customer_email']}`")
        st.markdown(f"**AI Summary:** {ticket_detail['auto_summary']}")
        st.markdown(f"**Confidence Score:** `{ticket_detail['confidence_score']} / 1.0`")
        
        with st.expander("View Original Message Body"):
            st.write(ticket_detail['body'])
