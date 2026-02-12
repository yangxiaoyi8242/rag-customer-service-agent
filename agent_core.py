from typing import List, Dict, Any, Optional
import json

from rag_core import RAGCore
from session_manager import SessionManager

class RAGTool:
    """RAG工具，封装现有的RAG功能"""
    
    name = "rag_tool"
    description = "用于回答与企业费控商旅相关的问题，包括出差申请、费用报销、借还款等功能"
    
    def __init__(self, rag_core: RAGCore):
        """
        初始化RAG工具
        
        Args:
            rag_core: RAGCore实例
        """
        self.rag_core = rag_core
    
    def _run(self, query: str, **kwargs) -> str:
        """
        运行RAG工具
        
        Args:
            query: 用户查询
            
        Returns:
            str: 回答内容
        """
        try:
            answer, relevant_docs = self.rag_core.process_query(query)
            
            # 构建回答内容
            if answer.get("type") == "no_info":
                return "抱歉，我无法回答这个问题，请转人工客服处理。"
            else:
                # 添加参考资料信息
                if relevant_docs:
                    sources_info = "\n参考资料："
                    for i, doc in enumerate(relevant_docs[:3]):
                        source = doc.get("metadata", {}).get("source", "未知")
                        content = doc.get("page_content", "").strip()[:100]
                        sources_info += f"\n{i+1}. {source}: {content}..."
                    return answer.get("message", "") + sources_info
                else:
                    return answer.get("message", "")
        except Exception as e:
            print(f"RAG工具执行失败: {e}")
            return "抱歉，系统暂时无法回答您的问题，请稍后再试。"

class AgentCore:
    """Agent核心，处理上下文理解和工具调用"""
    
    def __init__(self, rag_core: RAGCore, doubao_api_key: str):
        """
        初始化Agent核心
        
        Args:
            rag_core: RAGCore实例
            doubao_api_key: 豆包API密钥
        """
        self.rag_core = rag_core
        self.doubao_api_key = doubao_api_key
        self.session_manager = SessionManager()
        
        # 创建RAG工具
        self.rag_tool = RAGTool(rag_core)
        
        # 创建工具列表
        self.tools = [self.rag_tool]
        
        # 提示模板（简化实现）
        self.prompt_template = """你是一个专业的企业费控商旅客服助手，能够理解用户的上下文问题并提供准确的回答。

对话历史：
{chat_history}

当前问题：
{input}

请根据对话历史和当前问题，提供准确的回答。

回答格式：
直接回答用户问题，不需要任何引导语。
"""
    
    def create_session(self) -> str:
        """
        创建新会话
        
        Returns:
            str: 会话ID
        """
        return self.session_manager.create_session()
    
    def get_session_history(self, session_id: str) -> str:
        """
        获取会话历史，格式化为字符串
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: 格式化的会话历史
        """
        history = self.session_manager.get_history(session_id)
        if not history:
            return ""
        
        history_str = ""
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                history_str += f"用户: {content}\n"
            elif role == "assistant":
                history_str += f"助手: {content}\n"
        
        return history_str
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户查询
        
        Args:
            query: 用户查询
            session_id: 会话ID，可选
            
        Returns:
            Dict[str, Any]: 回答内容和会话信息
        """
        # 如果没有会话ID，创建新会话
        if not session_id:
            session_id = self.create_session()
        
        # 获取会话历史
        chat_history = self.get_session_history(session_id)
        
        # 直接使用RAG工具处理查询（简化实现）
        # 后续可以升级为完整的Agent流程
        answer = self.rag_tool._run(query)
        
        # 添加消息到会话历史
        self.session_manager.add_message(session_id, "user", query)
        self.session_manager.add_message(session_id, "assistant", answer)
        
        # 解析回答，判断是否需要调用豆包
        if "抱歉，我无法回答这个问题，请转人工客服处理。" in answer:
            answer_type = "no_info"
        else:
            answer_type = "info"
        
        return {
            "answer": {
                "type": answer_type,
                "message": answer
            },
            "session_id": session_id,
            "session_count": self.session_manager.get_session_count()
        }
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        return self.session_manager.delete_session(session_id)
    
    def get_session_count(self) -> int:
        """
        获取当前活跃会话数量
        
        Returns:
            int: 活跃会话数量
        """
        return self.session_manager.get_session_count()
