import requests
import json
import numpy as np
from keyword_manager import KeywordManager
import jieba

class RAGCore:
    def __init__(self, data_loader, doubao_api_key):
        self.data_loader = data_loader
        self.doubao_api_key = doubao_api_key
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.default_model = "doubao-seed-1-6-251015"
        self.keyword_manager = KeywordManager()
        # 初始化jieba分词
        self._init_jieba()
    
    def _init_jieba(self):
        """初始化jieba分词"""
        # 加载自定义词典
        # 这里可以添加行业特定词汇
        pass
    
    def extract_keywords(self, text, top_n=5):
        """从文本中提取关键词"""
        # 使用jieba分词
        words = jieba.cut(text)
        
        # 过滤停用词
        stop_words = {
            "怎么", "如何", "怎么", "怎样", "如何", "能否", "是否", 
            "可以", "能不能", "有没有", "有吗", "吗", "的", "了", "在", 
            "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", 
            "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", 
            "没有", "看", "好", "自己", "这"
        }
        
        # 计算词频
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按词频排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # 返回前top_n个关键词
        return [word for word, _ in sorted_words[:top_n]]
    
    def retrieve_relevant_docs(self, query, top_k=8):
        """检索与查询相关的文档"""
        if not self.data_loader.vector_store:
            return []
        
        # 从查询中提取关键词并添加到关键词库
        extracted_keywords = self.extract_keywords(query)
        
        # 添加新关键词到关键词库
        if extracted_keywords:
            self.keyword_manager.add_keywords(extracted_keywords)
        
        # 1. 强制检索规则（优先执行）
        mandatory_docs = []
        
        # 从关键词管理器获取触发关键词
        trigger_keywords = self.keyword_manager.get_keywords()
        
        # 检查是否触发强制检索
        trigger_found = any(keyword in query for keyword in trigger_keywords)
        
        if trigger_found:
            # 限制强制检索的文档数量，提高性能
            doc_count = 0
            max_docs = 20  # 限制处理的文档数量
            
            for doc in self.data_loader.documents:
                if doc_count >= max_docs:
                    break
                    
                content = doc["page_content"]
                # 检查是否包含相关内容
                content_has_relevant = False
                
                # 检查是否包含登录企业手机银行相关内容
                if "登录企业手机银行" in content and "进入费控商旅" in content:
                    content_has_relevant = True
                
                # 检查是否包含关键词库中的关键词
                for keyword in trigger_keywords:
                    if keyword in content:
                        content_has_relevant = True
                        break
                
                if content_has_relevant:
                    doc["mandatory_score"] = 0.6  # 强制得分权重设为0.6
                    mandatory_docs.append(doc)
                    doc_count += 1
        
        # 2. 关键词匹配
        # 从关键词管理器获取匹配关键词
        keywords = self.keyword_manager.get_keywords()
        keyword_matches = []
        
        # 查找包含关键词的文档，限制数量
        doc_count = 0
        max_docs = 15  # 限制处理的文档数量
        
        for doc in self.data_loader.documents:
            if doc_count >= max_docs:
                break
                
            content = doc["page_content"]
            match_count = 0
            for keyword in keywords:
                if keyword in content:
                    match_count += 1
                    # 更新关键词权重
                    self.keyword_manager.update_weight(keyword)
            if match_count > 0:
                # 计算关键词匹配得分
                doc["keyword_score"] = match_count * 0.3  # 关键词匹配得分0.3
                keyword_matches.append(doc)
                doc_count += 1
        
        # 3. 向量相似度检索
        # 计算查询向量
        query_embedding = self.data_loader.simple_embed(query)
        query_embedding = np.array([query_embedding]).astype('float32')
        
        # 检索最相似的文档
        distances, indices = self.data_loader.vector_store.search(query_embedding, top_k)
        
        similarity_docs = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.data_loader.documents):
                doc = self.data_loader.documents[idx]
                doc["distance"] = float(distances[0][i])  # 转换为Python原生float类型
                # 计算向量相似度得分
                doc["similarity_score"] = (1.0 / (1.0 + doc["distance"])) * 0.1  # 向量相似度0.1
                similarity_docs.append(doc)
        
        # 4. 合并结果
        # 去重
        seen_content = set()
        unique_docs = []
        
        # 先添加强制文档
        for doc in mandatory_docs:
            content = doc["page_content"]
            if content not in seen_content:
                seen_content.add(content)
                unique_docs.append(doc)
        
        # 再添加关键词匹配的文档
        for doc in keyword_matches:
            content = doc["page_content"]
            if content not in seen_content:
                seen_content.add(content)
                unique_docs.append(doc)
        
        # 最后添加相似度高的文档
        for doc in similarity_docs:
            content = doc["page_content"]
            if content not in seen_content:
                seen_content.add(content)
                unique_docs.append(doc)
        
        # 5. 排序
        # 优先按强制得分排序，然后按关键词匹配得分排序，最后按相似度排序
        def sort_key(doc):
            # 强制得分（默认0）
            mandatory_score = doc.get("mandatory_score", 0)
            # 关键词匹配得分（默认0）
            keyword_score = doc.get("keyword_score", 0)
            # 相似度得分（默认0）
            similarity_score = doc.get("similarity_score", 0)
            return (mandatory_score, keyword_score, similarity_score)
        
        unique_docs.sort(key=sort_key, reverse=True)  # 降序排序
        
        # 保留前8个文档
        relevant_docs = unique_docs[:8]
        
        return relevant_docs
    
    def generate_answer(self, query, relevant_docs):
        """基于检索到的文档生成回答"""
        if not relevant_docs:
            return {"type": "no_info", "message": "抱歉，我无法回答这个问题，请转人工客服处理。"}
        
        # 构建提示词，限制文档内容长度
        max_context_length = 1500  # 限制上下文长度
        context_parts = []
        current_length = 0
        
        for doc in relevant_docs:
            doc_content = doc["page_content"]
            # 只添加与查询相关的部分
            if len(doc_content) > 200:
                # 截取前200个字符，确保包含关键信息
                doc_content = doc_content[:200] + "..."
            
            if current_length + len(doc_content) < max_context_length:
                context_parts.append(doc_content)
                current_length += len(doc_content)
            else:
                break
        
        context = "\n".join(context_parts)
        prompt = f"你是一个专业的客户服务助手，只能基于以下提供的资料回答问题，禁止使用资料外的信息：\n\n"
        prompt += f"资料：\n{context}\n\n"
        prompt += f"问题：{query}\n\n"
        prompt += "要求：\n1. 严格基于提供的资料回答，不添加任何资料外的信息\n"
        prompt += "2. 用简洁明了的语言回答\n"
        prompt += "3. 如果资料中没有相关信息，直接回答'抱歉，我无法回答这个问题，请转人工客服处理。'\n"
        prompt += "4. 不要提及'根据资料'、'资料显示'等引导性短语，直接给出答案\n"
        prompt += "5. 对于操作步骤，使用换行符分隔每个步骤，提高可读性\n"
        prompt += "6. 对于多个功能或要点，使用换行符分隔，使回答更加清晰\n"
        
        try:
            # 调用豆包API，添加重试机制
            import time
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.doubao_api_key}"
                    }
                    
                    data = {
                        "model": self.default_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个专业的客户服务助手，严格基于提供的资料回答问题。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                    
                    response = requests.post(self.api_url, headers=headers, data=json.dumps(data, ensure_ascii=False), timeout=20)
                    response.raise_for_status()
                    
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]
                    
                    return {"type": "info", "message": answer}
                    
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        print(f"API调用失败，{retry_delay}秒后重试... (尝试 {attempt+1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"type": "error", "message": "抱歉，系统暂时无法回答您的问题，请稍后再试。"}
    
    def generate_general_answer(self, query):
        """调用豆包大模型自由回答问题"""
        # 构建提示词
        prompt = f"你是一个专业的客户服务助手，请自由回答以下问题：\n\n"
        prompt += f"问题：{query}\n\n"
        prompt += "要求：\n1. 用简洁明了的语言回答\n"
        prompt += "2. 提供准确、有用的信息\n"
        prompt += "3. 不要提及任何关于资料的内容\n"
        
        try:
            # 调用豆包API，添加重试机制
            import time
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.doubao_api_key}"
                    }
                    
                    data = {
                        "model": self.default_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个专业的客户服务助手，自由回答用户的问题。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                    
                    response = requests.post(self.api_url, headers=headers, data=json.dumps(data), timeout=20)
                    response.raise_for_status()
                    
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]
                    
                    return {"type": "general", "message": answer}
                    
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        print(f"API调用失败，{retry_delay}秒后重试... (尝试 {attempt+1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"type": "error", "message": "抱歉，系统暂时无法回答您的问题，请稍后再试。"}
    
    def process_query(self, query):
        """处理用户查询的完整流程"""
        # 检索相关文档
        relevant_docs = self.retrieve_relevant_docs(query)
        
        # 生成回答
        answer = self.generate_answer(query, relevant_docs)
        
        # 如果资料中没有相关信息，修改回答类型为no_info
        if len(relevant_docs) == 0 or answer.get("message") == "抱歉，我无法回答这个问题，请转人工客服处理。":
            answer = {"type": "no_info", "message": "抱歉，我无法回答这个问题，请转人工客服处理。"}
        
        # 更新查询中关键词的权重
        extracted_keywords = self.extract_keywords(query)
        for keyword in extracted_keywords:
            self.keyword_manager.update_weight(keyword)
        
        return answer, relevant_docs
    
    def process_general_query(self, query):
        """处理通用查询，调用豆包大模型自由回答"""
        # 提取关键词并添加到关键词库
        extracted_keywords = self.extract_keywords(query)
        if extracted_keywords:
            self.keyword_manager.add_keywords(extracted_keywords)
            # 更新关键词权重
            for keyword in extracted_keywords:
                self.keyword_manager.update_weight(keyword)
        
        # 生成通用回答
        answer = self.generate_general_answer(query)
        
        return answer
