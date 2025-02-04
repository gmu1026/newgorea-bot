@echo off
chcp 65001 > nul

:: 관리자 권한 체크 및 요청
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :admin
) else (
    echo 관리자 권한이 필요합니다. 관리자 권한으로 다시 실행합니다...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:admin
setlocal enabledelayedexpansion

:: Steam 설치 경로를 레지스트리에서 찾기
for /f "tokens=2* usebackq" %%a in (`reg query "HKLM\SOFTWARE\WOW6432Node\Valve\Steam" /v "InstallPath" 2^>nul`) do (
    set "STEAM_PATH=%%b"
)

:: Steam 설치 경로를 찾지 못한 경우 32비트 레지스트리 확인
if not defined STEAM_PATH (
    for /f "tokens=2* usebackq" %%a in (`reg query "HKLM\SOFTWARE\Valve\Steam" /v "InstallPath" 2^>nul`) do (
        set "STEAM_PATH=%%b"
    )
)

if not defined STEAM_PATH (
    echo Steam 설치 경로를 찾을 수 없습니다.
    pause
    exit /b
)

:: Project Zomboid 설치 경로 찾기
set "ZOMBOID_PATH="
:: 기본 라이브러리 검사
if exist "!STEAM_PATH!\steamapps\common\ProjectZomboid" (
    set "ZOMBOID_PATH=!STEAM_PATH!\steamapps\common\ProjectZomboid"
) else (
    :: libraryfolders.vdf 파일에서 추가 라이브러리 검사
    for /f "tokens=2,*" %%a in ('type "!STEAM_PATH!\steamapps\libraryfolders.vdf" ^| findstr /r "path"') do (
        set "libpath=%%~b"
        set "libpath=!libpath:"=!"
        if exist "!libpath!\steamapps\common\ProjectZomboid" (
            set "ZOMBOID_PATH=!libpath!\steamapps\common\ProjectZomboid"
        )
    )
)

if not defined ZOMBOID_PATH (
    echo Project Zomboid 설치 경로를 찾을 수 없습니다.
    pause
    exit /b
)

echo Project Zomboid 경로: !ZOMBOID_PATH!

:: 메모리 값 입력받기
set /p "memory=설정할 메모리 크기를 GB 단위로 입력하세요: "
set /p "username=사용자명을 입력하세요 (빈 값은 asd): "
set /p "userpass=비밀번호를 입력하세요 (빈 값은 asd): "

:: 사용자명과 비밀번호가 비어있으면 기본값 설정
if "!username!"=="" set "username=asd"
if "!userpass!"=="" set "userpass=asd"

:: GB를 MB로 변환
set /a "memoryMB=%memory%*1024"

:: 파일 존재 확인
if not exist "!ZOMBOID_PATH!\ProjectZomboid64.json" (
    echo ProjectZomboid64.json 파일을 찾을 수 없습니다.
    pause
    exit /b
)

:: zombie/popman 폴더 존재 확인 및 생성
if not exist "!ZOMBOID_PATH!\zombie\popman" (
    mkdir "!ZOMBOID_PATH!\zombie\popman"
    echo zombie\popman 폴더를 생성했습니다.
)

:: Zomboid 사용자 폴더 설정
set "zomboidFolder=%userprofile%\Zomboid"
set "userFolder=!zomboidFolder!\Lua"

:: default.txt 복사
if exist "%~dp0default.txt" (
    if not exist "!zomboidFolder!\mods" mkdir "!zomboidFolder!\mods"
    copy "%~dp0default.txt" "!zomboidFolder!\mods\default.txt" /y
    echo default.txt 파일이 mods 폴더에 복사되었습니다.
) else (
    echo default.txt 파일이 스크립트 폴더에 없습니다.
)

:: options.ini 파일 수정
if exist "!zomboidFolder!\options.ini" (
    echo options.ini 파일을 수정합니다...
    set "tempFile=!zomboidFolder!\options.temp"
    (
        for /f "usebackq tokens=1* delims==" %%a in ("!zomboidFolder!\options.ini") do (
            set "line=%%a"
            set "value=%%b"
            if "!line!"=="aimOutline" (
                echo aimOutline=3
            ) else if "!line!"=="bloodDecals" (
                echo bloodDecals=0
            ) else (
                echo %%a=!value!
            )
        )
    ) > "!tempFile!"
    move /y "!tempFile!" "!zomboidFolder!\options.ini"
    echo options.ini 파일이 수정되었습니다.
) else (
    echo options.ini 파일이 없습니다.
)

:: ServerListSteam.txt 생성/수정
if not exist "!userFolder!" mkdir "!userFolder!"

::서버 설정 파일 읽기
if not exist "%~dp0server_config.txt" (
    echo server_config.txt 파일이 없습니다. 패치를 중단합니다.
    pause
    exit /b
)
for /f "usebackq delims=" %%a in ("%~dp0server_config.txt") do (
    set "server_ip=%%a"
)

(
echo name=newgorea
echo ip=!server_ip!
echo localip=
echo port=16261
echo serverpassword=
echo description=
echo user=!username!
echo password=!userpass!
echo usesteamrelay=true
) > "!userFolder!\ServerListSteam.txt"
echo ServerListSteam.txt 파일이 생성/수정되었습니다.

:: 백업 생성
copy "!ZOMBOID_PATH!\ProjectZomboid64.json" "!ZOMBOID_PATH!\ProjectZomboid64.json.backup"
echo ProjectZomboid64.json 백업 파일이 생성되었습니다.

:: 메모리 설정 수정
set "tempFile=!ZOMBOID_PATH!\temp.json"
set "foundXmx=0"
set "addedXms=0"
(
    for /f "usebackq tokens=* delims=" %%a in ("!ZOMBOID_PATH!\ProjectZomboid64.json") do (
        set "line=%%a"
        if "!line:Xmx=!"=="!line!" (
            if "!line:Xms=!"=="!line!" (
                echo %%a
            ) else (
                set "addedXms=1"
            )
        ) else (
            if !foundXmx!==0 (
                echo 		"-Xmx%memoryMB%m",
                if !addedXms!==0 (
                    echo 		"-Xms%memoryMB%m",
                )
                set "foundXmx=1"
                set "addedXms=1"
            )
        )
    )
) > "!tempFile!"
move /y "!tempFile!" "!ZOMBOID_PATH!\ProjectZomboid64.json"
echo 메모리 설정이 %memory%GB(%memoryMB%MB)로 변경되었습니다.

:: 클래스 파일 복사
if exist "%~dp0ZombieCountOptimiser.class" (
    copy "%~dp0ZombieCountOptimiser.class" "!ZOMBOID_PATH!\zombie\popman\" /y
    echo ZombieCountOptimiser.class를 복사했습니다.
) else (
    echo ZombieCountOptimiser.class 파일이 스크립트 폴더에 없습니다.
)

if exist "%~dp0NetworkZombiePacker.class" (
    copy "%~dp0NetworkZombiePacker.class" "!ZOMBOID_PATH!\zombie\popman\" /y
    echo NetworkZombiePacker.class를 복사했습니다.
) else (
    echo NetworkZombiePacker.class 파일이 스크립트 폴더에 없습니다.
)

:: 설정 완료 후 백업 파일 삭제
del "!ZOMBOID_PATH!\ProjectZomboid64.json.backup"
echo 백업 파일이 삭제되었습니다.

echo.
echo 모든 작업이 완료되었습니다.
pause