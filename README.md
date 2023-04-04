# Confluence Secrets Scanner

Confluence Secrets Scanner is a set of scripts that help you scan Confluence spaces and pages for sensitive information such as API keys, passwords, and secrets.

## Usage

### Python

1. Set the `CONFLUENCE_ACCESS_TOKEN` environment variable with your Confluence personal access token.
2. Replace `https://your-confluence-instance.com` in `scanner.py` with your Confluence instance URL.
3. Install the required libraries:

```bash
pip install -r python/requirements.txt
