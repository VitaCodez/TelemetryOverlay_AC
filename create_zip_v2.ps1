# Creates a zip file for Assetto Corsa Content Manager installation
# This version creates a renamed copy so it can coexist with the original telemetry_overlay

$new_name = "telemetry_overlay_v2"
$internal_name = "_telemetry_overlay_v2"
$old_name = "telemetry_overlay"
$old_internal = "_telemetry_overlay"

# Clean up any previous temp directory
if (Test-Path "temp") { Remove-Item -Recurse -Force "temp" }
if (Test-Path "${new_name}.zip") { Remove-Item -Force "${new_name}.zip" }

# Create directory structure matching AC's expected layout
New-Item -ItemType Directory -Force -Path "temp\apps\python\$new_name\$internal_name" | Out-Null

# Copy the main app files
Copy-Item -Recurse "$old_name\$old_internal\*" "temp\apps\python\$new_name\$internal_name\"

# Copy and rename the main entry point script
$main_script = Get-Content "$old_name\$old_name.py" -Raw
# Update the import to use the new internal module name
$main_script = $main_script -replace "from _telemetry_overlay\.", "from ${internal_name}."
# Update the return name so AC registers it with the new name
$main_script = $main_script -replace 'return "telemetry_overlay"', "return `"$new_name`""
# Update the module reference for config_path
$main_script = $main_script -replace "from _telemetry_overlay\.utils", "from ${internal_name}.utils"
Set-Content -Path "temp\apps\python\$new_name\$new_name.py" -Value $main_script

# Update config.py to import from the new module name
$config_file = "temp\apps\python\$new_name\$internal_name\config.py"
$config_content = Get-Content $config_file -Raw
$config_content = $config_content -replace "from telemetry_overlay import", "from $new_name import"
$config_content = $config_content -replace "from _telemetry_overlay\.", "from ${internal_name}."
Set-Content -Path $config_file -Value $config_content

# Update all other Python files to use the new internal module name
Get-ChildItem "temp\apps\python\$new_name\$internal_name\*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "_telemetry_overlay") {
        $content = $content -replace "from _telemetry_overlay\.", "from ${internal_name}."
        $content = $content -replace "import _telemetry_overlay\.", "import ${internal_name}."
        Set-Content -Path $_.FullName -Value $content
    }
}

# Copy icons with the new name
New-Item -ItemType Directory -Force -Path "temp\content\gui\icons" | Out-Null
if (Test-Path "icons\${old_name}_ON.png") {
    Copy-Item "icons\${old_name}_ON.png" "temp\content\gui\icons\${new_name}_ON.png"
}
if (Test-Path "icons\${old_name}_OFF.png") {
    Copy-Item "icons\${old_name}_OFF.png" "temp\content\gui\icons\${new_name}_OFF.png"
}

# Create the zip
Compress-Archive -Path "temp\*" -DestinationPath "${new_name}.zip" -Force

# Clean up
Remove-Item -Recurse -Force "temp"

Write-Host ""
Write-Host "SUCCESS: Created ${new_name}.zip" -ForegroundColor Green
Write-Host "Install via Content Manager: drag and drop the zip file into Content Manager."
