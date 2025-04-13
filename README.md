# TroopTalk
by Abhay Sudhir

Instagram: [@trooptalk.ai](https://www.instagram.com/trooptalk.ai)
Website: [trooptalk.ai](https://trooptalk.ai)

## Goal
The aim of this project is to create a chat interface that will allow people to talk to their scout emails, providing easy access to troop information and communication.

TroopTalk Demo (Troop 2220): https://share.cleanshot.com/Kff67zV4

## Information Updates
Current Pinecone Context Window: 03/08/2025 - 3/22/2025 -- All emails sent to whole troop  
Last Date of BSA Website Scraping: 03/25/2025  
Last Date of T125 Website Scraping: 03/26/2025  

## Technologies Used
- **Backend**: Python, Node.js
- **Frontend**: Next.js, React
- **AI/ML**: Deepseek V3 (via OpenRouter), Pinecone Vector Database
- **Hosting**: DigitalOcean
- **Automation**: Google Scripts
- **Web Scraping**: Firecrawl

## Organization Structure
#### Troop-Talk - Main Repository  
* Backend Scripts
    - `ask_gpt.py` - API hosted on DigitalOcean under [TT Backend Scripts](https://cloud.digitalocean.com/apps/01757f84-58a3-427b-abeb-8f4ee99c27ad?source_ref=projects&i=f2dff9) that:
        1. Processes incoming query (sent as a POST request)
        2. Finds related Scouting information in Pinecone Database (checks for match of >=0.85, or defaults to fallback method with hardcoded top_k values)
        3. Sends `custom prompt + user query + Pinecone-retrieved information` to Deepseek V3 (Through OpenRouter)
    - `clean_and_upload.py` - Script that takes an Input/Output Directory, chunks data based on a set approximate token size, and uploads data to Pinecone (offers non-chunking mode too)
    - `inviteToOrganization.py` - Dormant code for an Admin Dashboard where requests to join Troops can be approved/denied
* Tools
    - `delete_vectors.py` - Python Script to delete Pinecone vectors by ID (with bulk support)
    - `download_emails.js` - GScript code that is hosted on [Google Scripts](https://script.google.com/home/projects/1p7LWD4aCjja0W3SjvDLOeXEfIyH_YPf3nxa8xoMImBszRJHTpxUKwaUp/edit?pli=1), allows for scraping Email data between a range of dates from a Google Group
    - `scrape_bsa.py` - Scrapes https://scouting.org using Firecrawl

#### troop-talk-website - Submodule of Troop-Talk
Hosted on DigitalOcean under [troop-talk-website](https://cloud.digitalocean.com/apps/625f0490-1baf-460e-aa23-190907b905e5?source_ref=projects&i=f2dff9)

## Installation & Setup

### Requirements
- Python 3.8+
- Node.js 16+
- Pinecone API key
- OpenRouter API key

### Backend Setup
1. Clone the repository
   ```
   git clone https://github.com/yourusername/Troop-Talk.git
   cd Troop-Talk
   ```
2. Install Python dependencies
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables
   ```
   export PINECONE_API_KEY=your_pinecone_key
   export OPENROUTER_API_KEY=your_openrouter_key
   ```

### Frontend Setup
1. Navigate to the website submodule
   ```
   cd troop-talk-website
   ```
2. Install dependencies
   ```
   npm i
   ```
3. Run development server
   ```
   npm run dev
   ```

## Usage
1. **Data Collection**: Use `download_emails.js` to collect email data from Google Groups
2. **Data Processing**: Use `clean_and_upload.py` to process and upload data to Pinecone
3. **Deployment**: The frontend and backend are deployed on DigitalOcean
4. **Querying**: Users can interact with the chat interface to ask questions about troop information

## Current Status
* Integrating TroopTalk into Troop 2220 (with Natalie's help)
* Emailed demo to Scoutmaster Ms. Visa
* Discussing integration with Aarush's Troop

#### Troop 2220 Integration
* Demo to Committee after Spring Break

## Future Plans
* Develop an AI crawler to scrape emails from Google Groups
* Establish partnerships with Boy Scouts of America leadership
* Expand beyond scouts to other youth organizations (Church Groups, YMCA, etc.) as suggested by Ozzie
* Explore partnership opportunities with Mr. Putt
* Investigate advertising in Scout Life Magazine

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
6. 
## Contact
Abhay Sudhir - abhay.sudhir08@gmail.com