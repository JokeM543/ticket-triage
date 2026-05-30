import os
import instructor
from openai import OpenAI, APIError, APITimeoutError
from .schemas import TicketTriageSchema  # Importing the schema we made earlier

# Initialize client
client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

def triage_incoming_ticket(ticket_body: str) -> TicketTriageSchema:
    # 1. Edge Case: Empty or whitespace-only inputs
    if not ticket_body or not ticket_body.strip():
        return TicketTriageSchema(
            category="General Inquiry",
            urgency="Low",
            sentiment="Neutral",
            summary="System Auto-Summary: Empty ticket submitted.",
            confidence=1.0
        )

    # 2. Main ML API Call with Error Handling
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=TicketTriageSchema,
            messages=[
                {"role": "system", "content": "You are an advanced B2B customer support operations routing bot. Analyze the ticket thoroughly."},
                {"role": "user", "content": f"Ticket Body: {ticket_body}"}
            ],
            temperature=0.0,
            timeout=8.0  # Crucial: Prevent infinite hanging if OpenAI is down
        )
        return response

    # 3. Fallback for API/Network Failures
    except (APIError, APITimeoutError) as e:
        print(f"Warning: OpenAI API failed - {str(e)}")
        return TicketTriageSchema(
            category="General Inquiry",
            urgency="Medium", # Defaulting to Medium so it doesn't get lost
            sentiment="Neutral",
            summary="System Auto-Summary: Ticket ingested, but AI classification failed due to network timeout.",
            confidence=0.0
        )
        
    # 4. Fallback for generic Python crashes (e.g., Pydantic validation errors)
    except Exception as e:
        print(f"Critical Error parsing ticket: {str(e)}")
        return TicketTriageSchema(
            category="General Inquiry",
            urgency="Medium",
            sentiment="Neutral",
            summary="System Auto-Summary: Ticket ingested, but parsing failed.",
            confidence=0.0
        )
    
    
