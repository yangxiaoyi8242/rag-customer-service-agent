import os
import datetime

class LogHandler:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        # 生成日志文件名（按日期）
        self.log_file = os.path.join(log_dir, f"rag_chat_{datetime.datetime.now().strftime('%Y%m%d')}.txt")
    
    def log_chat(self, query, answer, relevant_docs):
        """记录问答对话"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建日志内容
        log_content = f"[{timestamp}]\n"
        log_content += f"问题: {query}\n"
        log_content += f"回答: {answer}\n"
        
        if relevant_docs:
            log_content += "检索片段:\n"
            for i, doc in enumerate(relevant_docs):
                log_content += f"  [{i+1}] 来源: {doc['metadata']['source']}\n"
                log_content += f"     内容: {doc['page_content'][:200]}...\n"
                log_content += f"     相似度: {doc.get('distance', 'N/A')}\n"
        else:
            log_content += "检索片段: 无\n"
        
        log_content += "-" * 80 + "\n"
        
        # 写入日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_content)
            return True
        except Exception as e:
            print(f"日志写入失败: {str(e)}")
            return False
    
    def get_log_path(self):
        """获取当前日志文件路径"""
        return self.log_file
    
    def rotate_log(self):
        """按日期轮转日志文件"""
        new_log_file = os.path.join(self.log_dir, f"rag_chat_{datetime.datetime.now().strftime('%Y%m%d')}.txt")
        if new_log_file != self.log_file:
            self.log_file = new_log_file
