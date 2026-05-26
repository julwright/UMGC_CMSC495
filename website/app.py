from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def scan_wordpress(url):
    """
    Scrapes the target URL for WordPress plugin footprints.
    """
    found_plugins = []
    try:
        # Request the HTML from the target
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for /wp-content/plugins/ to get the Slug
        # Look at the ?ver= string at the end to get the Version
        plugin_pattern = re.compile(r'/wp-content/plugins/([^/]+)/.*?\?ver=([0-9\.]+)')
        
        # Search through all script and link tags
        for tag in soup.find_all(['script', 'link']):
            src = tag.get('src') or tag.get('href')
            if src:
                match = plugin_pattern.search(src)
                if match:
                    slug, version = match.groups()
                    plugin_info = {'slug': slug, 'version': version}
                    if plugin_info not in found_plugins:
                        found_plugins.append(plugin_info)
                        
        return found_plugins, None
    except requests.exceptions.RequestException as e:
        return None, f"Connection Error: Could not reach {url}."

def query_slm(plugin_slug, plugin_version):
    """
    Placeholder: Send plug in information 
    """
    # TODO: Connect to llm fastapi
    return {
        "threat_summary": f"Vulnerability found in '{plugin_slug}' version {plugin_version}.",
        "remediation": "Delete the plug in and find a new alternative. ."
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    scan_results = None
    error_message = None
    target_url = ""

    if request.method == 'POST':
        target_url = request.form.get('url')
        
        # 1. Fingerprint the Target
        plugins, error = scan_wordpress(target_url)
        
        if error:
            error_message = error
        elif not plugins:
            error_message = "No plugins detected or target is not a WordPress site."
        else:
            # 2. Query the SLM for each found plugin
            scan_results = []
            for plugin in plugins:
                slm_data = query_slm(plugin['slug'], plugin['version'])
                scan_results.append({
                    'slug': plugin['slug'],
                    'version': plugin['version'],
                    'threat_summary': slm_data['threat_summary'],
                    'remediation': slm_data['remediation']
                })

    return render_template('index.html', results=scan_results, error=error_message, url=target_url)

if __name__ == '__main__':
    # Running on 0.0.0.0 allows Docker to map the port externally
    app.run(host='0.0.0.0', port=5000, debug=True)