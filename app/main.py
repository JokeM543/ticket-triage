from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from .ml_engine import triage_incoming_ticket
from .database import supabase

app = FastAPI(title="Intelligent Triage Engine API", version="1.0")

# Request validation schema for incoming tickets
class TicketSubmission(BaseModel):
    customer_email: EmailStr
    subject: str
    body: str

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Triage Engine API is live."}

@app.post("/api/v1/tickets/triage")
def triage_and_store_ticket(ticket: TicketSubmission):
    # 1. Run the ML inference engine on the ticket body
    try:
        ml_analysis = triage_incoming_ticket(ticket.body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Inference failed: {str(e)}")

    # 2. Prepare the payload matching our Supabase schema
    db_payload = {
        "customer_email": ticket.customer_email,
        "subject": ticket.subject,
        "body": ticket.body,
        "predicted_category": ml_analysis.category,
        "confidence_score": ml_analysis.confidence,
        "urgency_level": ml_analysis.urgency,
        "customer_sentiment": ml_analysis.sentiment,
        "auto_summary": ml_analysis.summary,
        "status": "Unassigned"
    }

    # 3. Insert into Supabase
    try:
        response = supabase.table("tickets").insert(db_payload).execute()
        return {
            "success": True,
            "message": "Ticket parsed and saved successfully.",
            "data": response.data[0] if response.data else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")