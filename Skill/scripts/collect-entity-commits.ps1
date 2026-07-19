param(
    [Parameter(Mandatory = $true)]
    [string]$Repository,

    [Parameter(Mandatory = $true)]
    [string[]]$Pattern,

    [string[]]$Path = @(),

    [string]$Output
)

$ErrorActionPreference = 'Stop'
$repositoryPath = (Resolve-Path -LiteralPath $Repository).Path

if (-not (Test-Path -LiteralPath (Join-Path $repositoryPath '.git'))) {
    throw "Not a Git repository: $repositoryPath"
}

$isShallow = (git -C $repositoryPath rev-parse --is-shallow-repository).Trim() -eq 'true'
$hashes = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

foreach ($searchPattern in $Pattern) {
    foreach ($hash in @(git -C $repositoryPath log --all --format='%H' -G $searchPattern)) {
        if ($hash) { [void]$hashes.Add($hash.Trim()) }
    }
    foreach ($hash in @(git -C $repositoryPath log --all --format='%H' --regexp-ignore-case --fixed-strings --grep=$searchPattern)) {
        if ($hash) { [void]$hashes.Add($hash.Trim()) }
    }
}

foreach ($trackedPath in $Path) {
    foreach ($hash in @(git -C $repositoryPath log --follow --format='%H' -- $trackedPath)) {
        if ($hash) { [void]$hashes.Add($hash.Trim()) }
    }
}

$commits = foreach ($hash in $hashes) {
    $fields = (git -C $repositoryPath show -s --format='%H%x1f%an%x1f%ae%x1f%aI%x1f%cI%x1f%s' $hash) -split [char]0x1f, 6
    $affectedPaths = @(git -C $repositoryPath diff-tree --no-commit-id --name-only -r $hash | Where-Object { $_ })
    $matchedPatterns = @()
    $patch = git -C $repositoryPath show --format= --find-renames $hash
    foreach ($searchPattern in $Pattern) {
        if (($patch | Select-String -Pattern $searchPattern -Quiet) -or ($fields[5] -match [regex]::Escape($searchPattern))) {
            $matchedPatterns += $searchPattern
        }
    }

    [ordered]@{
        hash = $fields[0]
        author = [ordered]@{ name = $fields[1]; email = $fields[2] }
        authoredAt = $fields[3]
        committedAt = $fields[4]
        subject = $fields[5]
        affectedPaths = $affectedPaths
        matchedPatterns = @($matchedPatterns | Select-Object -Unique)
        candidateEvidence = @('content-search', 'commit-message-search', 'confirmed-path-history')
        requiresDiffReview = $true
    }
}

$result = [ordered]@{
    repository = $repositoryPath
    revision = (git -C $repositoryPath rev-parse HEAD).Trim()
    isShallow = $isShallow
    searchedPatterns = $Pattern
    followedPaths = $Path
    candidateCount = @($commits).Count
    candidates = @($commits | Sort-Object committedAt)
    warning = 'Candidates require semantic diff review before inclusion in history.commits.'
}

$json = $result | ConvertTo-Json -Depth 8
if ($Output) {
    $parent = Split-Path -Parent $Output
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    Set-Content -LiteralPath $Output -Value $json -Encoding utf8
}
else {
    $json
}
