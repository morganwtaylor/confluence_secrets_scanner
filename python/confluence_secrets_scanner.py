import requests
import re
import os

# Replace with your Confluence instance URL
confluence_url = 'https://your-confluence-instance.com'

# Authenticate with Confluence using a personal access token
access_token = os.environ['CONFLUENCE_ACCESS_TOKEN']
headers = {
    'Authorization': f'Bearer {access_token}'
}

# Search patterns for secrets, API keys, and passwords
patterns = [
    r'[a-zA-Z0-9]{32}',  # 32-character alphanumeric strings, e.g., API keys
    r'(?i)password\s*[:=]\s*[a-zA-Z0-9!@#$%^&*()_+-=]{6,}',  # Passwords
    r'Bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+',  # JWT tokens
    # Add more patterns as needed
]


# Function to search for sensitive data in a page
def search_page(page_id):
    response = requests.get(f"{confluence_url}/rest/api/content/{page_id}?expand=body.storage", headers=headers)
    response.raise_for_status()
    page = response.json()

    content = page['body']['storage']['value']
    title = page['title']

    found_secrets = []

    for pattern in patterns:
        matches = re.findall(pattern, content)
        if matches:
            found_secrets.extend(matches)

    if found_secrets:
        print(f'Secrets found in "{title}" (Page ID: {page_id}):')
        for secret in found_secrets:
            print(f'  - {secret}')


# Function to search for sensitive data in a space
def search_space(space_key):
    start = 0
    limit = 25
    has_more = True

    while has_more:
        response = requests.get(
            f"{confluence_url}/rest/api/content/search?cql=space={space_key}&start={start}&limit={limit}&expand=id",
            headers=headers)
        response.raise_for_status()
        results = response.json()

        for page in results['results']:
            search_page(page['id'])

        has_more = results['size'] == limit
        start += limit


# Function to get all spaces
def get_all_spaces():
    start = 0
    limit = 25
    spaces = []

    while True:
        response = requests.get(f"{confluence_url}/rest/api/space?start={start}&limit={limit}", headers=headers)
        response.raise_for_status()
        results = response.json()

        spaces.extend(results['results'])

        if results['size'] < limit:
            break

        start += limit

    return spaces


# Search for secrets in all Confluence spaces
print('Searching for secrets in all Confluence spaces...')
spaces = get_all_spaces()

for space in spaces:
    space_key = space['key']
    print(f'Searching for secrets in space "{space_key}"...')
    search_space(space_key)

print('Finished searching for secrets.')
