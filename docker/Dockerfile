FROM wordpress:5.0
COPY ./vulnerable-plugins/ /usr/src/wordpress/wp-content/plugins/
RUN chown -R www-data:www-data /usr/src/wordpress/wp-content/plugins/