from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import hmac
import hashlib
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

# Get environment variables
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")

if not CLERK_SECRET_KEY or not CLERK_WEBHOOK_SECRET:
    raise ValueError("Missing required environment variables")

def verify_clerk_webhook(signature: str, body: bytes) -> bool:
    """Verify that the webhook request came from Clerk"""
    computed_signature = hmac.new(
        CLERK_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)

@app.post("/webhook/signup")
async def handle_signup_webhook(request: Request):
    # Verify the webhook signature
    signature = request.headers.get("svix-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature header")
    
    # Get the raw body
    body = await request.body()
    if not verify_clerk_webhook(signature, body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse the webhook data
    webhook_data = await request.json()
    
    # Make sure it's a user.created event
    if webhook_data.get("type") != "user.created":
        return {"status": "ignored", "message": "Not a user.created event"}

    try:
        user_data = webhook_data["data"]
        email = user_data["email_addresses"][0]["email_address"]
        org_id = user_data["unsafe_metadata"]["requestedTroopId"]

        # Create form data for the invitation
        form_data = {
            'email_address': email,
            'organization_id': org_id,
            'role': 'org:guest',
            'redirect_url': os.getenv('APP_URL', 'http://localhost:8080') + '/pending-approval'
        }

        # Send invitation using Clerk's API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.clerk.com/v1/organizations/{org_id}/invitations",
                data=form_data,
                headers={
                    'Authorization': f'Bearer {CLERK_SECRET_KEY}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            if response.status_code != 200:
                print(f"Error from Clerk API: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to send organization invitation")

            return {"status": "success", "message": "Organization invitation sent successfully"}

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
