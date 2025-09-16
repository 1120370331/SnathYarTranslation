Param(
  [string]$FrontendKeyPath = "private/devbox_fe",
  [string]$BackendKeyPath  = "private/devbox_be"
)
$ErrorActionPreference = 'Stop'

function Convert-KeyEncoding([string]$path){
  if (-not (Test-Path $path)) { Write-Warning "Key not found: $path"; return }
  $raw = Get-Content -Raw -Path $path
  # Normalize line endings to LF for safety, ensure trailing newline
  $norm = ($raw -replace "\r\n", "\n")
  if (-not $norm.EndsWith("`n")) { $norm += "`n" }
  # Write as ASCII to avoid BOM/UTF-16 issues with ssh
  [System.IO.File]::WriteAllText((Resolve-Path $path), $norm, [System.Text.Encoding]::ASCII)
  try { icacls (Resolve-Path $path) /inheritance:r /grant:r "$env:USERNAME:(R)" *> $null } catch {}
  Write-Host "[ok] Re-encoded key (ASCII, LF): $path"
}

Convert-KeyEncoding $FrontendKeyPath
Convert-KeyEncoding $BackendKeyPath

