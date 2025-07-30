#!/bin/bash
set -euo pipefail

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' 

USER_NAME="stos2025"
GROUP_NAME="stos2025"
APP_NAME="stos2025"
APP_PATH="/srv/$APP_NAME"
SERVICE_NAME="$APP_NAME.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
TMP_SRC="/tmp/$APP_NAME"

echo -e "${BLUE}[INFO] Starting $APP_NAME installation script...${NC}"

# ------------------------------------------------------------------------------
# 1. Check for required tools
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Checking for required commands...${NC}"
for cmd in docker git; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}[ERROR] Required command '$cmd' is not installed.${NC}"
        exit 1
    fi
done

# ------------------------------------------------------------------------------
# 2. Create group and system user
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Creating system group: '$GROUP_NAME' and user '$USER_NAME'...${NC}"

if ! getent group $GROUP_NAME > /dev/null; then
    sudo groupadd -r $GROUP_NAME
    echo -e "${GREEN}[OK] Group '$GROUP_NAME' created.${NC}"
else
    echo -e "${YELLOW}[SKIP] Group 'stos2025' already exists.${NC}"
fi

if ! id -u $USER_NAME > /dev/null 2>&1; then
    # Create system user: no home, no login shell
    sudo useradd -r -M -s /usr/sbin/nologin -g $GROUP_NAME $USER_NAME
    echo -e "${GREEN}[OK] User '$USER_NAME' created.${NC}"
else
    echo -e "${YELLOW}[SKIP] User '$USER_NAME' already exists.${NC}"
fi

# ------------------------------------------------------------------------------
# 3. Add user to Docker group
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Adding user '$USER_NAME' to docker group...${NC}"
sudo usermod -aG docker $USER_NAME

# ------------------------------------------------------------------------------
# 4. Create application directory structure
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Creating application directories...${NC}"
for dir in "$APP_PATH" "$APP_PATH/src" "$APP_PATH/data/shared" "$APP_PATH/data/workers"; do
    sudo mkdir -p "$dir"
done

# Set permissions and ownership
sudo chown -R $USER_NAME:$GROUP_NAME "$APP_PATH"
sudo chmod -R 770 "$APP_PATH"
echo -e "${GREEN}[OK] Directory permissions set.${NC}"

# ------------------------------------------------------------------------------
# 5. Pull application source files (mocked copy)
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Pulling application source files...${NC}"

sudo rm -rf "$TMP_SRC"
sudo mkdir -p "$TMP_SRC"

# NOTE: replace this with actual git clone in production
# sudo git clone https://github.com/Stos-2025/Projekt_Inzynierski-2025.git "$TMP_SRC"
sudo cp -a /home/stos/Projekt_Inzynierski-2025 "$TMP_SRC/"

# Copy source files to application path
sudo cp -a "$TMP_SRC/Projekt_Inzynierski-2025/src/." "$APP_PATH/src/"
sudo rm -rf "$TMP_SRC"

sudo rm -rf "$APP_PATH/compose.yml"
sudo rm -rf "$APP_PATH/.env"
sudo ln -s "$APP_PATH/src/compose.yml" "$APP_PATH/compose.yml"
sudo ln -s "$APP_PATH/src/.env" "$APP_PATH/.env"
echo -e "${GREEN}[OK] Source files copied.${NC}"

# ------------------------------------------------------------------------------
# 6. Environment file setup 
# ------------------------------------------------------------------------------
DOCKER_GID=$(getent group docker | cut -d: -f3)
STOS_GID=$(getent group stos2025 | cut -d: -f3)
STOS_FILES="$APP_PATH/data"
ENV_FILE="$APP_PATH/.env"

echo -e "${BLUE}[INFO] Updating .env file...${NC}"

sudo sed -i \
    -e "s|^STOS_FILES=.*|STOS_FILES=$STOS_FILES|" \
    -e "s|^DOCKER_GID=.*|DOCKER_GID=$DOCKER_GID|" \
    -e "s|^STOS_GID=.*|STOS_GID=$STOS_GID|" \
    "$ENV_FILE"

sudo grep -E '^(STOS_FILES|DOCKER_GID|STOS_GID)=' "$ENV_FILE"
echo -e "${GREEN}[OK] .env file updated:${NC}"

# ------------------------------------------------------------------------------
# 7. Build Docker images
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Building Docker images...${NC}"
sudo docker compose -f "$APP_PATH/src/compose.yml" build
echo -e "${GREEN}[OK] Docker build complete.${NC}"

# ------------------------------------------------------------------------------
# 8. Setup systemd service
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Creating systemd service...${NC}"

sudo cp "$APP_PATH/src/deploy/$SERVICE_NAME" "$SERVICE_PATH"
sudo chmod 644 "$SERVICE_PATH"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}[SUCCESS] Service '$SERVICE_NAME' installed and enabled.${NC}"
echo -e "${BLUE}[INFO] You can now run:${NC} ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
