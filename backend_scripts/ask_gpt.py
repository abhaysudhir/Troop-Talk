from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pinecone import Pinecone
from urllib.parse import unquote
import os
import uvicorn
from openai import OpenAI
import dotenv
import asyncio

dotenv.load_dotenv()
# API keys and configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # For embeddings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_ENV = "us-east-1"
INDEX_NAME = "boyscout-gpt-t125"

# Query configurations
TROOP_TOP_K = 45  # Fixed value for Troop 125 namespace
BSA_TOP_K = 30    # Fixed value for BSA Website Data namespace
RANK_MB_TOP_K = 10  # Fixed value for Rank Requirements & Merit Badge Info namespace

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)  # For embeddings only
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# Define Pinecone index
index = pc.Index(INDEX_NAME)

# Define FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared system prompt for both streaming and non-streaming functions
SYSTEM_PROMPT = """You are an expert scout leader and BSA knowledge specialist, specifically focused on Troop 125. Your primary role is to provide accurate, helpful, and well-structured information about Troop 125's programs, policies, and procedures, supplemented by relevant BSA guidelines and official rank and merit badge requirements.
Give all answers in markdown format. This is not an email so don't include an email signature, use Notes only when required
Make sure to keep answers concise and to the point.
Key Responsibilities:
1. Prioritize Troop-specific information over general BSA guidelines
2. Provide clear, concise answers in markdown format
3. Always maintain a respectful, encouraging tone aligned with Scouting values
4. Prioritize accuracy and safety in all responses
5. Directly address the user's question without unnecessary information

When answering questions:
- Start with Troop-specific information when available
- For questions about rank requirements or merit badges, use the official BSA requirements from the Rank Requirements & Merit Badge Info namespace
- Fall back to BSA guidelines when Troop 125 information is not available
- Use bullet points or numbered lists for multiple steps or options
- Include relevant BSA policy references when applicable
- Provide practical examples when helpful
- Keep responses focused and concise

Knowledge Areas to Draw From (in order of priority):
1. Troop 125 Specific Information
   - Troop policies and procedures
   - Local event schedules and requirements
   - Troop-specific advancement processes
   - Unit-specific leadership roles and responsibilities

2. Official Rank Requirements & Merit Badge Information
   - Current rank requirements (Scout, Tenderfoot, Second Class, First Class, Star, Life, Eagle)
   - Merit badge requirements and procedures
   - Eagle-required merit badges
   - Eagle Scout process

3. BSA Program Structure
   - Rank advancements and requirements
   - Merit badges and their requirements
   - Leadership positions and responsibilities
   - Eagle Scout process and requirements

4. Troop Operations
   - Meeting planning and execution
   - Campout organization and safety
   - Service project coordination
   - Fundraising activities

5. Scouting Principles
   - Scout Oath and Law
   - Youth-led leadership
   - Patrol method
   - Leave No Trace principles

6. Adult Leadership
   - Safety protocols and guidelines
   - Event planning and risk management
   - Youth protection policies
   - Advancement tracking

If the specific answer isn't in the provided context:
1. First check if there's any Troop-specific guidance
2. If not, provide general guidance based on BSA standards
3. Suggest consulting with Troop leadership for specific details
4. Recommend relevant BSA resources or documentation
5. Offer to clarify or expand on any part of the response"""

def retrieve_from_troop125(query, top_k=15):
    """
    Retrieves the most relevant documents from Pinecone's "Troop 125" namespace.
    """
    try:
        # Generate query embedding using OpenAI embeddings
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        query_embedding = embedding_response.data[0].embedding

        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            include_values=True,
            namespace="Troop 125"
        )
        
        contexts = []
        for match in results["matches"]:
            # Check for both old and new metadata formats
            if "body" in match["metadata"]:
                body = match["metadata"]["body"]
            elif "chunk_text" in match["metadata"]:
                body = match["metadata"]["chunk_text"]
            else:
                # Skip if neither key exists
                print(f"Warning: Document missing both 'body' and 'chunk_text' fields. Available keys: {match['metadata'].keys()}")
                continue
                
            date = match["metadata"]["date"]
            from_ = match["metadata"]["from"]
            subject = match["metadata"]["subject"]
            score = match["score"]
            contexts.append((date, from_, subject, score, body))
        return contexts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error querying Pinecone Troop 125 namespace: {str(e)}"
        )

