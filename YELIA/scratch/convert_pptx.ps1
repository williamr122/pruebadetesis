$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$basePath = Join-Path $projectRoot "frontend\public\resources\RECOMENDACION_DE_RECURSOS_YELIA4AP"
$backendPath = Join-Path $projectRoot "backend\resources\RECOMENDACION_DE_RECURSOS_YELIA4AP"

try {
    Write-Host "Iniciando objeto COM de PowerPoint..."
    $pptApp = New-Object -ComObject PowerPoint.Application
    $pptApp.Visible = 1
} catch {
    Write-Error "No se pudo iniciar PowerPoint. Es posible que no esté instalado en esta máquina."
    exit 1
}

for ($i = 1; $i -le 4; $i++) {
    $pptxPath = Join-Path $basePath "u${i}\presentation.pptx"
    $pdfPath = Join-Path $basePath "u${i}\presentation.pdf"
    $backendPdfPath = Join-Path $backendPath "u${i}\presentation.pdf"
    
    if (Test-Path $pptxPath) {
        Write-Host "Convirtiendo u${i}: ${pptxPath} -> ${pdfPath}"
        try {
            # Open(filename, ReadOnly, Untitled, WithWindow)
            $presentation = $pptApp.Presentations.Open($pptxPath, $true, $true, $false)
            # 32 is ppSaveAsPDF
            $presentation.SaveAs($pdfPath, 32)
            $presentation.Close()
            Write-Host "¡Conversión de Unidad ${i} exitosa!"
            
            # Sync to backend resources
            if (Test-Path $pdfPath) {
                New-Item -ItemType Directory -Force -Path (Split-Path $backendPdfPath) | Out-Null
                Copy-Item -Path $pdfPath -Destination $backendPdfPath -Force
                Write-Host "Sincronizado a backend: ${backendPdfPath}"
            }
        } catch {
            Write-Error "Error al convertir la Unidad ${i}: $_"
        }
    } else {
        Write-Host "No se encontró la presentación para la Unidad ${i} en ${pptxPath}"
    }
}

$pptApp.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($pptApp) | Out-Null
Write-Host "Proceso de conversión finalizado."
