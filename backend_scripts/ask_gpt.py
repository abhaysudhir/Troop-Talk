from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone
from urllib.parse import unquote
import os
import uvicorn
from openai import OpenAI
import dotenv

dotenv.load_dotenv()
# API keys and configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # For embeddings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_ENV = "us-east-1"
INDEX_NAME = "boyscout-gpt-t125"

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

def ask_deepseek(contexts, question):
    """
    Uses Deepseek model through OpenRouter to answer a question based on the provided contexts.
    """
    system_prompt = """You are an expert scout leader. You are a highly specialized assistant designed to answer questions about Boy Scouts of America (BSA) programs, policies, activities, and procedures. Give all answers in markdown format. Be clear, concise, nice, respectful and helpful and align with scouting principles. I want all your responses to be in markdown format.
    Keep your answers condensed, short and MAKE SURE THAT IT DIRECTLY ADDRESSES THE QUESTION

If the answer is not explicitly in the provided context, rely on general knowledge about Boy Scouts, including:
1. BSA rank advancements, merit badges, and leadership roles
2. Campouts, service projects, and troop meetings
3. Adult responsibilities like organizing events, safety protocols, and guiding Scouts
4. Youth-led principles like the patrol method and leadership development
5. If no direct answer is available, provide general guidance and suggest next steps"""

    # Format contexts into a single string
    context_text = "\n\n---\n\n".join([
        f"Date: {date}\nFrom: {from_}\nSubject: {subject}\nRelevance: {score:.4f}\n\n{body}"
        for date, from_, subject, score, body in contexts
    ])

    try:
        completion = openrouter_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "troop125.org",  # Site URL for rankings on openrouter.ai
                "X-Title": "Troop 125 Scout Assistant",  # Site title for rankings on openrouter.ai
            },
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}\n\nProvide a clear, helpful answer in markdown format:"}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error from Deepseek model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@app.post("/ask")
def ask_question(
    question: str = Query(..., description="The question to ask the AI"),
):
    """
    Endpoint to handle user questions and return an AI-generated answer.
    """
    decoded_question = unquote(question)
    print("Decoded Question: " + decoded_question)
    
    # Retrieve documents from both namespaces with fixed top_k values
    troop_top_k = 15  # Fixed value for Troop 125 namespace
    bsa_top_k = 10    # Fixed value for BSA Website Data namespace
    
    # Retrieve documents from both namespaces
    troop_documents = retrieve_from_troop125(decoded_question, troop_top_k)
    bsa_documents = retrieve_from_bsa_website(decoded_question, bsa_top_k)
    
    # Combine the documents
    all_documents = troop_documents + bsa_documents
    
    if not all_documents:
        raise HTTPException(
            status_code=404, detail="No relevant documents found in Pinecone."
        )

    if any(all_documents):
        answer = ask_deepseek(all_documents, decoded_question)
        print(answer)
        return {"question": decoded_question, "answer": answer}
    else:
        raise HTTPException(
            status_code=404,
            detail="No content could be extracted from the retrieved documents.",
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)