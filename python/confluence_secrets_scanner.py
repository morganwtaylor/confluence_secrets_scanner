import os
import re
import requests
from requests.auth import HTTPBasicAuth

confluence_url = 'https://your-confluence-instance.com'
username = os.getenv('CONFLUENCE_USERNAME')
api_token = os.getenv('CONFLUENCE_API_TOKEN')

if username is None or api_token is None:
    print("Error: Please set the CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN environment variables.")
    exit(1)

auth = HTTPBasicAuth(username, api_token)
headers = {'Content-Type': 'application/json'}

patterns = [
    r'[a-zA-Z0-9_\-]{32}',
    r'[a-zA-Z0-9_\-]{40}',
    r'[a-zA-Z0-9_\-]{64}',
]


def get_all_spaces():
    url = f'{confluence_url}/rest/api/space'
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Unable to fetch spaces (Status code: {response.status_code})")
        exit(1)

    try:
        spaces_data = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Invalid JSON response when fetching spaces.")
        exit(1)

    return [space['key'] for space in spaces_data['results']]


def get_all_pages(space_key):
    url = f'{confluence_url}/rest/api/content/search'
    query = f'space={space_key} and type=page'
    params = {'cql': query}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error: Unable to fetch pages for space {space_key} (Status code: {response.status_code})")
        return []

    try:
        pages_data = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Error: Invalid JSON response when fetching pages for space {space_key}.")
        return []

    return pages_data['results']


def search_page(page):
    url = f'{confluence_url}/rest/api/content/{page["id"]}?expand=body.storage'
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Unable to fetch page {page['title']} (ID: {page['id']}) (Status code: {response.status_code})")
        return

    try:
        page_data = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Error: Invalid JSON response when fetching page {page['title']} (ID: {page['id']}).")
        return

    content = page_data['body']['storage']['value']

    found_secrets = []

    for pattern in patterns:
        secrets = re.findall(pattern, content)
        if secrets:
            found_secrets.extend(secrets)

    if found_secrets:
        print(f"Secrets found in \"{page['title']}\" (ID: {page['id']}):")
        for secret in found_secrets:
            print(f"  - {secret}")


def main():
    space_keys = get_all_spaces()

    for space_key in space_keys:
        pages = get_all_pages(space_key)
        for page in pages:
            search_page(page)


if __name__ == "__main__":
    main()
