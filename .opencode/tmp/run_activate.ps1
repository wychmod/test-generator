foreach ($env in @("claude","codebuddy","codex","cursor","openclaw","qoder","trae","windsurf")) {
 Write-Host "=== $env ==="
 node D:\pycharm\test-generator\bin\test-generator.js activate $env --dry-run *> D:\pycharm\test-generator\.opencode\tmp\act_$env.txt
 "EXIT=$LASTEXITCODE" | Out-File -Append D:\pycharm\test-generator\.opencode\tmp\act_$env.txt
}
Get-ChildItem D:\pycharm\test-generator\.opencode\tmp\act_*.txt | ForEach-Object { Write-Host "--- $($_.Name) ---"; Get-Content $_.FullName }
