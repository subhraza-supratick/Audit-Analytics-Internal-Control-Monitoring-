$ErrorActionPreference = "Stop"
$templates = Get-ChildItem "d:\PROJECTS\DA\DA1\templates" -Recurse -Filter "*.html"
foreach ($file in $templates) {
    $path = $file.FullName
    $content = Get-Content -Path $path -Raw -Encoding UTF8
    $updated = $content -replace '\$\{\{', '₹{{'
    Set-Content -Path $path -Value $updated -Encoding UTF8 -NoNewline
    Write-Host "Fixed: $path"
}
Write-Host "All HTML templates updated."
