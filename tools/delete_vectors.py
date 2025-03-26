import os
import time
import datetime
from pinecone import Pinecone
from dotenv import load_dotenv

# Define the list of vector IDs to delete here
VECTOR_IDS_TO_DELETE = [
    "T125-Jan21-Agenda-chunk1",
    
    # [T125] New Eagle rank application.eml
    "T125-EagleApp-chunk1",
    "T125-EagleApp-chunk2",
    
    # [T125] Coyote Hills Biking.eml
    "T125-CoyoteHills-chunk1", 
    "T125-CoyoteHills-chunk2",
    "T125-CoyoteHills-chunk3",
    
    # [T125] January 14th Troop Meeting Agenda.eml
    "T125-Jan14-Agenda-chunk1",
    
    # Feb 4th Troop Meeting Agenda.eml
    "Feb4-Agenda-chunk1",
    
    # [T125] January 2025 SMC.eml
    "T125-JanSMC-chunk1",
    
    # [T125] Trash Cleanup Service Opportunity.eml
    "T125-TrashCleanup-chunk1",
    "T125-TrashCleanup-chunk2",
    
    # [T125] Fwd_ 2024 GGAC Silver Beaver Awardees.eml
    "T125-SilverBeaver-chunk1",
    "T125-SilverBeaver-chunk2", 
    "T125-SilverBeaver-chunk3",
    "T125-SilverBeaver-chunk4",
    "T125-SilverBeaver-chunk5",
    
    # [T125] Re_ Merit Badge - Sustainability (Session 2) (1).eml
    "T125-Sustainability2-1-chunk1",
    "T125-Sustainability2-1-chunk2",
    "T125-Sustainability2-1-chunk3",
    
    # Feb 18th Troop Meeting Agenda.eml
    "Feb18-Agenda-chunk1",
    
    # [T125] Indoor Rally (2).eml
    "T125-IndoorRally2-chunk1",
    
    # [T125] Fwd_ MISSION PEAK DISTRICT Earth Day Activity.eml
    "T125-EarthDay-chunk1",
    "T125-EarthDay-chunk2",
    
    # [T125] Indoor Rally.eml
    "T125-IndoorRally-chunk1",
    "T125-IndoorRally-chunk2",
    
    # [T125] Merit Badge Extravaganza.eml
    "T125-MBExtravaganza-chunk1",
    "T125-MBExtravaganza-chunk2",
    
    # [T125] March BoR.eml
    "T125-MarBoR-chunk1",
    
    # [T125] Re_ Jan BoR.eml
    "T125-JanBoR-chunk1",
    "T125-JanBoR-chunk2",
    
    # [T125] Fwd_ Troop 125 Recruitment Night on 1_28 7 PM.eml
    "T125-Recruitment-chunk1",
    "T125-Recruitment-chunk2",
    
    # [T125] Check Merit badges pre requisites for Extravaganza.eml
    "T125-MBPrereqs-chunk1",
    
    # [T125] Merit Badge - Sustainability (Session 1).eml
    "T125-Sustainability1-chunk1",
    "T125-Sustainability1-chunk2",
    
    # [T125] Service opportunity.eml
    "T125-ServiceOpp-chunk1",
    
    # [T125] Re_ Merit Badge - Sustainability (Session 2).eml
    "T125-Sustainability2-chunk1",
    "T125-Sustainability2-chunk2",
    
    # [T125] From Sriman Jayanti - Lyrics for Taps.eml
    "T125-TapsLyrics-chunk1",
    
    # [T125] Re_ Court of Honor (COH) on March 25.eml
    "T125-COH-Mar25-chunk1",
    "T125-COH-Mar25-chunk2",
    "T125-COH-Mar25-chunk3",
    
    # [T125] March 2025 SMC Results.eml
    "T125-MarSMCResults-chunk1",
    
    # [T125] Troop Meeting drop off and pick up times_ground rules.eml
    "T125-GroundRules-chunk1",
    
    # [T125] Summer Camp 2025.eml
    "T125-SummerCamp-chunk1",
    "T125-SummerCamp-chunk2",
    "T125-SummerCamp-chunk3",
    
    # [T125] BSA Troop 125 Dues 2025.eml (partial upload)
    "T125-Dues2025-chunk1"
]

