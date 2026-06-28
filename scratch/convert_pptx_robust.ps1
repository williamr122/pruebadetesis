$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$basePath = Join-Path $projectRoot "frontend\public\resources\RECOMENDACION_DE_RECURSOS_YELIA4AP"

# 1. Kill any existing PowerPoint processes
Write-Host "Cerrando procesos de PowerPoint existentes..."
Get-Process | Where-Object { $_.Name -eq "POWERPNT" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Unblock the files to prevent security dialog popups
Write-Host "Desbloqueando archivos PPTX..."
for ($i = 1; $i -le 4; $i++) {
    $pptxPath = Join-Path $basePath "u${i}\presentation.pptx"
    if (Test-Path $pptxPath) {
        Unblock-File -Path $pptxPath
    }
}

# 3. Start PowerPoint COM instance
try {
    Write-Host "Iniciando PowerPoint COM..."
    $pptApp = New-Object -ComObject PowerPoint.Application
    # Keep visible so dialogs (if any) can be dismissed, but typically none occur after unblocking
    $pptApp.Visible = 1
} catch {
    Write-Error "No se pudo iniciar PowerPoint: $_"
    exit 1
}

# 4. Perform conversions
for ($i = 3; $i -le 4; $i++) {
    $pptxPath = Join-Path $basePath "u${i}\presentation.pptx"
    $pdfPath = Join-Path $basePath "u${i}\presentation.pdf"
    
    if (Test-Path $pptxPath) {
        Write-Host "Convirtiendo u${i}: ${pptxPath} -> ${pdfPath}"
        try {
            # Open(filename, ReadOnly, Untitled, WithWindow)
            # ReadOnly = $true, Untitled = $false, WithWindow = $false
            $presentation = $pptApp.Presentations.Open($pptxPath, $true, $false, $false)
            # 32 is ppSaveAsPDF
            $presentation.SaveAs($pdfPath, 32)
            $presentation.Close()
            Write-Host "¡Conversión de Unidad ${i} exitosa!"
        } catch {
            Write-Error "Error al convertir la Unidad ${i}: $_"
        }
    } else {
        Write-Host "No se encontró la presentación para la Unidad ${i} en ${pptxPath}"
    }
}

$pptApp.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($pptApp) | Out-Null
Write-Host "Proceso de conversión robusta finalizado."
