#!/bin/bash
set -e

# Start Apache in the background via the official WP entrypoint
docker-entrypoint.sh apache2-foreground &

echo "Waiting for WordPress files to be available..."
until [ -f /var/www/html/wp-config.php ]; do
  sleep 2
done

# Give Apache/PHP a moment to settle
sleep 5

WP="wp --allow-root --path=/var/www/html"

echo "Waiting for DB connection..."
until $WP db check --quiet 2>/dev/null; do
  sleep 3
done

# Only install once — idempotent check
if ! $WP core is-installed 2>/dev/null; then
  echo "Installing WordPress core..."
  $WP core install \
    --url="${WP_URL}" \
    --title="${WP_TITLE}" \
    --admin_user="${WP_ADMIN_USER}" \
    --admin_password="${WP_ADMIN_PASSWORD}" \
    --admin_email="${WP_ADMIN_EMAIL}" \
    --skip-email

echo "Installing plugins..."
  for zip in /tmp/plugins/*.zip; do
    echo "  → Installing: $(basename $zip)"
    $WP plugin install "$zip" --activate
  done

  echo "Creating content to activate frontend plugin output..."

  # Post with social share buttons (social-warfare renders on any post)
  $WP post create \
    --post_title="Test Article" \
    --post_content="This is a test article. Lorem ipsum dolor sit amet." \
    --post_status="publish"

  # Page with file list shortcode (simple-file-list)
  $WP post create \
    --post_type="page" \
    --post_title="File List" \
    --post_content="[eeSFL]" \
    --post_status="publish"

  # Page with contact form (contact-form-7)
  # CF7 auto-creates a default form on activation — grab its ID
  CF7_ID=$($WP post list --post_type=wpcf7_contact_form --format=ids --fields=ID 2>/dev/null | head -1)
  $WP post create \
    --post_type="page" \
    --post_title="Contact" \
    --post_content="[contact-form-7 id=\"${CF7_ID}\" title=\"Contact form 1\"]" \
    --post_status="publish"

  # Page with Google Maps embed
  $WP post create \
    --post_type="page" \
    --post_title="Location" \
    --post_content="[wpgmza id=\"1\"]" \
    --post_status="publish"

  # Initialize a default Google Map (required for wp-google-maps to render)
  $WP db query "INSERT INTO wp_wp_google_maps_table \
    (map_id, map_title, map_width, map_height, map_start_lat, map_start_lng, map_start_zoom) \
    VALUES (1, 'Test Map', '100%', '400px', '33.4735', '-82.0105', 14);" 2>/dev/null || true

  $WP rewrite structure '/%postname%/'
  $WP rewrite flush

 
else
  echo "✅ WordPress already installed — skipping setup."
fi
 
# Keep the container alive 
wait