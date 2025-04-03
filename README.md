# Goal
The aim of this project is to create a chat interface that will allow people to talk to their scout emails

- [x] Initialize & Setup Git & Venv
- [x] Create exporting emails to pinecone script (Current Supported Filetypes: .pdf, .docx, .xlsx)
- [x] Create Asking ChatGPT
- [x] Host on Digital Ocean

Problems
- [x] Unable to mass export emails (SOLVED USING Gscripts)
- [x] Too many tokens for ChatGPT to process

Current Pincone Context Window: 03/08/2025 - 3/22/2025 -- All emails sent to whole troop
Last Date of BSA Website Scraping: 03/25/2025
Last Date of T125 Website Scraping: 03/26/2025

troop-talk-website is a submodule now
branch that will be used will be `official-branch` 

## For troop-talk-website
# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev

Possibly using an AI crawler to scrape emails from google groups?

- [ ] Send emails to higher ups in Boy Scouts to partner with them
Ozzie suggested that we can use it for Boy Scouts but also expand to Church Groups, YMCA, etc.

Talking to Mr. Putt about possibly partnering up.
Advertising in Scout Life Magazine
- [x] Using Gemini 2.0 API for chatbot -- 2million token context window + cheaper

Changed to using Deepseek V3 from OpenRouter