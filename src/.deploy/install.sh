#!/bin/bash
set -euo pipefail

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' 

APP_PATH="/srv/stos2025"
SERVICE_NAME="stos2025.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
TMP_SRC="/tmp/stos2025/src"

echo -e "${BLUE}[INFO] Starting stos2025 installation script...${NC}"

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
echo -e "${BLUE}[INFO] Creating system group and user 'stos2025'...${NC}"

if ! getent group stos2025 > /dev/null; then
    sudo groupadd -r stos2025
    echo -e "${GREEN}[OK] Group 'stos2025' created.${NC}"
else
    echo -e "${YELLOW}[SKIP] Group 'stos2025' already exists.${NC}"
fi

if ! id -u stos2025 > /dev/null 2>&1; then
    # Create system user: no home, no login shell
    sudo useradd -r -M -s /usr/sbin/nologin -g stos2025 stos2025
    echo -e "${GREEN}[OK] User 'stos2025' created.${NC}"
else
    echo -e "${YELLOW}[SKIP] User 'stos2025' already exists.${NC}"
fi

# ------------------------------------------------------------------------------
# 3. Add user to Docker group
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Adding user 'stos2025' to docker group...${NC}"
sudo usermod -aG docker stos2025

# ------------------------------------------------------------------------------
# 4. Create application directory structure
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Creating application directories...${NC}"
for dir in "$APP_PATH" "$APP_PATH/src" "$APP_PATH/data/shared" "$APP_PATH/data/workers"; do
    sudo mkdir -p "$dir"
done

# Set permissions and ownership
sudo chown -R stos2025:stos2025 "$APP_PATH"
sudo chmod -R 770 "$APP_PATH"
echo -e "${GREEN}[OK] Directory permissions set.${NC}"

# ------------------------------------------------------------------------------
# 5. Pull application source files (mocked copy)
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Pulling application source files...${NC}"

sudo rm -rf /tmp/stos2025
sudo mkdir -p "$TMP_SRC"

# NOTE: replace this with actual git clone in production
# sudo git clone https://github.com/Stos-2025/Projekt_Inzynierski-2025.git "$TMP_SRC"
sudo cp -a /home/stos/Projekt_Inzynierski-2025 "$TMP_SRC/"

# Copy source files to application path
sudo cp -a "$TMP_SRC/Projekt_Inzynierski-2025/src/." "$APP_PATH/src/"
sudo rm -rf /tmp/stos2025

rm -rf /srv/stos2025/compose.yml
rm -rf /srv/stos2025/.env
ln -s /srv/stos2025/src/compose.yml /srv/stos2025/compose.yml
ln -s /srv/stos2025/src/.env /srv/stos2025/.env
echo -e "${GREEN}[OK] Source files copied.${NC}"

# ------------------------------------------------------------------------------
# 6. Build Docker images
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Building Docker images...${NC}"
sudo docker compose -f "$APP_PATH/src/compose.yml" build
echo -e "${GREEN}[OK] Docker build complete.${NC}"

# ------------------------------------------------------------------------------
# 7. Setup systemd service
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Creating systemd service...${NC}"

sudo cp "$APP_PATH/src/.deploy/$SERVICE_NAME" "$SERVICE_PATH"
sudo chmod 644 "$SERVICE_PATH"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}[SUCCESS] Service '$SERVICE_NAME' installed and enabled.${NC}"
echo -e "${BLUE}[INFO] You can now run:${NC} ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
