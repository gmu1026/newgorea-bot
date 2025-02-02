#!/bin/bash

set -e

echo "Discord Bot 배포 시작..."

# 현재 스크립트의 디렉토리 경로 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# 프로젝트 루트 디렉토리 (스크립트의 상위 디렉토리)
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
# bot 디렉토리 경로
BOT_DIR="$PROJECT_ROOT/bot"

echo "스크립트 위치: $SCRIPT_DIR"
echo "프로젝트 루트: $PROJECT_ROOT"
echo "봇 디렉토리 위치: $BOT_DIR"

# 환경 변수 파일 복사
cp "$PROJECT_ROOT/.env" /opt/discord-bot/.env

# 소스 코드 복사
cp -r "$BOT_DIR"/* /opt/discord-bot/

# 권한 설정
sudo chown -R $USER:$USER /opt/discord-bot

# 가상환경 활성화 및 패키지 업데이트
source /opt/discord-bot/venv/bin/activate
pip install -r "$BOT_DIR/requirements.txt"

# 서비스 재시작
sudo systemctl restart discord-bot
sudo systemctl enable discord-bot

echo "배포 완료!"
echo "서비스 상태 확인 중..."
sudo systemctl status discord-bot