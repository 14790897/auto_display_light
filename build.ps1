# 自动打包脚本
# 使用方法: .\build.ps1

Write-Host "=== 自动屏幕亮度调节工具 - 打包脚本 ===" -ForegroundColor Cyan
Write-Host ""

# 检查是否安装了 PyInstaller
Write-Host "检查依赖..." -ForegroundColor Yellow
$pipList = pip list 2>&1 | Out-String
if ($pipList -notmatch "pyinstaller") {
    Write-Host "正在安装 PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装失败！" -ForegroundColor Red
        exit 1
    }
}

# 检查是否安装了 requests
if ($pipList -notmatch "requests") {
    Write-Host "正在安装 requests..." -ForegroundColor Yellow
    pip install requests
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装失败！" -ForegroundColor Red
        exit 1
    }
}

Write-Host "依赖检查完成！" -ForegroundColor Green
Write-Host ""

# 清理旧的打包文件
Write-Host "清理旧文件..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

# 开始打包
Write-Host "开始打包..." -ForegroundColor Yellow
Write-Host ""

# 使用 spec 文件打包
pyinstaller autolight.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== 打包成功！ ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "生成的 EXE 文件位置:" -ForegroundColor Cyan
    Write-Host "  $(Resolve-Path 'dist\AutoDisplayLight.exe')" -ForegroundColor White
    Write-Host ""
    Write-Host "使用方法:" -ForegroundColor Cyan
    Write-Host "  1. 双击运行 AutoDisplayLight.exe" -ForegroundColor White
    Write-Host "  2. 按 Ctrl+C 停止程序" -ForegroundColor White
    Write-Host ""
    Write-Host "提示: 首次使用前请确认 autolight.py 中的配置正确" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "=== 打包失败！ ===" -ForegroundColor Red
    Write-Host "请检查错误信息" -ForegroundColor Yellow
    exit 1
}
