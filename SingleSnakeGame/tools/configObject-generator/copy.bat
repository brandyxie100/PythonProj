@echo off
set currentPath=%cd%\tools\configObject-generator
set projectDataDirPath=%cd%\src\data

if EXIST %projectDataDirPath%\config (
    rd %projectDataDirPath%\config /s /q
)

md %projectDataDirPath%\config
xcopy %currentPath%\config %projectDataDirPath%\config
