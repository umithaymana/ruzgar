# Tek kurulum kökü: D:\ÜMİT\14-) PROGRAMLAR
# Eski kullanıcı ortamı D:\ÜMİT\PROGRAMLAR yolunu açınca Windows aynı adı
# D:\ÜMİT\programlar olarak oluşturuyordu. Bu betik o yolu kalıcı olarak
# 14-) PROGRAMLAR altına çevirir; ikinci klasörü yeniden açmaz.

$script:RuzgarProgramlarRoot = "D:\ÜMİT\14-) PROGRAMLAR"
$script:RuzgarProgramlarEskiKok = "D:\ÜMİT\PROGRAMLAR"

function Repair-RuzgarProgramlarEnv {
    param([string]$LogPath)

    $good = $script:RuzgarProgramlarRoot
    $bad = $script:RuzgarProgramlarEskiKok
    if (-not (Test-Path -LiteralPath $good)) { return }

    $cmp = [System.StringComparison]::OrdinalIgnoreCase

    function Write-RepairLog([string]$m) {
        if (-not $LogPath) { return }
        Add-Content -Path $LogPath -Value "$(Get-Date -Format o) $m" -Encoding UTF8
    }

    function Convert-RuzgarProgramlarPath([string]$Value) {
        if (-not $Value) { return $null }
        $trim = $Value.Trim().TrimEnd('\')
        $isBad = ($trim.Equals($bad, $cmp)) -or $Value.StartsWith($bad + "\", $cmp)
        if (-not $isBad) { return $null }
        if ($Value.StartsWith($good, $cmp)) { return $null }
        return $good + $Value.Substring($bad.Length)
    }

    $userVars = [Environment]::GetEnvironmentVariables("User")
    foreach ($key in @($userVars.Keys)) {
        $fixed = Convert-RuzgarProgramlarPath ([string]$userVars[$key])
        if (-not $fixed) { continue }
        [Environment]::SetEnvironmentVariable($key, $fixed, "User")
        Set-Item -Path "Env:$key" -Value $fixed
        Write-RepairLog "programlar yolu duzeltildi (User) $key=$fixed"
    }

    foreach ($item in @(Get-ChildItem Env:)) {
        $fixed = Convert-RuzgarProgramlarPath $item.Value
        if (-not $fixed) { continue }
        Set-Item -Path "Env:$($item.Name)" -Value $fixed
        Write-RepairLog "programlar yolu duzeltildi (Process) $($item.Name)=$fixed"
    }

    $defaults = [ordered]@{
        PIP_CACHE_DIR            = Join-Path $good "Caches\pip"
        HF_HOME                  = Join-Path $good "Caches\huggingface"
        HUGGINGFACE_HUB_CACHE    = Join-Path $good "Caches\huggingface\hub"
        TRANSFORMERS_CACHE       = Join-Path $good "Caches\huggingface\transformers"
        TORCH_HOME               = Join-Path $good "Caches\torch"
        ELECTRON_CACHE           = Join-Path $good "Caches\electron"
        ELECTRON_BUILDER_CACHE   = Join-Path $good "Caches\electron\builder"
        npm_config_cache         = Join-Path $good "Caches\npm"
        XDG_CACHE_HOME           = Join-Path $good "Caches\xdg"
    }
    foreach ($key in $defaults.Keys) {
        $target = $defaults[$key]
        $proc = [Environment]::GetEnvironmentVariable($key, "Process")
        if (-not $proc -or -not $proc.StartsWith($good, $cmp)) {
            Set-Item -Path "Env:$key" -Value $target
        }
        $user = [Environment]::GetEnvironmentVariable($key, "User")
        if (-not $user -or -not $user.StartsWith($good, $cmp)) {
            [Environment]::SetEnvironmentVariable($key, $target, "User")
            Write-RepairLog "programlar yolu sabitlendi (User) $key=$target"
        }
    }
}
