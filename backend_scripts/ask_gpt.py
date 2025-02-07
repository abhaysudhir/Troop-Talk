from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pinecone import Pinecone
from urllib.parse import unquote
import os
import uvicorn


# Hardcoded API keys and configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = "us-east-1"
INDEX_NAME = "boyscout-gpt-t125"

# Initialize OpenAI and Pinecone clients
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# Define Pinecone index
index = pc.Index(INDEX_NAME)

# Define FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allows all origins. Use a specific list for security in production.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods.
    allow_headers=["*"],  # Allows all headers.
)


def retrieve_from_pinecone(query, top_k=5):
    """
    Retrieves the most relevant documents from Pinecone based on the query.
    Includes metadata, document content, and embedding values.
    """
    try:
        # Generate query embedding using OpenAI embeddings
        embedding_response = client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        query_embedding = embedding_response.data[0].embedding

        # Query Pinecone for the top-k relevant vectors
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            include_values=True,
        )
        # print("results: " + str(results))
        # Collect combined metadata, document content, and embedding values
        contexts = []
        for match in results["matches"]:
            body = match["metadata"]["body"]
            date = match["metadata"]["date"]
            from_ = match["metadata"]["from"]
            subject = match["metadata"]["subject"]
            score = match["score"]
            contexts.append((date, from_, subject, score, body))
        # print("Contexts: " + str(contexts))
        return contexts
        # print("context " + str(contexts))
        # if not contexts:
        #     raise HTTPException(
        #         status_code=404, detail="No relevant content found in Pinecone matches."
        #     )

        # return contexts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error querying Pinecone: {str(e)}"
        )


def ask_gpt(contexts, question):
    """
    Uses GPT-3.5-turbo to answer a question based on the provided contexts.
    """
    token_limit = 12000  # Token limit for context
    prompt_start = """
    GIVE ALL ANSWERS IN MARKDOWN FORMAT. Be clear and concise.
    Answer the question based on the context below. I want whatever you say to be nice, respectful and helpful and align with scouting principles. 
    and don't say based on provided email context or anything like that.
    You are a highly specialized assistant designed to answer questions about Boy Scouts of America (BSA) programs, policies, activities, and procedures. You will be provided with the context of an email (or other documentation) and a user question. The user is either a boy scout or an adult leader.
    Your task is to:

    Interpret the email context to extract relevant information.

    Prioritize clarity and precision in your responses.

    If the answer is not explicitly in the provided email context, rely on general knowledge about Boy Scouts, including:

    1. BSA rank advancements, merit badges, and leadership roles.
    2. Campouts, service projects, and troop meetings.
    3. Adult responsibilities like organizing events, safety protocols, and guiding Scouts in leadership and Eagle projects.
    4. Youth-led principles like the patrol method, Scout leadership development, and community service.
    5. If no direct answer is available, provide general guidance and suggest next steps or resources (e.g., checking specific pages on scouting.org or contacting a council representative).

    \n\nContext:\n"""
    prompt_end = f"\n\nQuestion: {question}\nAnswer:"

    # Build the context block for the prompt
    context_block = ""
    for context in contexts:
        if (
            len(context_block) + len(context) + len(prompt_start) + len(prompt_end)
            >= token_limit
        ):
            print("Too much content for ChatGPT")
            break
        context_block += f"\n\n---\n\n{context}"

    if not context_block.strip():
        raise HTTPException(
            status_code=404,
            detail="Insufficient content to generate a meaningful answer.",
        )

    prompt = prompt_start + context_block + prompt_end
    print(f"Generated Prompt:\n{prompt}")  # Debugging/logging

    # Generate the answer from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert scout leader. You are given a question and a context. You are to answer the question based on the context. You are to be helpful and respectful and align with scouting principles."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2000,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


@app.post("/ask")
def ask_question(
    question: str = Query(..., description="The question to ask the AI"),
    top_k: int = Query(5, description="Number of top results to retrieve"),
):
    """
    Endpoint to handle user questions and return an AI-generated answer.
    Accepts query parameters instead of JSON body.
    """
    # URL decode the question
    decoded_question = unquote(question)
    print("Decoded Question: " + decoded_question)
    # Step 1: Retrieve relevant documents from Pinecone
    documents = retrieve_from_pinecone(decoded_question, top_k)

    if not documents:
        raise HTTPException(
            status_code=404, detail="No relevant documents found in Pinecone."
        )

    # Step 2: Ask GPT with the combined content
    if any(documents):  # Ensure at least one document has content
        answer = ask_gpt(documents, decoded_question)
        print(answer)
        return {"question": decoded_question, "answer": answer}
    else:
        raise HTTPException(
            status_code=404,
            detail="No content could be extracted from the retrieved documents.",
        )


# Run the application
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8080)
