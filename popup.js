document.getElementById('startScraping').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    document.getElementById('status').textContent = 'Scraping started...';
    
    chrome.tabs.sendMessage(tab.id, { action: 'startScraping' }, response => {
        if (response?.status === 'started') {
            document.getElementById('status').textContent = 'Scraping in progress...';
        }
    });
}); 