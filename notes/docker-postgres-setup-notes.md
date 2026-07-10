# Docker + PostgreSQL Setup Notes — ph-weatherpulse-pipeline

This document covers everything learned and done while setting up Docker and PostgreSQL for this project — from installing Docker on Ubuntu, to understanding docker-compose.yml syntax, to the actual commands used to create and inspect the database.

---

## 1. Installing Docker on Ubuntu

Docker was installed using Docker's official repository (not the outdated `apt install docker.io` package), to get the current, properly maintained version.

```bash
# Remove any old/conflicting versions first
sudo apt-get remove docker docker-engine docker.io containerd runc

# Update packages and install prerequisites
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Compose plugin
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify install
sudo docker run hello-world

# Run Docker without sudo (log out/in after this)
sudo usermod -aG docker $USER

# Confirm Compose plugin is available
docker compose version

# Enable Docker to start on boot
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

Note: Modern Docker uses `docker compose` (no hyphen, built into the CLI) instead of the old standalone `docker-compose` binary. All commands below use the current syntax.

---

## 2. Annotated Dummy docker-compose.yml

Below is a fully commented example showing which parts are fixed by the Docker image and which parts can be freely customized. This distinction was one of the biggest sources of confusion early on, so every line is labeled.

```yaml
services:

  postgres_weather:
    image: postgres:15                     # Semi-fixed: pick any valid Postgres version tag; must be a real tag on Docker Hub, but the version number is your choice
    container_name: weather_data           # Modifiable — any name you want, must be unique on your system
    restart: always                        # Modifiable — options: "no", "always", "on-failure", "unless-stopped"
    environment:
       POSTGRES_USER: weather_user         # Variable NAME is fixed (Postgres image looks for this exact name). Value ("weather_user") is yours to choose
       POSTGRES_PASSWORD: weather_pass     # Variable NAME is fixed. Value is yours to choose
       POSTGRES_DB: weather_db             # Variable NAME is fixed. Value is yours to choose
    ports:
      - "5433:5432"
      # Format: "HOST_PORT:CONTAINER_PORT"
      # LEFT (5433)  = modifiable — the port opened on your machine. Pick any free port.
      # RIGHT (5432) = fixed — Postgres always listens internally on 5432. Do not change unless you reconfigure Postgres itself.
    volumes:
      - weather_postgre_data:/var/lib/postgresql/data
      # Format: "VOLUME_NAME:CONTAINER_PATH"
      # LEFT (weather_postgre_data) = modifiable — just a label you choose for Docker's managed storage
      # RIGHT (/var/lib/postgresql/data) = fixed — this is the exact path the Postgres image expects its data directory to live at. Changing this breaks persistence.

volumes:
  weather_postgre_data:                    # Modifiable name, must match whatever you used above — this is what makes your data survive container restarts/recreation
```

### Rule of thumb summary

| Config block | Left side of colon | Right side of colon |
|---|---|---|
| ports: | Your choice (host port) | Fixed by the image (internal listening port) |
| volumes: | Your choice (volume name) | Fixed by the image (internal data path) |
| environment: | Fixed by the image (variable name) | Your choice (value) |

To find the correct fixed values for any new image (Metabase, Superset, MySQL, etc.), check that image's official page on Docker Hub, under the "Environment Variables" and "Volumes" sections.

Note on the `version:` key: older Compose files started with `version: '3.8'` at the top. This is now obsolete in current Docker Compose versions and can simply be omitted — Compose will warn but still run fine if it's left in.

---

## 3. Questions and Answers From Setup

**Does Docker need Postgres installed on my machine?**

No. The Postgres application is fully packaged inside the postgres:15 image. Your host machine only needs Docker itself. A Python script talking to the database only needs a lightweight driver (psycopg2-binary), not Postgres itself.

**What is weather_pgdata / weather_postgre_data — is it a real folder path?**

No. It is a named volume, just a label. Docker decides internally where it actually lives on disk, and you are not meant to interact with that location directly.

This is different from a bind mount, like `./dags:/opt/airflow/dags`, where the left side is a real, literal path on your machine, relative to your docker-compose.yml file.

**Does the volume store the whole Postgres container?**

No. The volume stores the entire database data directory: every database, schema, table, and row, plus Postgres's own internal system files. It does not store the Postgres software itself or the container. The container is disposable. The volume is what keeps your data safe across container recreation.

Only running `docker compose down -v` (with the -v flag) deletes volumes.

**Why two separate Postgres containers, one for weather data and one for Airflow metadata?**

Airflow needs its own database to track DAGs, run history, and task states. This has nothing to do with the actual project data. Keeping it in a separate container and volume from postgres_weather avoids mixing application data with orchestration-tool internals. This is cleaner and matches how real production systems are usually set up.

An alternative is one Postgres instance with two databases inside it, using an init script. That approach uses fewer resources but gives less isolation.

**If docker compose up fails partway through, does it undo what already happened?**

No. Any steps that already succeeded, such as the image being pulled, the network being created, or the volume being created, stay in place. Only the failing step needs to be fixed. Re-running `docker compose up -d` picks up where it left off, reusing what already exists instead of redoing everything.

**Does Docker Compose rebuild everything every time I run up?**

No. It checks whether the image, network, volume, and container configuration already match what is defined.

If a container's configuration changed, for example you edited the port mapping, Compose stops and recreates just that container. The volume, meaning your actual data, stays untouched throughout.

**Will the Postgres container start automatically when I reboot my laptop?**

Yes, if restart is set to always or unless-stopped, and Docker itself is enabled to start on boot.

It will not come back on its own if you deliberately ran `docker compose down`, since that command removes the container entirely. In that case you would need to run `docker compose up -d` again yourself.

**If I have many Docker projects, will they all start on boot and use up resources?**

Only containers that have a restart policy set, such as always or unless-stopped, and that were running at the time of shutdown, will restart automatically.

Recommended practice when running multiple projects:

- Use `restart: unless-stopped` instead of always, since it respects manual stops across reboots
- Run `docker compose down` when you are finished working on a project for the day
- Give each project its own folder, unique container names, and unique host ports, to avoid naming or port collisions

**What do I need to set up every time I start a brand new Docker project?**

- A new dedicated project folder
- A new docker-compose.yml specific to that project
- Unique host-side ports, if other projects are running at the same time
- Unique, descriptive container names
- restart: unless-stopped is recommended for new projects

Docker itself does not need to be reinstalled. It is a one-time, system-wide setup, and every new project just reuses it.

---

## 4. Docker Commands Reference

```bash
# Start containers in the background / If you added new services
docker compose up -d

