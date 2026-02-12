import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

class SessionManager:
    """会话管理器，处理用户会话的创建、查询和删除"""
    
    def __init__(self, session_timeout: int = 3600):
        """
        初始化会话管理器
        
        Args:
            session_timeout: 会话超时时间（秒），默认3600秒（1小时）
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
    
    def create_session(self) -> str:
        """
        创建新会话
        
        Returns:
            str: 会话ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "history": []
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话信息，如果会话不存在或已超时返回None
        """
        if session_id not in self.sessions:
            return None
        
        # 检查会话是否超时
        session = self.sessions[session_id]
        if (datetime.now() - session["last_accessed"]).total_seconds() > self.session_timeout:
            # 会话超时，删除会话
            del self.sessions[session_id]
            return None
        
        # 更新最后访问时间
        session["last_accessed"] = datetime.now()
        return session
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, str]]: 会话历史
        """
        session = self.get_session(session_id)
        if session:
            return session.get("history", [])
        return []
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        添加消息到会话历史
        
        Args:
            session_id: 会话ID
            role: 角色，"user"或"assistant"
            content: 消息内容
            
        Returns:
            bool: 添加成功返回True，否则返回False
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史消息数量，最多保留50条
        if len(session["history"]) > 50:
            session["history"] = session["history"][-50:]
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理过期会话
        
        Returns:
            int: 清理的会话数量
        """
        expired_sessions = []
        current_time = datetime.now()
        
        for session_id, session in self.sessions.items():
            if (current_time - session["last_accessed"]).total_seconds() > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """
        获取当前活跃会话数量
        
        Returns:
            int: 活跃会话数量
        """
        # 先清理过期会话
        self.cleanup_expired_sessions()
        return len(self.sessions)

# 测试代码
if __name__ == "__main__":
    manager = SessionManager(session_timeout=30)  # 测试用，设置30秒超时
    
    # 测试创建会话
    session_id = manager.create_session()
    print(f"创建会话: {session_id}")
    
    # 测试添加消息
    manager.add_message(session_id, "user", "有借还款功能么？")
    manager.add_message(session_id, "assistant", "有，借还款功能实现员工向公司申请资金场景，支持企业内部资金的借出-还回-核销闭环。")
    manager.add_message(session_id, "user", "菜单在什么位置？")
    
    # 测试获取历史
    history = manager.get_history(session_id)
    print("\n会话历史:")
    for msg in history:
        print(f"{msg['role']}: {msg['content']}")
    
    # 测试获取会话数量
    print(f"\n活跃会话数量: {manager.get_session_count()}")
    
    # 测试删除会话
    manager.delete_session(session_id)
    print(f"删除会话后数量: {manager.get_session_count()}")
