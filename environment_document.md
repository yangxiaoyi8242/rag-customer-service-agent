# 环境配置文档

## 1. 操作系统信息

| 项目 | 详情 |
|------|------|
| OS Name | Microsoft Windows 11 家庭中文版 |
| OS Version | 10.0.26200 Build 26200 |

## 2. Python 环境

| 项目 | 详情 |
|------|------|
| Python Version | 3.13.2 |

## 3. Python 依赖包

| Package | Version |
|---------|---------|
aiohappyeyeballs | 2.6.1
aiohttp | 3.13.3
aiosignal | 1.4.0
annotated-doc | 0.0.4
annotated-types | 0.7.0
anyio | 4.12.1
attrs | 25.4.0
certifi | 2026.1.4
charset-normalizer | 3.4.4
click | 8.3.1
colorama | 0.4.6
dataclasses-json | 0.6.7
faiss-cpu | 1.13.2
fastapi | 0.128.7
filelock | 3.20.3
frozenlist | 1.8.0
fsspec | 2026.2.0
greenlet | 3.3.1
h11 | 0.16.0
hf-xet | 1.2.0
httpcore | 1.0.9
httpx | 0.28.1
httpx-sse | 0.4.3
huggingface_hub | 1.4.1
idna | 3.11
jieba | 0.42.1
Jinja2 | 3.1.6
joblib | 1.5.3
jsonpatch | 1.33
jsonpointer | 3.0.0
langchain | 1.2.10
langchain-classic | 1.0.1
langchain-community | 0.4.1
langchain-core | 1.2.11
langchain-text-splitters | 1.1.0
langgraph | 1.0.8
langgraph-checkpoint | 4.0.0
langgraph-prebuilt | 1.0.7
langgraph-sdk | 0.3.5
langsmith | 0.7.1
lxml | 6.0.2
MarkupSafe | 3.0.3
marshmallow | 3.26.2
mpmath | 1.3.0
multidict | 6.7.1
mypy_extensions | 1.1.0
networkx | 3.6.1
numpy | 2.4.2
orjson | 3.11.7
ormsgpack | 1.12.2
packaging | 26.0
pip | 24.3.1
propcache | 0.4.1
psutil | 7.2.2
pydantic | 2.12.5
pydantic_core | 2.41.5
pydantic-settings | 2.12.0
python-docx | 1.2.0
python-dotenv | 1.2.1
python-multipart | 0.0.22
PyYAML | 6.0.3
regex | 2026.1.15
requests | 2.32.5
requests-toolbelt | 1.0.0
safetensors | 0.7.0
scikit-learn | 1.8.0
scipy | 1.17.0
sentence-transformers | 5.2.2
setuptools | 82.0.0
shellingham | 1.5.4
SQLAlchemy | 2.0.46
starlette | 0.52.1
sympy | 1.14.0
tenacity | 9.1.4
threadpoolctl | 3.6.0
tokenizers | 0.22.2
torch | 2.10.0
tqdm | 4.67.3
transformers | 5.1.0
typer-slim | 0.21.2
typing_extensions | 4.15.0
typing-inspect | 0.9.0
typing-inspection | 0.4.2
urllib3 | 2.6.3
uuid_utils | 0.14.0
uvicorn | 0.40.0
xxhash | 3.6.0
yarl | 1.22.0
zstandard | 0.25.0

## 4. 系统运行组件

| 进程名 | PID | 内存使用 | 描述 |
|--------|-----|----------|------|
python.exe | 18040 | 83,120 K | Web服务器进程 |

## 5. 项目配置信息

| 项目 | 路径 |
|------|------|
| 资料目录 | D:\AI coding- Talk Agent\审核后资料文件夹 |
| 向量库路径 | D:\AI coding- Talk Agent\vector_db\faiss_index.bin |
| 日志目录 | D:\AI coding- Talk Agent\logs |
| 文档数量 | 49 |

## 6. 环境搭建步骤

### 6.1 安装 Python
1. 下载并安装 Python 3.13.2
2. 确保 Python 添加到系统环境变量

### 6.2 安装依赖包
```bash
# 安装所有依赖包
pip install -r requirements.txt

# 或者逐个安装关键依赖
pip install faiss-cpu==1.13.2 fastapi==0.128.7 jieba==0.42.1 numpy==2.4.2 psutil==7.2.2 pydantic==2.12.5 python-docx==1.2.0 requests==2.32.5 uvicorn==0.40.0
```

### 6.3 复制项目文件
1. 复制整个项目目录到本地
2. 确保目录结构一致

### 6.4 启动服务
```bash
# 启动 Web 服务器
python web_server.py

# 访问地址
http://localhost:8000
```

## 7. 关键依赖说明

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| faiss-cpu | 1.13.2 | 向量数据库，用于存储和检索文档向量 |
| fastapi | 0.128.7 | Web 框架，提供 API 接口 |
| jieba | 0.42.1 | 中文分词库，用于提取关键词 |
| numpy | 2.4.2 | 科学计算库，用于向量运算 |
| psutil | 7.2.2 | 系统信息库，用于监控内存使用 |
| python-docx | 1.2.0 | Word 文档处理库，用于读取 .docx 文件 |
| uvicorn | 0.40.0 | ASGI 服务器，用于运行 FastAPI 应用 |

## 8. 注意事项

1. **向量库路径**：确保 `vector_db` 目录存在，用于存储向量索引
2. **资料目录**：确保 `审核后资料文件夹` 目录存在，用于存放参考资料
3. **日志目录**：确保 `logs` 目录存在，用于存放日志文件
4. **网络连接**：系统需要访问豆包 API，确保网络连接正常
5. **端口占用**：确保 8000 端口未被其他服务占用

## 9. 故障排查

### 9.1 依赖包安装失败
- 检查 Python 版本是否正确
- 检查网络连接是否正常
- 尝试使用 `pip install --upgrade pip` 更新 pip

### 9.2 服务启动失败
- 检查端口是否被占用
- 检查依赖包是否安装完整
- 检查配置文件路径是否正确

### 9.3 向量库加载失败
- 检查 `vector_db` 目录是否存在
- 检查向量库文件是否完整
- 尝试重新构建向量库

## 10. 版本信息

| 项目 | 版本 |
|------|------|
| 文档创建日期 | 2026-02-13 |
| 项目版本 | 1.0 |
| Python 版本 | 3.13.2 |
