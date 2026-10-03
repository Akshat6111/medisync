Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

# Helper to await WinRT IAsyncOperation
function Await-Async($asyncOp) {
    $task = [System.WindowsRuntimeSystemExtensions]::AsTask($asyncOp)
    $task.Wait()
    return $task.Result
}

$imagePath = (Resolve-Path "user_prescription.jpg").Path
$file = Await-Async ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imagePath))
$stream = Await-Async ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read))
$decoder = Await-Async ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream))
$bitmap = Await-Async ($decoder.GetSoftwareBitmapAsync())

$lang = [Windows.Globalization.Language]::new("en-US")
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
$result = Await-Async ($engine.RecognizeAsync($bitmap))

Write-Output "=== EXTRACTED OCR TEXT ==="
$result.Text
