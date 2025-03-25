import os
import email
import time
import datetime
import tiktoken
from email.policy import default
from PyPDF2 import PdfReader
import docx
import openpyxl
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
print("\n" + "="*80) 
print(f"UPLOAD-ONLY SCRIPT STARTED: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# API keys and configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = "us-east-1"
PINECONE_NAMESPACE = "Troop 125"

print("\nCONFIGURATION:")
print(f"OpenAI API Key: {'✓ Found' if OPENAI_API_KEY else '✗ Missing'}")
print(f"Pinecone API Key: {'✓ Found' if PINECONE_API_KEY else '✗ Missing'}")
print(f"Pinecone Environment: {PINECONE_ENV}")
print(f"Pinecone Namespace: {PINECONE_NAMESPACE}")

# Initialize OpenAI and Pinecone
print("\nINITIALIZING CLIENTS...")
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✓ OpenAI client initialized successfully")
except Exception as e:
    print(f"✗ Error initializing OpenAI client: {e}")
    exit(1)

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

# Directory for already cleaned files
CLEANED_DIR = "Cleaned_Emails"
print(f"\nDIRECTORY:")
print(f"Input directory (already cleaned files): {os.path.abspath(CLEANED_DIR)}")

if not os.path.exists(CLEANED_DIR):
    print(f"✗ Input directory '{CLEANED_DIR}' does not exist!")
    exit(1)
else:
    print(f"✓ Input directory exists")
    file_count = len([f for f in os.listdir(CLEANED_DIR) if os.path.isfile(os.path.join(CLEANED_DIR, f))])
    print(f"  Found {file_count} files in input directory")

# Function to chunk text
def chunk_text(text, chunk_size=400):
    """
    Split text into chunks of approximately chunk_size tokens.
    Ensures splits occur at sentence or paragraph boundaries when possible.
    
    Args:
        text (str): The text to split into chunks
        chunk_size (int): Target number of tokens per chunk (default 400)
    
    Returns:
        list: List of text chunks
    """
    print(f"  Chunking text of {len(text)} characters into ~{chunk_size} token chunks")
    start_time = time.time()
    
    # Initialize tokenizer
    enc = tiktoken.encoding_for_model("text-embedding-ada-002")
    
    # First split by double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for paragraph in paragraphs:
        # If paragraph is empty, skip it
        if not paragraph.strip():
            continue
            
        # Get token count for this paragraph
        paragraph_tokens = len(enc.encode(paragraph))
        
        # If a single paragraph is too large, split it by sentences
        if paragraph_tokens > chunk_size:
            sentences = [s.strip() for s in paragraph.replace('\n', ' ').split('. ')]
            for sentence in sentences:
                if not sentence:
                    continue
                sentence_tokens = len(enc.encode(sentence))
                
                # If adding this sentence would exceed chunk size, start a new chunk
                if current_token_count + sentence_tokens > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_token_count = 0
                
                current_chunk.append(sentence + '.')
                current_token_count += sentence_tokens
        else:
            # If adding this paragraph would exceed chunk size, start a new chunk
            if current_token_count + paragraph_tokens > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_token_count = 0
            
            current_chunk.append(paragraph)
            current_token_count += paragraph_tokens
    
    # Add any remaining text as the last chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    print(f"  ✓ Created {len(chunks)} chunks in {time.time() - start_time:.2f} seconds")
    for i, chunk in enumerate(chunks):
        chunk_tokens = len(enc.encode(chunk))
        print(f"    Chunk {i+1}: {chunk_tokens} tokens, {len(chunk)} chars")
    
    return chunks

# Function to generate embeddings
def embed_text(text):
    print(f"  Generating embedding for text ({len(text)} characters)")
    start_time = time.time()
    
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002", input=text
        )
        embedding = response.data[0].embedding
        vector_dim = len(embedding)
        print(f"  ✓ Embedding generated successfully: {vector_dim} dimensions in {time.time() - start_time:.2f} seconds")
        print(f"  Vector sample (first 5 values): {embedding[:5]}")
        return embedding
    except Exception as e:
        print(f"  ✗ Error generating embedding: {e}")
        raise

