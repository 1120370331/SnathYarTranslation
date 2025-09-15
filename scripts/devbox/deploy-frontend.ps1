Param()
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

function Get-Env($key, $default='') { if ($envMap.ContainsKey($key)) { return $envMap[$key] } else { return $default } }

$feHost   = Get-Env 'FE_DEVBOX_SSH_HOST'   (Get-Env 'DEVBOX_SSH_HOST')
$fePort   = Get-Env 'FE_DEVBOX_SSH_PORT'   (Get-Env 'DEVBOX_SSH_PORT')
$feUser   = Get-Env 'FE_DEVBOX_SSH_USER'   (Get-Env 'DEVBOX_SSH_USER')
$feKey    = Get-Env 'FE_DEVBOX_SSH_KEY_PATH' (Get-Env 'DEVBOX_SSH_KEY_PATH')
$feDir    = Get-Env 'FE_REMOTE_DIR'        (Get-Env 'REMOTE_DIR')
$feBranch = Get-Env 'FE_DEPLOY_BRANCH'     (Get-Env 'DEPLOY_BRANCH','devbox-deploy')
$repoSsh  = Get-Env 'REMOTE_REPO_SSH'

if (-not $feHost -or -not $fePort -or -not $feUser -or -not $feKey -or -not $feDir -or -not $repoSsh) {
  throw 'Missing required .env values for frontend deploy.'
}

$sshBase = @('ssh','-p',"$fePort",'-i',"$feKey",'-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null',"$feUser@$feHost")
$scpBase = @('scp','-P',"$fePort",'-i',"$feKey",'-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null')

Write-Host "[remote] Preparing frontend repo at $feDir"
$prepTpl = @'
set -e
dir='__DIR__'
case "$dir" in
  ~/*) dir="$HOME/${dir#~/}" ;;
esac
mkdir -p "$dir"
if [ ! -d "$dir/.git" ]; then
  # Prefer SSH; fallback to HTTPS if provided and SSH fails
  if git ls-remote '__REPO_SSH__' >/dev/null 2>&1; then
    git clone '__REPO_SSH__' "$dir"
  elif [ -n "__REPO_HTTPS__" ] && git ls-remote '__REPO_HTTPS__' >/dev/null 2>&1; then
    git clone '__REPO_HTTPS__' "$dir"
  else
    echo "[error] Cannot access repo via SSH or HTTPS" >&2
    exit 1
  fi
fi
cd "$dir"
git fetch --all --prune
git checkout '__BRANCH__' || git checkout -b '__BRANCH__'
git pull --ff-only || true
mkdir -p logs
chmod +x frontend/devbox-start.sh || true
# Normalize line endings if needed
if command -v dos2unix >/dev/null 2>&1; then
  dos2unix frontend/devbox-start.sh 2>/dev/null || true
else
  sed -i 's/\r$//' frontend/devbox-start.sh 2>/dev/null || true
fi
'@
$prepCmd = $prepTpl.Replace('__DIR__',$feDir).Replace('__REPO_SSH__',$repoSsh).Replace('__BRANCH__',$feBranch).Replace('__REPO_HTTPS__',(Get-Env 'REMOTE_REPO_HTTPS'))
& $sshBase[0] $sshBase[1..($sshBase.Count-1)] -- @("bash","-lc", $prepCmd)
if ($LASTEXITCODE -ne 0) { throw "[ssh] Repo prep failed (exit $LASTEXITCODE)" }

if (Test-Path $envFile) {
  Write-Host "[remote] Uploading .env"
  $remoteHome = & $sshBase[0] $sshBase[1..($sshBase.Count-1)] -- @('bash','-lc','echo $HOME')
  if (-not $remoteHome) { $remoteHome = '/home/' + $feUser }
  $remoteEnvPath = ("{0}/{1}" -f $remoteHome, ($feDir -replace '^~/', ''))
  $remoteEnvPath = ("{0}/.env" -f $remoteEnvPath)
  & $scpBase[0] $scpBase[1..($scpBase.Count-1)] -- $envFile ("{0}@{1}:{2}" -f $feUser,$feHost,$remoteEnvPath)
  if ($LASTEXITCODE -ne 0) { throw "[scp] Upload .env failed (exit $LASTEXITCODE)" }
}

Write-Host "[remote] Starting frontend"
$startCmd = @'
set -e
cd '{0}'
if pgrep -f 'vite' >/dev/null 2>&1; then
  pkill -f vite || true
  sleep 1
fi
nohup bash frontend/devbox-start.sh > logs/frontend.out 2>&1 & echo \$! > logs/frontend.pid
echo 'Frontend PID:' \$(cat logs/frontend.pid)
'@ -f $feDir
& $sshBase[0] $sshBase[1..($sshBase.Count-1)] -- @("bash","-lc", $startCmd)
if ($LASTEXITCODE -ne 0) { throw "[ssh] Frontend start failed (exit $LASTEXITCODE)" }

Write-Host "[done] Frontend deployed. Tail logs with: ssh -p $fePort -i $feKey $feUser@$feHost 'tail -f $feDir/logs/frontend.out'"
