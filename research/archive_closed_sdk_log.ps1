$ErrorActionPreference = 'Stop'
$workspaceRoot = (Resolve-Path -LiteralPath 'D:\ApexOptions').Path
$sourcePath = [IO.Path]::GetFullPath((Join-Path $workspaceRoot 'logs\apiLogs.log'))
if (-not $sourcePath.StartsWith($workspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Source outside workspace' }
$archivePath = Join-Path $workspaceRoot 'logs\apiLogs_2026-11-09_codex_archive.log.gz'
$tempPath = $archivePath + '.new'
$manifestPath = Join-Path $workspaceRoot 'data\replay\batch\codex_predictive_review_2026-11-10\log_archive_manifest.json'
if ((Test-Path -LiteralPath $archivePath) -or (Test-Path -LiteralPath $tempPath)) { throw 'Archive target already exists' }
if (@(git -C $workspaceRoot ls-files -- logs/apiLogs.log).Count -gt 0) { throw 'Source is tracked; leave unchanged' }
$source = $null
try {
    # Deny concurrent readers/writers; permit deletion only after verified archive.
    # An existing live logger with a write handle prevents this open from succeeding.
    $source = [IO.File]::Open($sourcePath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Delete)
} catch {
    @{status='skipped';reason='Could not acquire exclusive read against writers';path=$sourcePath} | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Output 'Skipped archive: source may be active.'
    exit 0
}
try {
    $sourceBytes = $source.Length
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $sourceHash = [BitConverter]::ToString($sha.ComputeHash($source)).Replace('-','') } finally { $sha.Dispose() }
    $source.Position = 0
    $target = [IO.File]::Open($tempPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $gzip = [IO.Compression.GZipStream]::new($target, [IO.Compression.CompressionLevel]::Fastest, $true)
        try { $source.CopyTo($gzip) } finally { $gzip.Dispose() }
        $target.Flush($true)
    } finally { $target.Dispose() }
    $check = [IO.File]::OpenRead($tempPath)
    try {
        $unzip = [IO.Compression.GZipStream]::new($check, [IO.Compression.CompressionMode]::Decompress, $true)
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $archiveHash = [BitConverter]::ToString($sha.ComputeHash($unzip)).Replace('-','') } finally { $sha.Dispose(); $unzip.Dispose() }
    } finally { $check.Dispose() }
    if ($sourceHash -ne $archiveHash) { throw 'Archive verification failed; original retained' }
    Move-Item -LiteralPath $tempPath -Destination $archivePath
    $archiveBytes = (Get-Item -LiteralPath $archivePath).Length
    $record = @{status='verified_original_retained';source=$sourcePath;archive=$archivePath;sha256=$sourceHash;original_bytes=$sourceBytes;archive_bytes=$archiveBytes;reclaimed_bytes=0}
    $record | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Remove-Item -LiteralPath $sourcePath
    $record.status='archived'; $record.reclaimed_bytes=$sourceBytes-$archiveBytes
    $record | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    $record | ConvertTo-Json -Compress
} finally { $source.Dispose() }
