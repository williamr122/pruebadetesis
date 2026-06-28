$basePath = "c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\resources\RECOMENDACION_DE_RECURSOS_YELIA4AP"

Write-Host "Cerrando PowerPoint..."
Get-Process | Where-Object { $_.Name -eq "POWERPNT" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

try {
    Write-Host "Iniciando PowerPoint COM..."
    $pptApp = New-Object -ComObject PowerPoint.Application
    # Run invisible to avoid user interaction popups interrupting
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
            # ReadOnly = $true (1st true)
            # Untitled = $true (2nd true) - opens as copy, bypasses links/template dialogs
            # WithWindow = $false (3rd false) - don't show window
            $presentation = $pptApp.Presentations.Open($pptxPath, $true, $true, $false)
            
            # SaveAs(pdfPath, ppSaveAsPDF)
            # ppSaveAsPDF = 32
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
