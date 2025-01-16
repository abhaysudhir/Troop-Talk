from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from svix.webhooks import Webhook, WebhookVerificationError
import json

# Load environment variables
load_dotenv()

app = FastAPI()

# Get environment variables
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")

if not CLERK_SECRET_KEY or not CLERK_WEBHOOK_SECRET:
    raise ValueError("Missing required environment variables")

@app.post("/webhook/signup")
async def handle_signup_webhook(request: Request):
    try:
        # Get and validate required headers
        required_headers = ["svix-id", "svix-timestamp", "svix-signature"]
        headers = {}
        for header in required_headers:
            value = request.headers.get(header)
            if not value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required header: {header}"
                )
            headers[header] = value
        
        # Debug logging
        print("=== Webhook Debug Info ===")
        print(f"WEBHOOK_SECRET (first 10 chars): {CLERK_WEBHOOK_SECRET[:10]}...")
        print(f"Headers received: {dict(request.headers)}")
        print(f"Parsed headers: {headers}")
        
        # Get the raw body
        body = await request.body()
        body_str = body.decode()
        print(f"Raw body: {body_str[:100]}...") # First 100 chars
        
        # Initialize the Svix webhook instance with our secret
        wh = Webhook(CLERK_WEBHOOK_SECRET)
        
        try:
            # Verify the webhook
            wh.verify(body_str, headers)
        except WebhookVerificationError as e:
            print(f"Webhook verification failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid signature: {str(e)}")

        webhook_data = json.loads(body)
        
        if webhook_data.get("type") != "user.created":
            return {"status": "ignored", "message": "Not a user.created event"}

        user_data = webhook_data["data"]
        email = user_data["email_addresses"][0]["email_address"]
        org_id = user_data["unsafe_metadata"]["requestedTroopId"]

        form_data = {
            'email_address': email,
            'organization_id': org_id,
            'role': 'org:guest',
        }

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
    uvicorn.run(app, host="0.0.0.0", port=8080)
