#!/bin/bash

set -e

echo "Discord Bot 배포 시작..."

# 환경 변수 파일 복사
cp .env /opt/discord-bot/.env

# 소스 코드 복사
cp -r bot/* /opt/discord-bot/

# 권한 설정
sudo chown -R $USER:$USER /opt/discord-bot

# 가상환경 활성화 및 패키지 업데이트
source /opt/discord-bot/venv/bin/activate
pip install -r requirements.txt

# 서비스 재시작
sudo systemctl restart discord-bot
sudo systemctl enable discord-bot

echo "배포 완료!"