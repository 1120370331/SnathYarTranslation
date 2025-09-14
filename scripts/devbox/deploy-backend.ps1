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

$beHost   = Get-Env 'BE_DEVBOX_SSH_HOST'   (Get-Env 'DEVBOX_SSH_HOST')
$bePort   = Get-Env 'BE_DEVBOX_SSH_PORT'   (Get-Env 'DEVBOX_SSH_PORT')
$beUser   = Get-Env 'BE_DEVBOX_SSH_USER'   (Get-Env 'DEVBOX_SSH_USER')
$beKey    = Get-Env 'BE_DEVBOX_SSH_KEY_PATH' (Get-Env 'DEVBOX_SSH_KEY_PATH')
$beDir    = Get-Env 'BE_REMOTE_DIR'        (Get-Env 'REMOTE_DIR')
$beBranch = Get-Env 'BE_DEPLOY_BRANCH'     (Get-Env 'DEPLOY_BRANCH','devbox-deploy')
$repoSsh  = Get-Env 'REMOTE_REPO_SSH'

${missing} = @()
if (-not $beHost) { $missing += 'BE_DEVBOX_SSH_HOST/DEVBOX_SSH_HOST' }
if (-not $bePort) { $missing += 'BE_DEVBOX_SSH_PORT/DEVBOX_SSH_PORT' }
if (-not $beUser) { $missing += 'BE_DEVBOX_SSH_USER/DEVBOX_SSH_USER' }
if (-not $beKey)  { $missing += 'BE_DEVBOX_SSH_KEY_PATH/DEVBOX_SSH_KEY_PATH' }
if (-not $beDir)  { $missing += 'BE_REMOTE_DIR/REMOTE_DIR' }
if (-not $repoSsh) { $missing += 'REMOTE_REPO_SSH' }
if ($missing.Count -gt 0) {
  Write-Error ("Missing required .env values: {0}" -f ($missing -join ', '))
  throw 'Missing required .env values for backend deploy.'
}

$sshBase = @('ssh','-p',"$bePort",'-i',"$beKey",'-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null',"$beUser@$beHost")
$scpBase = @('scp','-P',"$bePort",'-i',"$beKey",'-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null')

Write-Host "[remote] Preparing backend repo at $beDir"
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
chmod +x backend/devbox-start.sh || true
# Normalize line endings if needed
if command -v dos2unix >/dev/null 2>&1; then
  dos2unix backend/devbox-start.sh 2>/dev/null || true
else
  sed -i 's/\r$//' backend/devbox-start.sh 2>/dev/null || true
fi
'@
$prepCmd = $prepTpl.Replace('__DIR__',$beDir).Replace('__REPO_SSH__',$repoSsh).Replace('__BRANCH__',$beBranch).Replace('__REPO_HTTPS__',(Get-Env 'REMOTE_REPO_HTTPS'))
& $sshBase[0] $sshBase[1..($sshBase.Count-1)] -- @("bash","-lc", $prepCmd)
if ($LASTEXITCODE -ne 0) { throw "[ssh] Repo prep failed (exit $LASTEXITCODE)" }

if (Test-Path $envFile) {
  Write-Host "[remote] Uploading .env"
  # Resolve remote home dir to avoid '~' expansion issues on scp
  $remoteHome = & $sshBase[0] $sshBase[1..($sshBase.Count-1)] -- @('bash','-lc','echo $HOME')
  if (-not $remoteHome) { $remoteHome = '/home/' + $beUser }
  $remoteEnvPath = ("{0}/{1}" -f $remoteHome, ($beDir -replace '^~/', ''))
  $remoteEnvPath = ("{0}/.env" -f $remoteEnvPath)
  & $scpBase[0] $scpBase[1..($scpBase.Count-1)] -- $envFile ("{0}@{1}:{2}" -f $beUser,$beHost,$remoteEnvPath)
  if ($LASTEXITCODE -ne 0) { throw "[scp] Upload .env failed (exit $LASTEXITCODE)" }
}

Write-Host "[remote] Starting backend"
$startCmd = @'
set -e
cd '{0}'
if pgrep -f 'uvicorn .*src.main:app' >/dev/null 2>&1; then
  pkill -f 'uvicorn .*src.main:app' || true
  sleep 1
fi
nohup bash backend/devbox-start.sh > logs/backend.out 2>&1 & echo \$! > logs/backend.pid
echo 'Backend PID:' \$(cat logs/backend.pid)
'@ -f $beDir
& $sshBase[0] $sshBase[1..($sshBase.Count-1)] -- @("bash","-lc", $startCmd)
if ($LASTEXITCODE -ne 0) { throw "[ssh] Backend start failed (exit $LASTEXITCODE)" }

Write-Host "[done] Backend deployed. Tail logs with: ssh -p $bePort -i $beKey $beUser@$beHost 'tail -f $beDir/logs/backend.out'"
