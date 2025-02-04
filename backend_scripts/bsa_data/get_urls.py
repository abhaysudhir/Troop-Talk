import requests
from xml.etree import ElementTree

def get_bsa_urls():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)',
        'Accept': 'text/html,application/xml',
    }
    
    try:
        response = requests.get('https://www.scouting.org/page-sitemap.xml', headers=headers)
        response.raise_for_status()
        
        root = ElementTree.fromstring(response.content)
        return [loc.text for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    urls = get_bsa_urls()
    print(urls) 