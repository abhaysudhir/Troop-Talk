from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pinecone import Pinecone
from urllib.parse import unquote

# Hardcoded API keys and configurations
OPENAI_API_KEY = "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"
PINECONE_API_KEY = (
    "pcsk_5CwF7M_2c71gSS2ogeQnpVRd3TJWHrj69hJBVGn1uZxNqtbSkgeXXszh6Q2dDpvghvA6sF"
)
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


def retrieve_from_pinecone(query, top_k=3):
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
        print("Contexts: " + str(contexts))
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
    token_limit = 3750  # Token limit for context
    prompt_start = "Answer the question based on the context below.\n\nContext:\n"
    prompt_end = f"\n\nQuestion: {question}\nAnswer:"

    # Build the context block for the prompt
    context_block = ""
    for context in contexts:
        if (
            len(context_block) + len(context) + len(prompt_start) + len(prompt_end)
            >= token_limit
        ):
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
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=800,
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
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
