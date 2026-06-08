# Website - The Scanner

Website made with flask. Takes user input as a URL
and it scrapes the page, figures out what WordPress plugins are installed and what
versions, and (once we finish hooking it up) sends that to the language model to check
for vulnerabilities.

## Files

- `app.py` - the Flask app, does all the scraping and plugin detection
- `templates/index.html` - the single page with the form and the results
- `requirements.txt` - the Python packages you need

## Setup

You need Python 3. From this folder:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running it

```
python app.py
```

It runs at http://localhost:5000. Open that in a browser, type in a URL, and hit scan.
To test against our Docker WordPress server, use http://localhost:8080.

Right now it runs in debug mode since we're still developing. We'll turn that off later.

## How the scanning works

1. It does a GET request on the URL you give it. Just that one page, it doesn't crawl
   the rest of the site.
2. It looks through the HTML with regex for `/wp-content/plugins/<name>/` paths to find
   the plugins. There's also a backup pass that checks HTML comments.
3. For the version, it tries to read it off the `?ver=` part of the plugin's files, but
   that's usually wrong, so it then grabs the plugin's `readme.txt`, every WordPress
   plugin has one, and reads the real version from there.
4. Each plugin and version goes to `query_slm()`, which is supposed to send it to the
   language model and get back the vulnerability info and a fix.

## Stuff that's not done yet

This part works for scraping but there's still a few things to finish:

- The language model isn't actually connected yet. `query_slm()` just returns fake
  placeholder text for now (there's a TODO in the code).
- The fields don't line up between the app and the template. `app.py` sends
  `threat_summary` and `remediation` but `index.html` is looking for `assessment`, so
  the results won't show up right until we fix that.
- It doesn't catch cookie-notice. That plugin shows up in a stylesheet instead of a
  normal href/src tag, so our regex misses it. Need to update the regex to handle that.

## Notes

- We don't save anything about the sites people scan. That was on purpose as we didn't
  want to be storing a database of vulnerable websites.
- Only scan sites you own or are allowed to test. We use our own Docker WordPress server
  for this.
