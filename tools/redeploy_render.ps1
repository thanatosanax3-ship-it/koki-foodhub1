<#
Trigger a manual deploy on Render using the Render API.
Usage:
  powershell -ExecutionPolicy Bypass -File tools\redeploy_render.ps1
You can set env vars `RENDER_API_KEY` and `RENDER_SERVICE_ID` before running.
#>

$apiKey = $env:RENDER_API_KEY
if (-not $apiKey) {
    $apiKey = Read-Host -Prompt 'Enter Render API Key (will not be stored)'
}

$serviceId = $env:RENDER_SERVICE_ID
if (-not $serviceId) {
    $serviceId = Read-Host -Prompt 'Enter Render Service ID (eg. srv-xxxx)'
}

if (-not $apiKey -or -not $serviceId) {
    Write-Error 'API key and Service ID are required. Aborting.'
    exit 1
}

$headers = @{
    Authorization = "Bearer $apiKey"
    'Content-Type' = 'application/json'
}

Write-Host "Triggering deploy for service: $serviceId"
try {
    $response = Invoke-RestMethod -Method Post -Uri "https://api.render.com/v1/services/$serviceId/deploys" -Headers $headers -Body '{}' -ContentType 'application/json'
    Write-Host "Deploy triggered successfully. Deploy id: $($response.id)" -ForegroundColor Green
    Write-Host "Check Render dashboard for build logs and status."
} catch {
    Write-Error "Failed to trigger deploy: $($_.Exception.Message)"
    exit 1
}

Write-Host "To fetch recent logs (JSON):"
Write-Host "Invoke-RestMethod -Method Get -Uri \"https://api.render.com/v1/services/$serviceId/logs?cursor=now&limit=200\" -Headers @{ Authorization = \"Bearer $apiKey\" } | ConvertTo-Json -Depth 5"