# Process and upload files
print("\n" + "="*80)
print("STARTING UPLOAD OF PRE-CLEANED FILES")
print("="*80)

file_count = len([f for f in os.listdir(CLEANED_DIR) if f.endswith(".txt")])
print(f"Found {file_count} .txt files to upload")

processed_count = 0
success_count = 0
error_count = 0
start_time_all = time.time()

for filename in os.listdir(CLEANED_DIR):
    if filename.endswith(".txt"):
        processed_count += 1
        print(f"\n[{processed_count}/{file_count}] Processing: {filename}")
        file_start_time = time.time()
        file_path = os.path.join(CLEANED_DIR, filename)
        
        try:
            # Extract basic metadata from filename
            base_name = os.path.splitext(filename)[0]
            
            # Read the file content
            print(f"  Reading file for upload")
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
            print(f"  ✓ Read {len(text)} characters from file")
            
            # Try to extract metadata from the file content
            # Assuming the first few lines might contain metadata like Subject, From, Date
            lines = text.split('\n', 10)
            
            subject = base_name  # Default to filename
            sender = "Unknown"
            date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            
            # Try to extract metadata from file content if available
            for line in lines[:10]:  # Check first 10 lines for metadata
                if line.startswith("Subject:"):
                    subject = line[8:].strip()
                elif line.startswith("From:"):
                    sender = line[5:].strip()
                elif line.startswith("Date:"):
                    date = line[5:].strip()
            
            print(f"  File metadata:")
            print(f"    Subject: {subject}")
            print(f"    From: {sender}")
            print(f"    Date: {date}")

            try:
                print(f"  Generating embeddings and uploading chunks to Pinecone")
                chunks = chunk_text(text)
                
                # Prepare base metadata
                base_metadata = {
                    "subject": subject, 
                    "from": sender, 
                    "date": date,
                    "filename": filename,
                    "processed_at": datetime.datetime.now().isoformat()
                }
                
                # Process and upload each chunk
                upload_start = time.time()
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{filename}_chunk_{i+1}"
                    embedding = embed_text(chunk)
                    
                    # Add chunk-specific metadata
                    chunk_metadata = {
                        **base_metadata,
                        "chunk_index": i + 1,
                        "total_chunks": len(chunks),
                        "chunk_text": chunk
                    }
                    
                    index.upsert(
                        vectors=[(chunk_id, embedding, chunk_metadata)],
                        namespace=PINECONE_NAMESPACE
                    )
                    print(f"  ✓ Uploaded chunk {i+1}/{len(chunks)}")
                
                print(f"  ✓ Successfully uploaded all chunks to Pinecone in {time.time() - upload_start:.2f} seconds")
                
                success_count += 1
                print(f"  ✓ COMPLETE: Processed {filename} in {time.time() - file_start_time:.2f} seconds")
            except Exception as e:
                print(f"  ✗ ERROR: Failed to process or upload {filename}")
                print(f"  Error details: {str(e)}")
                print(f"  Error type: {type(e).__name__}")
                error_count += 1
        except Exception as e:
            print(f"  ✗ CRITICAL ERROR processing {filename}: {e}")
            error_count += 1

total_time = time.time() - start_time_all
print("\n" + "="*80)
print("PROCESSING SUMMARY")
print("="*80)
print(f"Total files processed: {processed_count}")
print(f"Successfully processed: {success_count}")
print(f"Errors: {error_count}")
print(f"Total processing time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
if processed_count > 0:
    print(f"Average time per file: {total_time/processed_count:.2f} seconds")
print(f"Success rate: {success_count/processed_count*100:.1f}% ({success_count}/{processed_count})")
print("="*80)
print(f"SCRIPT COMPLETED: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
