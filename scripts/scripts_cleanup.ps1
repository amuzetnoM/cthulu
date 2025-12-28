$now = Get-Date -Format yyyyMMdd_HHmmss
$bk = "C:\workspace\cleanup_backups\backup_$now"
New-Item -ItemType Directory -Path $bk -Force | Out-Null
Write-Output "backupDir: $bk"
$patterns = @('gcp_startup*','mt5*','*_automate*','cthulhu_deploy*.zip','cthulhu.zip','cthulhu_deploy2.zip','cthulhu_env_to_copy.txt')
$moved = @()
foreach ($p in $patterns) {
  Get-ChildItem -Path 'C:\workspace' -Filter $p -File -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $bk -Force
    $moved += $_.FullName
  }
}
if ($moved.Count -eq 0) { Write-Output 'no files matched for backup' } else { $moved | ForEach-Object { Write-Output "backed up: $_" } }