# Stop and remove containers (data in named volumes is preserved)
docker compose down

# Stop and remove containers AND delete volumes (this destroys persisted data)
docker compose down -v

# Check status of containers defined in this compose file
docker compose ps

# View logs for a specific service (useful for debugging startup issues)
docker compose logs postgres_weather

# Follow logs live
docker compose logs -f

# List all Docker volumes on the system
docker volume ls

# Inspect where a named volume actually lives on disk
docker volume inspect weather_postgre_data

# List all containers, running and stopped, across the system
docker ps -a

# Show live CPU and RAM usage per running container
docker stats

# Stop every currently running container on the system
docker stop $(docker ps -q)

# Check if the Docker service itself is set to start on boot
systemctl is-enabled docker

# Enable Docker to start on boot
sudo systemctl enable docker
```

---

## 5. PostgreSQL Commands Reference (via Docker)

### Accessing Postgres inside the container

```bash
# Enter the interactive psql shell inside the running container
docker exec -it weather_data psql -U weather_user -d weather_db

# Run a single SQL command without entering the interactive shell
docker exec -it weather_data psql -U weather_user -d weather_db -c "SELECT * FROM raw.weather_api_response;"
```

### Commands used inside the psql prompt

| Command | Purpose |
|---|---|
| \l | List all databases |
| \dt | List tables in the current (public) schema |
| \dt raw.* | List tables specifically in the raw schema |
| \d raw.weather_api_response | Show column structure of a specific table |
| \x | Toggle expanded display, one column per line, useful for wide rows or JSON |
| \q | Quit psql, return to the normal shell |

### SQL used to set up and query the raw table

```sql
-- Create schema and raw landing table
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE raw.weather_api_response (
    id SERIAL PRIMARY KEY,
    fetched_at TIMESTAMP NOT NULL DEFAULT now(),
    latitude FLOAT,
    longitude FLOAT,
    raw_json JSONB NOT NULL
);

-- View all rows
SELECT * FROM raw.weather_api_response;

-- View specific columns
SELECT id, fetched_at FROM raw.weather_api_response;

-- Pretty-print the JSON column
SELECT id, fetched_at, jsonb_pretty(raw_json) FROM raw.weather_api_response;

-- Count total rows
SELECT COUNT(*) FROM raw.weather_api_response;
```

Pager navigation, if long output opens a colon pager prompt:

- Space: scroll down a page
- q: quit pager, return to the psql prompt

---

## 6. Python Environment Notes

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install required libraries
pip install psycopg2-binary requests
```

Important: use psycopg2-binary, not plain psycopg2. The plain version compiles a C extension and requires Postgres development headers (libpq-dev, pg_config.h) that typically are not installed on a machine running Postgres via Docker rather than natively. psycopg2-binary is a precompiled wheel, so no compiler is needed.

If VS Code shows "Import psycopg2 could not be resolved" despite the package being installed, it usually means the editor is not pointed at the .venv interpreter. Fix: Ctrl+Shift+P, then Python: Select Interpreter, then choose ./.venv/bin/python.

---

## 7. Known Gotchas

- Port already in use error ("address already in use"): usually means a native Postgres install or another container is already bound to 5432 on the host. Fix by mapping to a different host port, for example "5433:5432", rather than fighting for 5432.
- Environment variables silently ignored on later changes: POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB are only read by the image on the very first startup, when the data directory is empty. Changing them later has no effect unless the volume is wiped first with `docker compose down -v`.
- YAML colon spacing matters: "key: value" with a space after the colon is a YAML mapping. "key:value" with no space, inside a Compose shorthand string such as a volumes or ports list item, is Compose's own delimiter. Mixing these up causes parse errors or silent misconfiguration.
