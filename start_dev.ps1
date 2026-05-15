# Mwalimu Platform — Development Startup Scripts
#
# Run the Django backend with Uvicorn (ASGI) instead of the WSGI dev server.
# Benefits over `manage.py runserver`:
#   - True async support — SSE streaming is not buffered
#   - HTTP/1.1 keep-alive handled correctly
#   - Matches the production server (Uvicorn behind Nginx)
#
# Usage:
#   .\start_dev.ps1

Write-Host "Starting Mwalimu backend with Uvicorn (ASGI)..." -ForegroundColor Cyan
Write-Host "API:  http://127.0.0.1:8000/api/v1/" -ForegroundColor Green
Write-Host "Admin: http://127.0.0.1:8000/admin/" -ForegroundColor Green
Write-Host ""

.\venv\Scripts\uvicorn.exe `
    cbc_backend.asgi:application `
    --reload `
    --host 127.0.0.1 `
    --port 8000 `
    --log-level info
