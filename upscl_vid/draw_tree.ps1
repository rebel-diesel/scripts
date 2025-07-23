param([string]$StartFolder = ".")

function Draw-Tree([string]$path, [string]$prefix = '') {
    $items = Get-ChildItem -LiteralPath $path | Sort-Object { -not $_.PSIsContainer }, Name
    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $isLast = ($i -eq $items.Count - 1)

        if ($isLast) {
            $connector = "└── "
            $newPrefix = "$prefix    "
        } else {
            $connector = "├── "
            $newPrefix = "$prefix│   "
        }

        $name = if ($item.PSIsContainer) { "$($item.Name)/" } else { "$($item.Name)" }
        $line = "$prefix$connector$name"
        Add-Content -Encoding utf8 -Path "tree_output.txt" -Value $line

        if ($item.PSIsContainer) {
            Draw-Tree -path $item.FullName -prefix $newPrefix
        }
    }
}

"Структура от: $StartFolder" | Out-File -Encoding utf8 -FilePath "tree_output.txt"
Draw-Tree -path $StartFolder
