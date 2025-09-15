Param(
  [switch]$Frontend,
  [switch]$Backend
)
$ErrorActionPreference = 'Stop'

function Load-Dotenv($path) {
  if (-not (Test-Path $path)) { return @{} }
  $result = @{}
  Get-Content -Path $path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith('#')) { return }
    $idx = $line.IndexOf('=')
    if ($idx -gt 0) {
      $k = $line.Substring(0,$idx)
      $v = $line.Substring($idx+1)
      $result[$k] = $v
    }
  }
  return $result
}

$ROOT = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
$envFile = Join-Path $ROOT '.env'
$envMap = Load-Dotenv $envFile
function GE($k,$d=''){ if($envMap.ContainsKey($k)){ $envMap[$k] } else { $d } }

if ($Frontend) {
  $rhost = GE 'FE_DEVBOX_SSH_HOST' (GE 'DEVBOX_SSH_HOST')
  $port = GE 'FE_DEVBOX_SSH_PORT' (GE 'DEVBOX_SSH_PORT')
  $user = GE 'FE_DEVBOX_SSH_USER' (GE 'DEVBOX_SSH_USER')
  $key  = GE 'FE_DEVBOX_SSH_KEY_PATH' (GE 'DEVBOX_SSH_KEY_PATH')
  $target = "$user@$rhost"
  Write-Host ("[test] Frontend SSH to {0}:{1} using {2}" -f $target,$port,$key)
  ssh -p "$port" -i "$key" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $target echo ok
  exit $LASTEXITCODE
}

if ($Backend -or -not $Frontend) {
  $rhost = GE 'BE_DEVBOX_SSH_HOST' (GE 'DEVBOX_SSH_HOST')
  $port = GE 'BE_DEVBOX_SSH_PORT' (GE 'DEVBOX_SSH_PORT')
  $user = GE 'BE_DEVBOX_SSH_USER' (GE 'DEVBOX_SSH_USER')
  $key  = GE 'BE_DEVBOX_SSH_KEY_PATH' (GE 'DEVBOX_SSH_KEY_PATH')
  $target = "$user@$rhost"
  Write-Host ("[test] Backend SSH to {0}:{1} using {2}" -f $target,$port,$key)
  ssh -p "$port" -i "$key" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $target echo ok
  exit $LASTEXITCODE
}
