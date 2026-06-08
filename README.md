# WordPress Plugin Vulnerability Scanner

CMSC 495 Capstone - Group 3
Aidan Durham and Julian Wright

This is our capstone project. It's a tool that scans a WordPress site, figures out
what plugins it's running, and checks those against known vulnerabilities (CVEs). A
small language model gives the user info about the vulnerability and how to fix it.


## How it's set up

The repo is split into three folders:

- `website/` - the Flask website the user actually interacts with. It does the scraping
  and plugin detection.
- `docker/` - a fake vulnerable WordPress server we built so we have something to
  test against. 
- `training/` - the data and scripts for fine tuning the language model.


## How it works

The user types in a URL. The website does a GET request on that page and uses
BeautifulSoup and some regex to pull out the WordPress plugin names from the
`/wp-content/plugins/` paths. If it can't find the version in the HTML, it grabs the
plugin's `readme.txt` to get the real version. Then the plugin + version gets handed
off to the language model, which tells the user about any CVEs and how to fix them.

## Running it

You need Docker, for the test server, and Python 3 ,for the website.

Start the test server:

```
cd docker
docker compose up --build -d
```

That gives you a WordPress site at http://localhost:8080 - Login is admin / admin 

Then in another terminal, run the website:

```
cd website
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The website runs at http://localhost:5000. Put in http://localhost:8080 to scan the
test server.
