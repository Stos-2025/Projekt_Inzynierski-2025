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

echo -e "${BLUE}[INFO] Starting $APP_NAME cleanup script...${NC}"

# ------------------------------------------------------------------------------
# 1. Stop and disable systemd service
# ------------------------------------------------------------------------------
if sudo systemctl status "$SERVICE_NAME" &> /dev/null; then
    echo -e "${BLUE}[INFO] Stopping and disabling service: $SERVICE_NAME...${NC}"
    sudo systemctl stop "$SERVICE_NAME" || true
    sudo systemctl disable "$SERVICE_NAME" || true
    sudo rm -f "$SERVICE_PATH"
    sudo systemctl daemon-reload
    echo -e "${GREEN}[OK] Service removed.${NC}"
else
    echo -e "${YELLOW}[SKIP] Service '$SERVICE_NAME' not found.${NC}"
fi

# ------------------------------------------------------------------------------
# 2. Remove application directory
# ------------------------------------------------------------------------------
if [ -d "$APP_PATH" ]; then
    echo -e "${BLUE}[INFO] Removing application directory: $APP_PATH...${NC}"
    sudo rm -rf "$APP_PATH"
    echo -e "${GREEN}[OK] Application files removed.${NC}"
else
    echo -e "${YELLOW}[SKIP] Application path does not exist: $APP_PATH${NC}"
fi

# ------------------------------------------------------------------------------
# 3. Remove system user and group
# ------------------------------------------------------------------------------
if id "$USER_NAME" &> /dev/null; then
    echo -e "${BLUE}[INFO] Deleting system user: $USER_NAME...${NC}"
    sudo userdel "$USER_NAME" || true
    echo -e "${GREEN}[OK] User deleted.${NC}"
else
    echo -e "${YELLOW}[SKIP] User '$USER_NAME' does not exist.${NC}"
fi

# if getent group "$GROUP_NAME" > /dev/null; then
#     echo -e "${BLUE}[INFO] Deleting system group: $GROUP_NAME...${NC}"
#     sudo groupdel "$GROUP_NAME" || true
#     echo -e "${GREEN}[OK] Group deleted.${NC}"
# else
#     echo -e "${YELLOW}[SKIP] Group '$GROUP_NAME' does not exist.${NC}"
# fi

# ------------------------------------------------------------------------------
# 4. Optional: remove Docker images (prompt)
# ------------------------------------------------------------------------------
# read -rp "$(echo -e "${YELLOW}Do you want to remove Docker images? [y/N]: ${NC}")" CONFIRM
# if [[ "${CONFIRM:-N}" =~ ^[Yy]$ ]]; then
#     echo -e "${BLUE}[INFO] Removing Docker images...${NC}"
#     sudo docker image prune -a --force
#     echo -e "${GREEN}[OK] Docker images removed.${NC}"
# else
#     echo -e "${YELLOW}[SKIP] Docker images not removed.${NC}"
# fi

# echo -e "${GREEN}[DONE] Cleanup complete.${NC}"
