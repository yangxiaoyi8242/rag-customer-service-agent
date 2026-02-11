import os
import time
import json
from data_loader import DataLoader
from rag_core import RAGCore
from log_handler import LogHandler

class RAGAgent:
    def __init__(self):
        # 配置参数
        self.config = {
            "data_dir": os.path.join(os.path.dirname(__file__), "审核后资料文件夹"),
            "vector_db_path": os.path.join(os.path.dirname(__file__), "vector_db", "faiss_index.bin"),
            "log_dir": os.path.join(os.path.dirname(__file__), "logs"),
            "doubao_api_key": "1457918f-9107-4ca2-9c0d-bcda415e3830"
        }
        
        # 确保必要的目录存在
        os.makedirs(os.path.dirname(self.config["vector_db_path"]), exist_ok=True)
        os.makedirs(self.config["log_dir"], exist_ok=True)
        os.makedirs(self.config["data_dir"], exist_ok=True)
        
        # 初始化各个模块
        self.data_loader = DataLoader(self.config["data_dir"], self.config["vector_db_path"])
        self.rag_core = RAGCore(self.data_loader, self.config["doubao_api_key"])
        self.log_handler = LogHandler(self.config["log_dir"])
        
        # 加载或构建向量库
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """初始化向量库"""
        if not self.data_loader.load_vector_store():
            print("向量库不存在，正在构建...")
            self.data_loader.rebuild_vector_store()
        else:
            print("向量库加载成功")
    
    def check_and_update_data(self):
        """检查资料更新并更新向量库"""
        if self.data_loader.check_for_changes():
            self.data_loader.rebuild_vector_store()
    
    def run(self):
        """运行RAG Agent"""
        print("=" * 80)
        print("Windows本地RAG客户问答Agent")
        print("基于豆包LLM和审核后本地资料的智能问答系统")
        print("=" * 80)
        print("提示：输入'退出'或'quit'可退出系统")
        print("\n")
        
        try:
            while True:
                # 检查资料更新
                self.check_and_update_data()
                
                # 获取用户输入
                query = input("请输入您的问题：\n")
                
                # 处理退出命令
                if query.lower() in ["退出", "quit"]:
                    print("感谢使用，再见！")
                    break
                
                # 处理空输入
                if not query.strip():
                    print("请输入有效的问题")
                    continue
                
                # 处理查询
                print("\n正在分析问题...")
                answer, relevant_docs = self.rag_core.process_query(query)
                
                # 显示回答
                print("\n回答：")
                print(answer)
                print("\n")
                
                # 记录日志
                self.log_handler.log_chat(query, answer, relevant_docs)
                
        except KeyboardInterrupt:
            print("\n程序被用户中断，再见！")
        except Exception as e:
            print(f"程序运行出错: {str(e)}")

def main():
    """主函数"""
    agent = RAGAgent()
    agent.run()

if __name__ == "__main__":
    main()
