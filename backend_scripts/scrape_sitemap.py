import requests
import xmltodict
import json

def scrape_sitemap():
    response = requests.get('https://www.scouting.org/page-sitemap.xml')
    data = xmltodict.parse(response.text)
    urls = [url['loc'] for url in data['urlset']['url']]
    
    with open('sitemap.json', 'w') as f:
        json.dump({"urls": urls}, f, indent=2)

if __name__ == "__main__":
    scrape_sitemap() 