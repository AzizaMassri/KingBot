@echo off
echo ==============================================
echo KingBot Local Folder Updater
echo ==============================================
echo.

cd /d "%~dp0"

echo Pulling latest approved changes from GitHub...
git pull origin master

echo.
echo Update complete! The bot folder is synced with GitHub.
echo.
pause
