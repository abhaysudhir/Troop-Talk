# TroopTalk by Abhay Sudhir

## Goal
The aim of this project is to create a chat interface that will allow people to talk to their scout emails

## Information Updates
Current Pincone Context Window: 03/08/2025 - 3/22/2025 -- All emails sent to whole troop  
Last Date of BSA Website Scraping: 03/25/2025  
Last Date of T125 Website Scraping: 03/26/2025  

## Organization Structure
Troop-Talk - Main Repostiory  
* Backend Scripts
* Tools
    - `delete_vectors.py` - Python Script to delete Pinecone vectors by ID (with bulk support)
    - `download_emails.js` - GScript code that is hosted on [Google Scripts](https://script.google.com/home/projects/1p7LWD4aCjja0W3SjvDLOeXEfIyH_YPf3nxa8xoMImBszRJHTpxUKwaUp/edit?pli=1), allows for scraping Email data between a range of dates from a Google Group
    
troop-talk-website - Submodule of Troop-Talk

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