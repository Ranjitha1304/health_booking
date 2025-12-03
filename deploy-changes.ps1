Write-Host "🚀 Starting deployment..." -ForegroundColor Cyan

# Backup config files
Write-Host "📋 Backing up config files from server..." -ForegroundColor Yellow
$backupFolder = "backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupFolder -Force

$configFiles = @(
    "docker-compose.prod.yml",
    "docker-compose.yml", 
    ".env.prod",
    ".env.dev",
    "nginx.conf"
)

foreach ($config in $configFiles) {
    Write-Host "  Downloading $config..." -ForegroundColor Gray
    scp ubuntu@98.92.246.79:~/healthcare-app/$config $backupFolder/ 2>$null
}

# Upload changed files
Write-Host "📤 Uploading changed files to server..." -ForegroundColor Yellow

$files = @(
    "apps/reports/forms.py",
    "apps/reports/models.py", 
    "apps/reports/urls.py",
    "apps/reports/views.py",
    "apps/reports/pdf_utils.py",
    "apps/users/forms.py",
    "apps/users/views.py",
    "healthcare/settings.py",
    "templates/reports/detail.html",
    "requirements.txt"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  Uploading $file..." -ForegroundColor Gray
        scp $file ubuntu@98.92.246.79:~/healthcare-app/$file
    } else {
        Write-Host "  ⚠️  File not found: $file" -ForegroundColor Red
    }
}

Write-Host "🔨 Rebuilding containers..." -ForegroundColor Green
# Use semicolons instead of &&
ssh ubuntu@98.92.246.79 "cd ~/healthcare-app; docker-compose -f docker-compose.prod.yml down; docker-compose -f docker-compose.prod.yml up -d --build"

Write-Host "📦 Running migrations..." -ForegroundColor Magenta
ssh ubuntu@98.92.246.79 "cd ~/healthcare-app; docker-compose -f docker-compose.prod.yml exec web python manage.py migrate"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Open: http://98.92.246.79" -ForegroundColor Cyan