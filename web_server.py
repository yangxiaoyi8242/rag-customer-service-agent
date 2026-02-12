from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
import shutil
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from data_loader import DataLoader
from rag_core import RAGCore
from log_handler import LogHandler
from agent_core import AgentCore

class WebServer:
    def __init__(self, config):
        self.config = config
        self.app = FastAPI(title="RAG客户问答系统", description="基于豆包LLM的智能问答系统")
        
        # 初始化核心模块
        self.data_loader = DataLoader(config["data_dir"], config["vector_db_path"])
        self.rag_core = RAGCore(self.data_loader, config["doubao_api_key"])
        self.agent_core = AgentCore(self.rag_core, config["doubao_api_key"])
        self.log_handler = LogHandler(config["log_dir"])
        
        # 初始化线程池
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.rebuilding = False
        
        # 加载向量库
        if not self.data_loader.load_vector_store():
            # 在后台线程中重建向量库
            self.executor.submit(self._rebuild_vector_store_background)
        
        # 注册路由
        self._register_routes()
        
        # 挂载静态文件
        if os.path.exists("static"):
            self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    def _rebuild_vector_store_background(self):
        """在后台线程中重建向量库"""
        if self.rebuilding:
            print("向量库重建已在进行中，跳过")
            return
        
        print("开始后台重建向量库...")
        self.rebuilding = True
        try:
            self.data_loader.rebuild_vector_store()
            print("后台向量库重建完成")
        except Exception as e:
            print(f"后台向量库重建失败: {str(e)}")
        finally:
            self.rebuilding = False
    
    def _register_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root():
            with open("static/index.html", "r", encoding="utf-8") as f:
                return f.read()
        
        @self.app.post("/api/query")
        async def query(text: str = Form(...), session_id: str = Form(None)):
            try:
                # 调试信息
                print(f"接收到查询请求: {text}, session_id: {session_id}")
                
                # 检查资料更新
                if self.data_loader.check_for_changes():
                    # 在后台线程中重建向量库
                    self.executor.submit(self._rebuild_vector_store_background)
                    # 立即返回，不等待重建完成
                    # 注意：此时返回的可能是基于旧向量库的结果
                
                # 使用Agent处理查询
                result = self.agent_core.process_query(text, session_id)
                answer = result.get("answer")
                session_id = result.get("session_id")
                
                # 处理relevant_docs
                relevant_docs = []
                if answer.get("type") != "no_info":
                    # 重新获取相关文档
                    _, relevant_docs = self.rag_core.process_query(text)
                
                # 记录日志
                # 暂时注释掉日志记录，避免处理relevant_docs
                # self.log_handler.log_chat(text, answer, relevant_docs)
                
                # 调试信息
                print(f"Answer: {answer}")
                print(f"Session ID: {session_id}")
                print(f"Relevant docs count: {len(relevant_docs)}")
                
                # 准备检索片段，确保不包含numpy类型
                sources = []
                for doc in relevant_docs:
                    source_item = {
                        "source": str(doc["metadata"]["source"]),
                        "content": str(doc["page_content"]),
                        "distance": "N/A"
                    }
                    sources.append(source_item)
                
                return {
                    "answer": answer,
                    "sources": sources,
                    "rebuilding": self.rebuilding,
                    "session_id": session_id
                }
            except Exception as e:
                print(f"Error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/session")
        async def create_session():
            """创建新会话"""
            try:
                session_id = self.agent_core.create_session()
                print(f"创建新会话: {session_id}")
                return {
                    "session_id": session_id,
                    "session_count": self.agent_core.get_session_count()
                }
            except Exception as e:
                print(f"创建会话失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/session/{session_id}")
        async def delete_session(session_id: str):
            """删除会话"""
            try:
                success = self.agent_core.delete_session(session_id)
                print(f"删除会话: {session_id}, 结果: {success}")
                return {
                    "success": success,
                    "session_count": self.agent_core.get_session_count()
                }
            except Exception as e:
                print(f"删除会话失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/general_query")
        async def general_query(text: str = Form(...)):
            try:
                # 调试信息
                print(f"接收到通用查询请求: {text}")
                
                # 处理通用查询，调用豆包大模型自由回答
                answer = self.rag_core.process_general_query(text)
                
                # 调试信息
                print(f"General answer: {answer}")
                
                return {
                    "answer": answer
                }
            except Exception as e:
                print(f"Error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            try:
                # 保存上传的文件
                file_path = os.path.join(self.config["data_dir"], file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # 在后台线程中重建向量库
                self.executor.submit(self._rebuild_vector_store_background)
                
                return {"message": "文件上传成功，向量库正在后台更新"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            return {
                "vector_store_status": "loaded" if self.data_loader.vector_store else "not loaded",
                "document_count": len(self.data_loader.documents),
                "data_dir": self.config["data_dir"],
                "rebuilding": self.rebuilding
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