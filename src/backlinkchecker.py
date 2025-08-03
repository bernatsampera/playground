import requests
import time
from urllib.parse import urlparse
import json
import os


def prepare_url(url):
    """Add https:// scheme if URL doesn't have one"""
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url



def get_openpagerank(domain):
    try:
        response = requests.get(
            "https://openpagerank.com/api/v1.0/getPageRank",
            headers={"API-OPR": "kcw0s08sscc0oog0cscgk4wwosc0c0g08wow00og"},  # You can request a free one
            params={"domains[]": domain}
        )
        response.raise_for_status()
        return response.json()['response'][0]['page_rank_integer']
    except Exception as e:
        print("Error:", e)
        return None



# Create output directory
os.makedirs('output', exist_ok=True)

domain_rankings = []
to_check = open('src/data.txt', 'r+')

for check in to_check.read().splitlines():
    do_check = check.split(',')
    url = prepare_url(do_check[0])
    domain = urlparse(url).netloc
    
    ranking = get_openpagerank(domain)
    domain_rankings.append({
        'domain': domain,
        'ranking': ranking
    })
    
    time.sleep(1)

to_check.close()

# Sort by ranking (highest first) and filter out None values
ranked_domains = [item for item in domain_rankings if item['ranking'] is not None]
ranked_domains.sort(key=lambda x: x['ranking'], reverse=True)

# Export results to txt
with open('output/rankings.txt', 'w') as f:
    for item in ranked_domains:
        f.write(f"{item['domain']}: {item['ranking']}\n")

# Simple console output
print(f"Checked {len(domain_rankings)} domains")
print("Results saved to output/rankings.txt")