FROM wordpress:6.4-php8.1-apache

# Install WP-CLI and dependencies
RUN apt-get update && apt-get install -y \
    less \
    default-mysql-client \
    curl \
    && curl -sO https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar \
    && chmod +x wp-cli.phar \
    && mv wp-cli.phar /usr/local/bin/wp \
    && rm -rf /var/lib/apt/lists/*

# Copy vulnerable plugings to docker container, sets the plugins to the correct permission too
RUN chown -R www-data:www-data /usr/src/wordpress/wp-content/plugins/
COPY ./vulnerable-plugins/ /tmp/plugins/

# Copy custom entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

