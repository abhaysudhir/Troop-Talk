const historyContainer = document.getElementById("history-container");

async function submitPrompt() {
    const promptInput = document.getElementById("prompt-input");
    const promptText = promptInput.value.trim();
    console.log("Check Prompt");
    if (!promptText) {
        alert("Please enter a prompt.");
        return;
    }

    // Clear the input field
    promptInput.value = "";

    try {
        // Send a POST request to the API
        const response = await fetch(
            "http://0.0.0.0:8080/ask?question=" +
                encodeURIComponent(promptText) +
                "&top_k=3",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            }
        );
        console.log(response);
        // Parse the JSON response
        const responseData = await response.json();

        // Extract the "answer" field from the response
        console.log("Response" + responseData);
        const answer = responseData.answer || "No answer provided.";

        // Add the prompt and response to the history
        addToHistory(promptText, answer);
    } catch (error) {
        console.error("Error fetching the response:", error);
        addToHistory(
            promptText,
            "Error: Unable to fetch response from the server."
        );
    }
}

function addToHistory(prompt, response) {
    const historyItem = document.createElement("div");
    historyItem.className = "history-item";

    const promptElement = document.createElement("div");
    promptElement.className = "prompt";
    promptElement.textContent = `Prompt: ${prompt}`;

    const responseElement = document.createElement("div");
    responseElement.className = "response";
    responseElement.textContent = `Response: ${response}`;

    historyItem.appendChild(promptElement);
    historyItem.appendChild(responseElement);
    historyContainer.appendChild(historyItem);
}
