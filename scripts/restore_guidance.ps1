$ErrorActionPreference = 'Stop'
$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')
$guidance = Join-Path $root 'guidance'
New-Item -ItemType Directory -Path $guidance -Force | Out-Null

foreach ($name in @('stage43_expected.odb', 'final_topology_placement.odb')) {
    $archive = Join-Path $root ("guidance_archives\$name.zip")
    $temporary = Join-Path $env:TEMP ("h3_c40_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temporary | Out-Null
    try {
        Expand-Archive -LiteralPath $archive -DestinationPath $temporary -Force
        $source = Get-ChildItem -LiteralPath $temporary -Recurse -File |
            Where-Object Name -eq $name
        if (@($source).Count -ne 1) { throw "Unexpected archive members for $name" }
        Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $guidance $name) -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Host 'H3_C40_GUIDANCE_RESTORED'