# Pinecone namespace to use
NAMESPACE = "Troop 125"

def main():
    load_dotenv()
    print("\n" + "="*80)
    print(f"PINECONE VECTOR DELETION SCRIPT STARTED: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # API keys and configurations
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV = "us-east-1"
    PINECONE_NAMESPACE = NAMESPACE

    print("\nCONFIGURATION:")
    print(f"Pinecone API Key: {'✓ Found' if PINECONE_API_KEY else '✗ Missing'}")
    print(f"Pinecone Environment: {PINECONE_ENV}")
    print(f"Pinecone Namespace: {PINECONE_NAMESPACE}")

    if not PINECONE_API_KEY:
        print("✗ Error: Pinecone API key is required. Please set the PINECONE_API_KEY environment variable.")
        exit(1)

    # Get vector IDs to delete
    vector_ids = VECTOR_IDS_TO_DELETE
    
    if not vector_ids:
        print("✗ Error: No vector IDs specified. Please add vector IDs to the VECTOR_IDS_TO_DELETE list.")
        exit(1)
    
    print(f"\nUsing {len(vector_ids)} predefined vector IDs")

    # Connect to Pinecone
    print("\nINITIALIZING PINECONE CLIENT...")
    try:
        pinecone_client = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        print("✓ Pinecone client initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing Pinecone client: {e}")
        exit(1)

    # Set up Pinecone index
    INDEX_NAME = "boyscout-gpt-t125"
    print(f"\nCONNECTING TO PINECONE INDEX: {INDEX_NAME}")
    try:
        index = pinecone_client.Index(INDEX_NAME)
        print(f"✓ Successfully connected to Pinecone index '{INDEX_NAME}'")
    except Exception as e:
        print(f"✗ Error connecting to Pinecone index: {e}")
        exit(1)

    # Process vectors in batches
    BATCH_SIZE = 100  # Adjust based on Pinecone rate limits
    total_vectors = len(vector_ids)
    deleted_count = 0
    error_count = 0
    start_time = time.time()

    print(f"\nDELETING {total_vectors} VECTORS FROM NAMESPACE '{PINECONE_NAMESPACE}'")
    
    for i in range(0, total_vectors, BATCH_SIZE):
        batch = vector_ids[i:i + BATCH_SIZE]
        batch_size = len(batch)
        batch_start_time = time.time()
        
        print(f"\nBatch {i//BATCH_SIZE + 1}/{(total_vectors + BATCH_SIZE - 1)//BATCH_SIZE}: Processing {batch_size} vectors")
        
        try:
            index.delete(ids=batch, namespace=PINECONE_NAMESPACE)
            batch_time = time.time() - batch_start_time
            deleted_count += batch_size
            print(f"✓ Successfully deleted batch in {batch_time:.2f} seconds")
            print(f"  Progress: {deleted_count}/{total_vectors} vectors deleted ({deleted_count/total_vectors*100:.1f}%)")
            
            # Add a small delay to avoid rate limiting
            if i + BATCH_SIZE < total_vectors:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error deleting batch: {e}")
            print(f"  Failed IDs in this batch: {batch}")
            error_count += batch_size

    total_time = time.time() - start_time
    print("\n" + "="*80)
    print("DELETION SUMMARY")
    print("="*80)
    print(f"Total vectors processed: {total_vectors}")
    print(f"Successfully deleted: {deleted_count}")
    print(f"Errors: {error_count}")
    print(f"Namespace: {PINECONE_NAMESPACE}")
    print(f"Total processing time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    
    if deleted_count > 0:
        print(f"Average time per vector: {total_time/deleted_count:.4f} seconds")
    
    print(f"Success rate: {deleted_count/total_vectors*100:.1f}% ({deleted_count}/{total_vectors})")
    print("="*80)
    print(f"SCRIPT COMPLETED: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main() 