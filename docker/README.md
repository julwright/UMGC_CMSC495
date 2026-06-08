# Docker - Vulnerable WordPress Test Server


Sets up a vulnerable wordpress servers with five different vulnerable plugins. Used to test 
scanner and SLM. 

WordPress server is set up automatically via docker compose

## What's in here

- `docker-compose.yml` - starts the database and the WordPress container
- `Dockerfile` - builds the WordPress image and adds WP-CLI plus our plugins
- `entrypoint.sh` - the script that installs WordPress and activates the plugins
- `uploads.ini` - increases upload limit for plugins. 
- `vulnerable-plugins/` - vulnerable plugin zip files

## Running it

You need Docker and Docker Compose. From this folder:

```
docker compose up --build -d
```

The first time takes a few minutes because it has to download everything. When it's
done, go to http://localhost:8080. The admin login is at /wp-admin and it's:

- user: admin
- password: admin

To stop it:

```
docker compose down
```

If you want to wipe everything and start over (it keeps the database between runs
otherwise):

```
docker compose down -v
```

## What it's doing

The compose file starts a MySQL database and the WordPress container and puts them on
the same network so they can talk to each other. WordPress gets mapped to port 8080 on your machine.
There's a health check on the database so WordPress waits until the database is
actually ready before it starts.

The Dockerfile pulls the official WordPress image, installs WP-CLI (the command line
tool, so we can script the whole setup), and copies our plugins in. Then entrypoint.sh
runs, which installs WordPress, installs and activates each plugin, and makes a couple
of demo pages that some of the plugins need to actually show up.

## The vulnerable plugins

These are the plugins it installs. 

- social-warfare 3.5.2 - CVE-2019-9978
- wp-gdpr-compliance 1.4.2 - CVE-2018-19207
- simple-file-list 4.2.2 - CVE-2020-36847
- contact-form-7 5.0.3 - CVE-2020-35489
- cookie-notice 2.4.6 - CVE-2023-0823

## Checking that it worked

After it starts up:

1. Make sure port 8080 is listening
2. Go to http://localhost:8080 and see if the site loads
3. Log into /wp-admin with admin / admin
4. Go to the Plugins page and check that all five plugins are there and active

Then you can point the scanner at http://localhost:8080.

Note: these plugins are actually vulnerable, so only run this locally. Don't put it on
the internet.
