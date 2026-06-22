@echo off
REM Render IONQ slides → PNGs. Run from any cwd; script anchors itself.
pushd "%~dp0"
where python >nul 2>nul || (echo Python not found in PATH & popd & exit /b 1)
python -c "import playwright" 2>nul || (echo Installing playwright... & pip install playwright)
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.chromium.launch(args=['--no-sandbox']).close(); p.stop()" 2>nul || (echo Installing chromium... & python -m playwright install chromium)
python render.py
popd
