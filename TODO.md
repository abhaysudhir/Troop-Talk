# TroopTalk To-Do's

- [x] Scrape https://scouting.org website data
- [x] Process/Upload website scraped data to Pinecone
- [x] Create namespace for T125
- [x] Upload chunked email content to Troop 125 Namespace


- [x] Create a separate namespace with just website data
- [x] Add in ability to query webiste data + troop data -> send to model
- [x] Add Scoutbook Requirements into Pinecone Vector Store

### Multiple Troop Integration
- [x] Add ability to read User's associated Organization ID (ex. `org_2rj04NYnOGUtlfms1uiOXFAHQDp`) for any user
- [ ] Send Organization ID as part of POST request to `ask_gpt.py`
- [ ] Add in dictionary of corresponding Organization IDs and namespaces to `ask_gpt.py`
- [ ] Ensure that only namespaces associated with particular Organization (Troop) are being queried
- [ ] Add in querying of universal sources of information (BSA Website, Merit Badges/Rank Requirements, etc.)
- [ ] Document Process of onboarding new Troops.