@echo off

rem 设置脚本执行目录为脚本所在目录
cd /d "%~dp0"

echo ================================================
echo Windows本地RAG客户问答Agent启动脚本
echo ================================================
echo 

rem 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python，请先安装Python 3.8+
    echo 建议从官网下载并安装：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 检测到Python，正在安装必要的依赖...
echo 

rem 安装依赖
pip install -q requests numpy faiss-cpu langchain sentence-transformers

if %errorlevel% neq 0 (
    echo 错误：依赖安装失败，请检查网络连接或Python环境
    pause
    exit /b 1
)

echo 依赖安装成功，正在启动RAG Agent...
echo 
echo 首次运行会自动构建向量库，可能需要一些时间...
echo 

rem 启动主程序
python main.py

rem 捕获程序退出
if %errorlevel% neq 0 (
    echo 程序异常退出，错误码：%errorlevel%
    pause
    exit /b %errorlevel%
)

pause
