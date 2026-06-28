$basePath = "c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\resources\RECOMENDACION_DE_RECURSOS_YELIA4AP"

Write-Host "Cerrando PowerPoint..."
Get-Process | Where-Object { $_.Name -eq "POWERPNT" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

try {
    Write-Host "Iniciando PowerPoint COM..."
    $pptApp = New-Object -ComObject PowerPoint.Application
    # Suppress all alert popups and dialogs
    $pptApp.DisplayAlerts = 1
    # Visible = 1 is often required for some COM operations on PowerPoint, but we open presentations with WithWindow = $false
    $pptApp.Visible = 1
} catch {
    Write-Error "No se pudo iniciar PowerPoint: $_"
    exit 1
}

for ($i = 3; $i -le 4; $i++) {
    $pptxPath = Join-Path $basePath "u${i}\presentation.pptx"
    $pdfPath = Join-Path $basePath "u${i}\presentation.pdf"
    
    if (Test-Path $pptxPath) {
        Write-Host "Convirtiendo u${i}: ${pptxPath} -> ${pdfPath}"
        try {
            # Open(filename, ReadOnly, Untitled, WithWindow)
            # ReadOnly = $true, Untitled = $true, WithWindow = $false
            $presentation = $pptApp.Presentations.Open($pptxPath, $true, $true, $false)
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
Write-Host "Proceso finalizado."
