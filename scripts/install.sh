#!/bin/bash

# 에러 발생시 스크립트 중단
set -e

echo "Discord Bot 설치 스크립트 시작..."

# 현재 스크립트의 디렉토리 경로 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# bot 디렉토리 경로 (스크립트의 상위 디렉토리의 bot 폴더)
BOT_DIR="$( dirname "$SCRIPT_DIR" )/bot"

echo "스크립트 위치: $SCRIPT_DIR"
echo "봇 디렉토리 위치: $BOT_DIR"

# Python 및 필수 패키지 설치
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# 프로젝트 디렉토리 생성
sudo mkdir -p /opt/discord-bot
sudo chown $USER:$USER /opt/discord-bot

# 가상환경 생성
python3 -m venv /opt/discord-bot/venv
source /opt/discord-bot/venv/bin/activate

# bot 폴더의 requirements.txt 사용하여 패키지 설치
pip install -r "$BOT_DIR/requirements.txt"

# systemd 서비스 파일 복사
sudo cp "$SCRIPT_DIR/discord-bot.service" /etc/systemd/system/
sudo systemctl daemon-reload

echo "설치 완료!"