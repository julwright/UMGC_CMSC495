from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup, Comment
import re
from urllib.parse import urlparse

app = Flask(__name__)


def get_base_url(url):
    """Extract the base URL (scheme + host + port) from a full URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_plugin_version_from_readme(base_url, slug):
    """
    Fetch the real plugin version from readme.txt.
    The ver= param in enqueued assets is unreliable (timestamps, WP core
    version, file versions). readme.txt always has the actual installed version.
    """
    readme_url = f"{base_url}/wp-content/plugins/{slug}/readme.txt"
    try:
        r = requests.get(readme_url, timeout=5)
        if r.status_code == 200:
            match = re.search(r'(?i)stable\s*tag:\s*([0-9.]+)', r.text)
            if match:
                return match.group(1)
    except requests.exceptions.RequestException:
        pass
    return None


def scan_wordpress(url):
    """
    Scrapes the target URL for WordPress plugin footprints.

    Detection strategy:
      1. Raw regex scan of the entire HTML string for /wp-content/plugins/ paths.
         This is the most reliable pass — immune to parser quirks.
      2. BeautifulSoup scan of inline <style> blocks and HTML comments as backup.
      3. For each detected plugin, verify the version via readme.txt.
    """
    found_plugins = {}

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
        base_url = get_base_url(url)

        # Matches: /wp-content/plugins/SLUG/...?ver=X.X.X or &ver=X.X.X
        versioned_pattern = re.compile(
            r'/wp-content/plugins/([^/]+)/[^"\'<>]*?[?&]ver=([0-9.]+)'
        )
        # Matches: /wp-content/plugins/SLUG/ (slug only, no version)
        slug_pattern = re.compile(r'/wp-content/plugins/([^/]+)/')

        # ── Pass 1: Raw regex on full HTML string ──
        # This bypasses BeautifulSoup entirely. It catches every reference
        # to /wp-content/plugins/ regardless of whether it's in a src, href,
        # inline style url(), HTML comment, or anywhere else.
        for match in versioned_pattern.finditer(html):
            slug, version = match.groups()
            if slug not in found_plugins:
                found_plugins[slug] = version

        # Catch any slug references that don't have a ver= param
        for match in slug_pattern.finditer(html):
            slug = match.group(1)
            if slug not in found_plugins:
                found_plugins[slug] = 'unknown'

        # ── Pass 2: HTML comments (some plugins leave version in comments) ──
        soup = BeautifulSoup(html, 'html.parser')
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            for match in slug_pattern.finditer(comment):
                slug = match.group(1)
                if slug not in found_plugins:
                    found_plugins[slug] = 'unknown'

        # ── Verify versions via readme.txt ──
        # The ver= param from enqueued assets is often wrong.
        # readme.txt has the real installed version.
        for slug in found_plugins:
            readme_version = get_plugin_version_from_readme(base_url, slug)
            if readme_version:
                found_plugins[slug] = readme_version

        # Convert to list format
        results = [
            {'slug': slug, 'version': version}
            for slug, version in found_plugins.items()
        ]

        return results, None

    except requests.exceptions.RequestException:
        return None, f"Connection Error: Could not reach {url}."


def query_slm(plugin_slug, plugin_version):
    """
    Placeholder: Send plugin information to LLM for threat analysis.
    """
    # TODO: Connect to LLM FastAPI
    return {
        "threat_summary": f"Vulnerability found in '{plugin_slug}' version {plugin_version}.",
        "remediation": "Delete the plugin and find a new alternative."
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    scan_results = None
    error_message = None
    target_url = ""

    if request.method == 'POST':
        target_url = request.form.get('url')

        # Fingerprint the website, get URL and return plugin data
        plugins, error = scan_wordpress(target_url)

        if error:
            error_message = error
        elif not plugins:
            error_message = "No plugins detected or target is not a WordPress site."
        else:
            # Query the SLM for each found plugin
            scan_results = []
            for plugin in plugins:
                slm_data = query_slm(plugin['slug'], plugin['version'])
                scan_results.append({
                    'slug': plugin['slug'],
                    'version': plugin['version'],
                    'threat_summary': slm_data['threat_summary'],
                    'remediation': slm_data['remediation']
                })

    return render_template(
        'index.html',
        results=scan_results,
        error=error_message,
        url=target_url
    )


if __name__ == '__main__':
    # Globally reachable. Debug mode during dev, switch to False for prod.
    app.run(host='0.0.0.0', port=5000, debug=True)