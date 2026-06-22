# 从 natapp 官方脚本下载 Windows 客户端到当前目录
$ErrorActionPreference = "Stop"
$token = "84da27cada47ec2f"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir
Write-Host "正在下载 natapp 到 $dir ..."
Invoke-Expression "irm https://natapp.cn/get.ps1?authtoken=$token | iex"
if (Test-Path "natapp.exe") {
    Write-Host "下载完成: $dir\natapp.exe"
} else {
    Write-Host "若未自动下载，请手动访问 https://natapp.cn/#download"
}
