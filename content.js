class GroupScraper {
    constructor() {
        this.emails = [];
        this.isRunning = false;
    }

    async start() {
        if (this.isRunning) return;
        this.isRunning = true;
        
        try {
            await this.scrapeCurrentPage();
            await this.goToNextPage();
        } catch (error) {
            console.error('Scraping error:', error);
        }
        
        this.isRunning = false;
    }

    async scrapeCurrentPage() {
        // Wait for the email list to load
        await this.waitForElements('div[role="article"]');
        
        // Get all email threads on the current page
        const threads = document.querySelectorAll('div[role="article"]');
        
        for (const thread of threads) {
            try {
                // Click to open the thread
                thread.click();
                await this.waitForElements('.message-content');
                
                // Extract email data
                const email = {
                    subject: this.getSubject(),
                    sender: this.getSender(),
                    date: this.getDate(),
                    content: this.getContent()
                };
                
                this.emails.push(email);
                console.log('Scraped:', email);
                
                // Go back to the list
                document.querySelector('button[aria-label="Back"]')?.click();
                await new Promise(r => setTimeout(r, 1000));
            } catch (error) {
                console.error('Error scraping thread:', error);
            }
        }
    }

    async goToNextPage() {
        const nextButton = document.querySelector('button[aria-label="Next page"]');
        if (nextButton && !nextButton.disabled) {
            nextButton.click();
            await new Promise(r => setTimeout(r, 2000));
            await this.start(); // Continue scraping
        } else {
            this.downloadResults();
        }
    }

    getSubject() {
        return document.querySelector('.thread-subject')?.textContent?.trim() || '';
    }

    getSender() {
        return document.querySelector('.message-sender')?.textContent?.trim() || '';
    }

    getDate() {
        return document.querySelector('.message-date')?.textContent?.trim() || '';
    }

    getContent() {
        return document.querySelector('.message-content')?.textContent?.trim() || '';
    }

    async waitForElements(selector, timeout = 5000) {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) return elements;
            await new Promise(r => setTimeout(r, 100));
        }
        throw new Error(`Timeout waiting for ${selector}`);
    }

    downloadResults() {
        const blob = new Blob([JSON.stringify(this.emails, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'google-group-emails.json';
        a.click();
    }
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'startScraping') {
        const scraper = new GroupScraper();
        scraper.start();
        sendResponse({status: 'started'});
    }
}); 