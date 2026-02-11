from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
import shutil
from data_loader import DataLoader
from rag_core import RAGCore
from log_handler import LogHandler

class WebServer:
    def __init__(self, config):
        self.config = config
        self.app = FastAPI(title="RAG客户问答系统", description="基于豆包LLM的智能问答系统")
        
        # 初始化核心模块
        self.data_loader = DataLoader(config["data_dir"], config["vector_db_path"])
        self.rag_core = RAGCore(self.data_loader, config["doubao_api_key"])
        self.log_handler = LogHandler(config["log_dir"])
        
        # 加载向量库
        if not self.data_loader.load_vector_store():
            self.data_loader.rebuild_vector_store()
        
        # 注册路由
        self._register_routes()
        
        # 挂载静态文件
        if os.path.exists("static"):
            self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    def _register_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root():
            with open("static/index.html", "r", encoding="utf-8") as f:
                return f.read()
        
        @self.app.post("/api/query")
        async def query(text: str = Form(...)):
            try:
                # 检查资料更新
                if self.data_loader.check_for_changes():
                    self.data_loader.rebuild_vector_store()
                
                # 处理查询
                answer, relevant_docs = self.rag_core.process_query(text)
                
                # 记录日志
                self.log_handler.log_chat(text, answer, relevant_docs)
                
                # 准备检索片段
                sources = []
                for doc in relevant_docs:
                    sources.append({
                        "source": doc["metadata"]["source"],
                        "content": doc["page_content"],
                        "distance": doc.get("distance", "N/A")
                    })
                
                return {
                    "answer": answer,
                    "sources": sources
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            try:
                # 保存上传的文件
                file_path = os.path.join(self.config["data_dir"], file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # 重建向量库
                self.data_loader.rebuild_vector_store()
                
                return {"message": "文件上传成功，向量库已更新"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            return {
                "vector_store_status": "loaded" if self.data_loader.vector_store else "not loaded",
                "document_count": len(self.data_loader.documents),
                "data_dir": self.config["data_dir"]
            }
    
    def run(self, host="0.0.0.0", port=8000):
        uvicorn.run(self.app, host=host, port=port)

if __name__ == "__main__":
    print("正在启动Web服务器...")
    
    config = {
        "data_dir": os.path.join(os.path.dirname(__file__), "审核后资料文件夹"),
        "vector_db_path": os.path.join(os.path.dirname(__file__), "vector_db", "faiss_index.bin"),
        "log_dir": os.path.join(os.path.dirname(__file__), "logs"),
        "doubao_api_key": "1457918f-9107-4ca2-9c0d-bcda415e3830"
    }
    
    print(f"配置信息：")
    print(f"  资料目录: {config['data_dir']}")
    print(f"  向量库路径: {config['vector_db_path']}")
    print(f"  日志目录: {config['log_dir']}")
    
    # 确保必要的目录存在
    os.makedirs(os.path.dirname(config["vector_db_path"]), exist_ok=True)
    os.makedirs(config["log_dir"], exist_ok=True)
    os.makedirs(config["data_dir"], exist_ok=True)
    
    print("目录检查完成，正在初始化WebServer...")
    
    try:
        server = WebServer(config)
        print("WebServer初始化成功，正在启动服务器...")
        print("服务器启动后，可通过以下地址访问：")
        print("http://localhost:8000")
        server.run()
    except Exception as e:
        print(f"启动失败: {str(e)}")
        import traceback
        traceback.print_exc()