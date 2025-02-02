import os
import asyncio
import discord
from discord.ext import commands
import logging
from rcon.source import rcon
from datetime import datetime, UTC
from discord.ui import Button, View, Modal, TextInput
from typing import Optional, List
import subprocess
from config import DISCORD_TOKEN, RCON_HOST, RCON_PORT, RCON_PASSWORD

# 로깅 설정


def setup_logging():
    log_filename = f'bot_{datetime.now().strftime("%Y%m%d")}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('discord_bot')


logger = setup_logging()

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!좀보이드', intents=intents)


async def send_rcon_command(command: str) -> str:
    try:
        logger.info(f'RCON 명령어 전송: {command}')
        response = await rcon(command, host=RCON_HOST, port=RCON_PORT, passwd=RCON_PASSWORD)
        logger.info(f'응답: {repr(response)}')
        return response if response else "서버로부터 응답이 없습니다."
    except Exception as e:
        logger.error(f'RCON 오류: {str(e)}', exc_info=True)
        return f"RCON 오류: {e}"


class ItemModal(Modal, title="아이템 지급"):
    player_name = TextInput(label="플레이어 이름", placeholder="플레이어 이름을 입력하세요")
    item_name = TextInput(label="아이템 이름", placeholder="예: Base.Axe")
    amount = TextInput(label="수량", placeholder="1", default="1")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            item = self.item_name.value
            if not item.startswith("Base."):
                item = f"Base.{item}"

            command = f'additem "{self.player_name.value}" "{item}" {self.amount.value}'
            response = await send_rcon_command(command)

            embed = discord.Embed(
                title="아이템 지급 결과",
                color=discord.Color.green(),
                timestamp=datetime.now(UTC)
            )
            embed.add_field(
                name="플레이어", value=self.player_name.value, inline=True)
            embed.add_field(name="아이템", value=item, inline=True)
            embed.add_field(name="수량", value=self.amount.value, inline=True)
            embed.add_field(name="결과", value=response, inline=False)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"오류가 발생했습니다: {str(e)}", ephemeral=True)


