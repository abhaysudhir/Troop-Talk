from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import hmac
import hashlib
import uvicorn
import json

# Load environment variables
load_dotenv()

app = FastAPI()

# Get environment variables
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")

if not CLERK_SECRET_KEY or not CLERK_WEBHOOK_SECRET:
    raise ValueError("Missing required environment variables")

def verify_clerk_webhook(signature_header: str, timestamp: str, body: bytes) -> bool:
    """Verify that the webhook request came from Clerk"""
    try:
        print("=== Debug Verification ===")
        print(f"Raw signature header: {signature_header}")
        print(f"Timestamp: {timestamp}")
        print(f"Raw body: {body.decode()}")
        
        # The signature header format is "v1,<signature>"
        version, signature = signature_header.split(',')
        if version != 'v1':
            print(f"Unsupported version: {version}")
            return False
            
        # Construct the message as timestamp + "." + body
        message = f"{timestamp}.{body.decode()}"
        print(f"Constructed message: {message[:100]}...") # Print first 100 chars
        
        # Compute HMAC
        computed = hmac.new(
            CLERK_WEBHOOK_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        # Base64 encode the computed signature
        import base64
        computed_b64 = base64.b64encode(computed).decode()
        
        print(f"Comparing signatures:")
        print(f"Computed (base64): {computed_b64}")
        print(f"Received: {signature}")
        
        return hmac.compare_digest(computed_b64, signature)
        
    except Exception as e:
        print(f"Verification error: {str(e)}")
        return False

@app.post("/webhook/signup")
async def handle_signup_webhook(request: Request):
    try:
        print("=== New Webhook Request ===")
        print("Headers received:", dict(request.headers))
        
        # Get the required headers
        signature = request.headers.get("svix-signature")
        timestamp = request.headers.get("svix-timestamp")
        
        if not signature or not timestamp:
            raise HTTPException(status_code=400, detail="Missing required headers")
        
        # Get the raw body
        body = await request.body()
        
        if not verify_clerk_webhook(signature, timestamp, body):
            raise HTTPException(status_code=401, detail="Invalid signature")

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
