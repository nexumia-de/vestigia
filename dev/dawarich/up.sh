#!/bin/sh
# Start the local Dawarich server and print a test account's API key.
# Usage: dev/dawarich/up.sh        (down: docker compose -f dev/dawarich/compose.yml down -v)
set -eu
cd "$(dirname "$0")"

# Cloud containers do not start the Docker daemon on their own.
if ! docker info >/dev/null 2>&1; then
    (dockerd >"${TMPDIR:-/tmp}/dockerd.log" 2>&1 &)
    i=0; until docker info >/dev/null 2>&1; do i=$((i+1)); [ $i -lt 30 ] || exit 1; sleep 1; done
fi

if [ ! -f .env ]; then
    rnd() { od -An -tx1 -N"$1" /dev/urandom | tr -d ' \n'; }
    {
        echo "DB_PASSWORD=$(rnd 16)"
        echo "SECRET_KEY_BASE=$(rnd 64)"
        echo "OTP_PRIMARY=$(rnd 16)"
        echo "OTP_DETERMINISTIC=$(rnd 16)"
        echo "OTP_SALT=$(rnd 16)"
    } > .env
fi

docker compose up -d --wait
docker compose exec -T app bin/rails runner '
  u = User.find_or_initialize_by(email: "demo@vestigia.test")
  if u.new_record?
    u.password = u.password_confirmation = "vestigia-demo-password"
    u.save!
  end
  puts "URL:      http://127.0.0.1:#{ENV.fetch("DAWARICH_PORT", "3000")}"
  puts "E-mail:   #{u.email}"
  puts "Password: vestigia-demo-password"
  puts "API key:  #{u.api_key}"
'