class AccessLevelModal(Modal, title="권한 설정"):
    player_name = TextInput(label="플레이어 이름", placeholder="플레이어 이름을 입력하세요")

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        # 권한 선택 드롭다운을 포함한 후속 메시지 전송
        embed = discord.Embed(
            title="권한 레벨 선택",
            description=f"{self.player_name.value}님의 권한 레벨을 선택하세요.",
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC)
        )

        class AccessLevelView(View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.select(
                placeholder="권한 레벨을 선택하세요",
                options=[
                    discord.SelectOption(
                        label="player", description="일반 플레이어 권한"),
                    discord.SelectOption(label="admin", description="관리자 권한"),
                    discord.SelectOption(
                        label="moderator", description="중재자 권한"),
                    discord.SelectOption(
                        label="overseer", description="감독자 권한"),
                    discord.SelectOption(label="gm", description="게임 마스터 권한"),
                    discord.SelectOption(
                        label="observer", description="관찰자 권한")
                ]
            )
            async def select_callback(self, interaction: discord.Interaction, select):
                try:
                    player = self.parent_modal.player_name.value  # Modal의 player_name 값 접근
                    level = select.values[0]
                    command = f'setaccesslevel "{player}" {level}'
                    response = await send_rcon_command(command)

                    result_embed = discord.Embed(
                        title="권한 설정 결과",
                        color=discord.Color.green(),
                        timestamp=datetime.now(UTC)
                    )
                    result_embed.add_field(
                        name="플레이어", value=player, inline=True)
                    result_embed.add_field(
                        name="권한 레벨", value=level, inline=True)
                    result_embed.add_field(
                        name="서버 응답", value=response, inline=False)

                    await interaction.response.send_message(embed=result_embed)
                except Exception as e:
                    await interaction.response.send_message(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

            def set_modal(self, modal):
                self.parent_modal = modal

        view = AccessLevelView()
        view.set_modal(self)  # Modal 인스턴스를 View에 전달
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class TeleportModal(Modal, title="텔레포트"):
    player1 = TextInput(label="이동할 플레이어", placeholder="플레이어 이름을 입력하세요")
    player2 = TextInput(label="목적지 플레이어 (선택사항)",
                        placeholder="이동할 목적지의 플레이어", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if self.player2.value:
                command = f'teleport "{self.player1.value}" "{self.player2.value}"'
                description = f"{self.player1.value}님을 {self.player2.value}님의 위치로 이동시켰습니다."
            else:
                command = f'teleport "{self.player1.value}"'
                description = f"{self.player1.value}님을 텔레포트했습니다."

            response = await send_rcon_command(command)

            embed = discord.Embed(
                title="텔레포트 결과",
                description=description,
                color=discord.Color.blue(),
                timestamp=datetime.now(UTC)
            )
            embed.add_field(name="서버 응답", value=response, inline=False)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"오류가 발생했습니다: {str(e)}", ephemeral=True)


class MainView(View):
    def __init__(self):
        super().__init__(timeout=None)  # 버튼 시간제한 없음

    @discord.ui.button(label="🎮 서버 시작", style=discord.ButtonStyle.success, custom_id="start_server")
    async def start_server_button(self, interaction: discord.Interaction, button: Button):
        try:
            command = "screen -S 1031.pzserver -X stuff 'bash start_server.sh\n'"

        # ProcessBuilder와 비슷한 방식으로 구현
            process = subprocess.Popen(
                ["bash", "-c", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 출력 읽기
            stdout, stderr = process.communicate()
            exit_code = process.returncode

            # 디버깅을 위한 로그
            print(f"Command output: {stdout}")
            print(f"Error output: {stderr}")
            print(f"Exit code: {exit_code}")

            if exit_code == 0:
                embed = discord.Embed(
                    title="서버 시작",
                    description="서버 시작 명령을 전송했습니다.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(UTC)
                )
                embed.add_field(name="상태", value="서버가 곧 시작됩니다.", inline=False)
                if stdout:
                    embed.add_field(
                        name="출력", value=stdout[:1024], inline=False)
            else:
                embed = discord.Embed(
                    title="서버 시작 실패",
                    description="서버 시작 중 오류가 발생했습니다.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(UTC)
                )
                error_msg = stderr if stderr else "알 수 없는 오류"
                embed.add_field(name="오류", value=error_msg, inline=False)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Exception details: {str(e)}")  # 디버깅용 로그
            await interaction.response.send_message(
                f"서버 시작 중 오류가 발생했습니다: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="👥 플레이어 목록", style=discord.ButtonStyle.primary, custom_id="players")
    async def players_button(self, interaction: discord.Interaction, button: Button):
        try:
            response = await send_rcon_command("players")

            player_list = []
            if response and "Players connected" in response:
                lines = response.split('\n')
                for line in lines[1:]:
                    if line.startswith('-'):
                        player_list.append(line[1:].strip())

            embed = discord.Embed(
                title="접속 중인 플레이어",
                color=discord.Color.blue(),
                timestamp=datetime.now(UTC)
            )

            if player_list:
                embed.description = f"총 {len(player_list)}명 접속 중"
                players_text = "\n".join(
                    f"• {player}" for player in player_list)
                embed.add_field(
                    name="플레이어 목록", value=players_text, inline=False)
            else:
                embed.description = "현재 접속자가 없습니다."

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    @discord.ui.button(label="📦 패치파일 다운로드", style=discord.ButtonStyle.primary, custom_id="download_patch")
    async def download_patch_button(self, interaction: discord.Interaction, button: Button):
        try:
            script_path = "/home/pzuser/create_patcher.sh"
            file_path = "/home/pzuser/newgorea-patcher.zip"

            # 먼저 로딩 메시지를 보냄
            await interaction.response.send_message(
                "패치 파일을 생성 중입니다. 잠시만 기다려주세요...",
                ephemeral=True
            )

            # 스크립트 실행
            try:
                process = await asyncio.create_subprocess_exec(
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "스크립트 실행 중 오류가 발생했습니다."
                    await interaction.edit_original_response(
                        content=f"패치 파일 생성 실패: {error_msg}"
                    )
                    return
            except Exception as e:
                await interaction.edit_original_response(
                    content=f"스크립트 실행 중 오류 발생: {str(e)}"
                )
                return

            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                embed = discord.Embed(
                    title="파일 없음",
                    description="패치 파일을 생성할 수 없습니다.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(UTC)
                )
                await interaction.edit_original_response(embed=embed)
                return

            # 파일 크기 확인 (Discord 파일 크기 제한: 25MB)
            file_size = os.path.getsize(file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB in bytes
                embed = discord.Embed(
                    title="파일 크기 초과",
                    description="파일이 Discord 업로드 제한(25MB)을 초과합니다.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(UTC)
                )
                await interaction.edit_original_response(embed=embed)
                return

            file = discord.File(file_path)
            embed = discord.Embed(
                title="패치파일 다운로드",
                description="아래 파일을 다운로드하세요.",
                color=discord.Color.blue(),
                timestamp=datetime.now(UTC)
            )

            # 기존 메시지를 파일과 함께 업데이트
            await interaction.edit_original_response(
                embed=embed,
                attachments=[file]
            )

        except Exception as e:
            print(f"Exception details: {str(e)}")  # 디버깅용
            await interaction.edit_original_response(
                content=f"파일 다운로드 중 오류가 발생했습니다: {str(e)}"
            )

    @discord.ui.button(label="📦 아이템 지급", style=discord.ButtonStyle.green, custom_id="items")
    async def items_button(self, interaction: discord.Interaction, button: Button):
        modal = ItemModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="👑 권한 설정", style=discord.ButtonStyle.primary, custom_id="access")
    async def access_button(self, interaction: discord.Interaction, button: Button):
        modal = AccessLevelModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🚀 텔레포트", style=discord.ButtonStyle.primary, custom_id="teleport")
    async def teleport_button(self, interaction: discord.Interaction, button: Button):
        modal = TeleportModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🌧️ 날씨 제어", style=discord.ButtonStyle.secondary, custom_id="weather")
    async def weather_button(self, interaction: discord.Interaction, button: Button):
        class WeatherView(View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(label="비 내리기", style=discord.ButtonStyle.primary)
            async def rain_start(self, interaction: discord.Interaction, button: Button):
                response = await send_rcon_command("startrain")
                embed = discord.Embed(
                    title="날씨 변경",
                    description="비가 내리기 시작했습니다.",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(UTC)
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            @discord.ui.button(label="비 그치기", style=discord.ButtonStyle.primary)
            async def rain_stop(self, interaction: discord.Interaction, button: Button):
                response = await send_rcon_command("stoprain")
                embed = discord.Embed(
                    title="날씨 변경",
                    description="비가 그쳤습니다.",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(UTC)
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        weather_view = WeatherView()
        await interaction.response.send_message("날씨를 선택하세요:", view=weather_view, ephemeral=True)

    @discord.ui.button(label="❌ 서버 종료", style=discord.ButtonStyle.danger, custom_id="quit")
    async def quit_button(self, interaction: discord.Interaction, button: Button):
        try:
            confirm_embed = discord.Embed(
                title="⚠️ 서버 종료 확인",
                description="정말로 서버를 종료하시겠습니까?",
                color=discord.Color.red(),
                timestamp=datetime.now(UTC)
            )

            class ConfirmView(View):
                def __init__(self):
                    super().__init__(timeout=30)

                @discord.ui.button(label="종료", style=discord.ButtonStyle.danger)
                async def confirm(self, interaction: discord.Interaction, button: Button):
                    response = await send_rcon_command("quit")
                    embed = discord.Embed(
                        title="서버 종료",
                        description="서버 종료 명령을 전송했습니다.",
                        color=discord.Color.red(),
                        timestamp=datetime.now(UTC)
                    )
                    await interaction.response.send_message(embed=embed)

                @discord.ui.button(label="취소", style=discord.ButtonStyle.secondary)
                async def cancel(self, interaction: discord.Interaction, button: Button):
                    embed = discord.Embed(
                        title="서버 종료 취소",
                        description="서버 종료가 취소되었습니다.",
                        color=discord.Color.green(),
                        timestamp=datetime.now(UTC)
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            confirm_view = ConfirmView()
            await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"오류가 발생했습니다: {str(e)}", ephemeral=True)


@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} 봇이 시작되었습니다.')


@bot.command(name="봇")
async def show_menu(ctx):
    """메인 메뉴를 표시합니다."""
    embed = discord.Embed(
        title="🎮 좀보이드 서버 관리",
        description="원하는 기능의 버튼을 클릭하세요.",
        color=discord.Color.blue(),
        timestamp=datetime.now(UTC)
    )
    embed.set_footer(text="버튼을 클릭하여 각 기능을 사용할 수 있습니다.")

    view = MainView()
    await ctx.send(embed=embed, view=view)


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f'글로벌 에러 발생 - 이벤트: {event}', exc_info=True)

try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    logger.critical(f'봇 실행 실패: {str(e)}', exc_info=True)
