#!/usr/bin/env python3
import requests
import os
import argparse
import json
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
logger.debug("Loading environment variables")
load_dotenv()

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
logger.debug(f"CLERK_SECRET_KEY found: {bool(CLERK_SECRET_KEY)}")
if CLERK_SECRET_KEY:
    logger.debug(f"CLERK_SECRET_KEY starts with: {CLERK_SECRET_KEY[:5]}...")

if not CLERK_SECRET_KEY:
    logger.error("CLERK_SECRET_KEY environment variable is missing")
    raise ValueError("CLERK_SECRET_KEY environment variable is required")

def get_user_details(user_id):
    """
    Get complete user details from Clerk API
    """
    logger.debug(f"Getting details for user: {user_id}")
    url = f"https://api.clerk.com/v1/users/{user_id}"
    
    headers = {
        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    logger.debug(f"Making API request to: {url}")
    logger.debug(f"Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer XXXX' for k, v in headers.items()})}")
    
    try:
        response = requests.get(url, headers=headers)
        logger.debug(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Error response: {response.text}")
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        
        user_data = response.json()
        logger.debug(f"Successfully retrieved user data. User ID: {user_data.get('id')}")
        return user_data
    
    except Exception as e:
        logger.exception(f"Exception during API request: {str(e)}")
        print(f"Error making request: {str(e)}")
        return None

def get_user_organizations(user_id):
    """
    Get all organizations a user belongs to
    """
    logger.debug(f"Getting organizations for user: {user_id}")
    url = f"https://api.clerk.com/v1/users/{user_id}/organization_memberships"
    
    headers = {
        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    logger.debug(f"Making API request to: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        logger.debug(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Error response: {response.text}")
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        
        org_data = response.json()
        org_count = len(org_data.get('data', []))
        logger.debug(f"Found {org_count} organization(s) for user")
        return org_data
    
    except Exception as e:
        logger.exception(f"Exception during API request: {str(e)}")
        print(f"Error making request: {str(e)}")
        return None

def display_organization_info(org_memberships):
    """
    Display organization information in a readable format
    """
    logger.debug("Displaying organization information")
    
    if not org_memberships or len(org_memberships.get('data', [])) == 0:
        logger.debug("No organizations found for this user")
        print("No organizations found for this user.")
        return
    
    print("\nUser's Organization Memberships:")
    print("--------------------------------")
    
    for i, membership in enumerate(org_memberships.get('data', []), 1):
        org_id = membership.get('organization', {}).get('id', 'Unknown')
        org_name = membership.get('organization', {}).get('name', 'Unnamed Organization')
        role = membership.get('role', 'Unknown role')
        
        logger.debug(f"Organization {i}: ID={org_id}, Name={org_name}, Role={role}")
        
        print(f"{i}. Organization ID: {org_id}")
        print(f"   Name: {org_name}")
        print(f"   Role: {role}")
        print("   ------------------------")

def main():
    logger.debug("Script started")
    
    parser = argparse.ArgumentParser(description='Get a user\'s organization ID from Clerk')
    parser.add_argument('user_id', help='The Clerk user ID to look up')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')
    
    args = parser.parse_args()
    logger.debug(f"Arguments: user_id={args.user_id}, json={args.json}, verbose={args.verbose}")
    
    # Adjust logging level based on verbose flag
    if not args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    # Get user organizations
    logger.debug("Retrieving user organizations")
    org_memberships = get_user_organizations(args.user_id)
    
    if not org_memberships:
        logger.error("Failed to retrieve organization information")
        print("Failed to retrieve organization information")
        return
    
    if args.json:
        # Output as JSON
        logger.debug("Outputting results as JSON")
        print(json.dumps(org_memberships, indent=2))
    else:
        # Display in user-friendly format
        logger.debug("Displaying user-friendly output")
        display_organization_info(org_memberships)
        
        # For easy scripting, also print just the first org ID if it exists
        if org_memberships and len(org_memberships.get('data', [])) > 0:
            first_org_id = org_memberships['data'][0]['organization']['id']
            logger.debug(f"Primary organization ID: {first_org_id}")
            print(f"\nPrimary Organization ID: {first_org_id}")
    
    logger.debug("Script completed successfully")

if __name__ == "__main__":
    main() 