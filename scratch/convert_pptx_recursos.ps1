$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$resourcesPath = Join-Path $projectRoot "backend\resources\RECURSOS_YELIA4AP"

# 1. Kill any existing PowerPoint processes
Write-Host "Cerrando procesos de PowerPoint..."
Get-Process | Where-Object { $_.Name -eq "POWERPNT" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 2. Start PowerPoint COM instance
try {
    Write-Host "Iniciando PowerPoint COM..."
    $pptApp = New-Object -ComObject PowerPoint.Application
    $pptApp.Visible = 1
} catch {
    Write-Error "No se pudo iniciar PowerPoint: $_"
    exit 1
}

# 3. Perform conversion for u4
$pptxPath = Join-Path $resourcesPath "u4\presentation.pptx"
$pdfPath = Join-Path $resourcesPath "u4\presentation.pdf"

if (Test-Path $pptxPath) {
    Write-Host "Convirtiendo: ${pptxPath} -> ${pdfPath}"
    try {
        # Unblock the file first
        Unblock-File -Path $pptxPath
        
        # Open(filename, ReadOnly, Untitled, WithWindow)
        $presentation = $pptApp.Presentations.Open($pptxPath, $true, $false, $false)
        # 32 is ppSaveAsPDF
        $presentation.SaveAs($pdfPath, 32)
        $presentation.Close()
        Write-Host "¡Conversión exitosa!"
    } catch {
        Write-Error "Error al convertir: $_"
    }
} else {
    Write-Host "No se encontró el archivo PPTX en ${pptxPath}"
}

$pptApp.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($pptApp) | Out-Null
Write-Host "Conversión finalizada."