def retrieve_from_bsa_website(query, top_k=10):
    """
    Retrieves the most relevant documents from Pinecone's "BSA Website Data" namespace.
    """
    try:
        # Generate query embedding using OpenAI embeddings
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        query_embedding = embedding_response.data[0].embedding

        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            include_values=True,
            namespace="BSA Website Data"
        )
        
        contexts = []
        for match in results["matches"]:
            # Check for both old and new metadata formats
            if "body" in match["metadata"]:
                body = match["metadata"]["body"]
            elif "chunk_text" in match["metadata"]:
                body = match["metadata"]["chunk_text"]
            else:
                # Skip if neither key exists
                print(f"Warning: Document missing both 'body' and 'chunk_text' fields. Available keys: {match['metadata'].keys()}")
                continue
                
            date = match["metadata"]["date"]
            from_ = match["metadata"]["from"]
            subject = match["metadata"]["subject"]
            score = match["score"]
            contexts.append((date, from_, subject, score, body))
        return contexts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error querying Pinecone BSA Website Data namespace: {str(e)}"
        )

def retrieve_from_rank_mb_info(query, top_k=10):
    """
    Retrieves the most relevant documents from Pinecone's "Rank Requirements & Merit Badge Info" namespace.
    """
    try:
        # Generate query embedding using OpenAI embeddings
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        query_embedding = embedding_response.data[0].embedding

        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            include_values=True,
            namespace="Rank Requirements & Merit Badge Info"
        )
        
        contexts = []
        for match in results["matches"]:
            # Handle the metadata fields specific to this namespace
            # Expected fields: id, body, date, filename, from, processed_at, subject
            if "body" in match["metadata"]:
                body = match["metadata"]["body"]
            else:
                # Skip if body doesn't exist
                print(f"Warning: Document missing 'body' field. Available keys: {match['metadata'].keys()}")
                continue
                
            date = match["metadata"].get("date", "No Date")
            from_ = match["metadata"].get("from", "Official BSA Requirements")
            subject = match["metadata"].get("subject", match["metadata"].get("filename", "Requirements Document"))
            score = match["score"]
            
            # Add document ID for better traceability
            doc_id = match["metadata"].get("id", "Unknown ID")
            body = f"Document ID: {doc_id}\n\n{body}"
            
            contexts.append((date, from_, subject, score, body))
        return contexts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error querying Pinecone Rank Requirements & Merit Badge Info namespace: {str(e)}"
        )

# Helper function to format contexts into a string
def format_contexts(contexts):
    return "\n\n---\n\n".join([
        f"Date: {date}\nFrom: {from_}\nSubject: {subject}\nRelevance: {score:.4f}\n\n{body}"
        for date, from_, subject, score, body in contexts
    ])

async def ask_deepseek_stream(contexts, question):
    """
    Uses Deepseek model through OpenRouter to answer a question based on the provided contexts.
    Returns a streaming response.
    """
    # Format contexts into a single string
    context_text = format_contexts(contexts)

    try:
        stream = openrouter_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "troop125.org",  # Site URL for rankings on openrouter.ai
                "X-Title": "Troop 125 Scout Assistant",  # Site title for rankings on openrouter.ai
            },
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}\n\nProvide a clear, helpful answer in markdown format:"}
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)  # Print content as it streams without newlines
                yield content
    except Exception as e:
        print(f"Error from Deepseek model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@app.post("/ask")
async def ask_question(
    question: str = Query(..., description="The question to ask the AI"),
):
    """
    Endpoint to handle user questions and return an AI-generated answer with streaming.
    """
    decoded_question = unquote(question)
    print("Decoded Question: " + decoded_question)
    
    # Retrieve documents from all namespaces
    troop_documents = retrieve_from_troop125(decoded_question, TROOP_TOP_K)
    bsa_documents = retrieve_from_bsa_website(decoded_question, BSA_TOP_K)
    rank_mb_documents = retrieve_from_rank_mb_info(decoded_question, RANK_MB_TOP_K)
    
    # Print document counts for debugging
    print(f"Retrieved {len(troop_documents)} documents from Troop 125 namespace")
    print(f"Retrieved {len(bsa_documents)} documents from BSA Website Data namespace")
    print(f"Retrieved {len(rank_mb_documents)} documents from Rank Requirements & Merit Badge Info namespace")
    
    # Log some info about the top documents from each source if available
    if troop_documents:
        print(f"Top Troop document: {troop_documents[0][2]} (Score: {troop_documents[0][3]:.4f})")
    if bsa_documents:
        print(f"Top BSA document: {bsa_documents[0][2]} (Score: {bsa_documents[0][3]:.4f})")
    if rank_mb_documents:
        print(f"Top Rank/MB document: {rank_mb_documents[0][2]} (Score: {rank_mb_documents[0][3]:.4f})")
    
    # Combine the documents
    all_documents = troop_documents + bsa_documents + rank_mb_documents
    print(f"Total documents retrieved: {len(all_documents)}")
    
    if not all_documents:
        raise HTTPException(
            status_code=404, detail="No relevant documents found in Pinecone."
        )

    if any(all_documents):
        # Return a streaming response
        return StreamingResponse(
            ask_deepseek_stream(all_documents, decoded_question),
            media_type="text/plain"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="No content could be extracted from the retrieved documents.",
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)