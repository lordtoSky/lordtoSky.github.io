@echo off
setlocal

cd /d "%~dp0"

set "RUBY_BIN=D:\exe_file\Ruby40-x64\bin"
if exist "%RUBY_BIN%\ruby.exe" set "PATH=%RUBY_BIN%;%PATH%"

where ruby >nul 2>nul
if errorlevel 1 (
  echo Ruby was not found. Expected: %RUBY_BIN%\ruby.exe
  exit /b 1
)

where bundle >nul 2>nul
if errorlevel 1 (
  echo Bundler was not found in PATH.
  exit /b 1
)

bundle exec jekyll serve -P 5555 --watch
