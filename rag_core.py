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
        
        print(f"\n=== 强制检索规则调试与强化 ===")
        print(f"用户查询: {query}")
        
        # 从查询中提取关键词并添加到关键词库
        extracted_keywords = self.extract_keywords(query)
        print(f"从查询中提取的关键词: {extracted_keywords}")
        
        # 添加新关键词到关键词库
        if extracted_keywords:
            self.keyword_manager.add_keywords(extracted_keywords)
            print(f"已将新关键词添加到关键词库")
        
        # 1. 强制检索规则（优先执行）
        print("\n步骤1: 执行强制检索")
        mandatory_docs = []
        
        # 从关键词管理器获取触发关键词
        trigger_keywords = self.keyword_manager.get_keywords()
        
        # 检查是否触发强制检索
        trigger_found = any(keyword in query for keyword in trigger_keywords)
        print(f"触发关键词检查: {'已触发' if trigger_found else '未触发'}")
        
        if trigger_found:
            print("强制检索包含相关内容的文档...")
            for doc in self.data_loader.documents:
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
                    print(f"强制添加文档: {doc['page_content'][:150]}...")
        
        # 2. 关键词匹配
        print("\n步骤2: 执行关键词匹配")
        # 从关键词管理器获取匹配关键词
        keywords = self.keyword_manager.get_keywords()
        keyword_matches = []
        
        # 查找包含关键词的文档
        for doc in self.data_loader.documents:
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
        
        # 打印关键词匹配结果
        print(f"找到 {len(keyword_matches)} 个包含关键词的文档")
        for i, doc in enumerate(keyword_matches[:3]):
            print(f"关键词匹配文档 {i+1}: {doc['page_content'][:100]}...")
        
        # 3. 向量相似度检索
        print("\n步骤3: 执行向量相似度检索")
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
        
        # 打印相似度检索结果
        print(f"检索到 {len(similarity_docs)} 个相似度文档")
        for i, doc in enumerate(similarity_docs[:3]):
            print(f"相似度文档 {i+1} 得分: {doc.get('similarity_score', 0):.4f}, 内容: {doc['page_content'][:100]}...")
        
        # 4. 合并结果
        print("\n步骤4: 合并结果")
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
        print("\n步骤5: 排序结果")
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
        
        # 打印最终结果
        print(f"\n最终保留 {len(relevant_docs)} 个相关文档")
        for i, doc in enumerate(relevant_docs):
            mandatory_score = doc.get("mandatory_score", 0)
            keyword_score = doc.get("keyword_score", 0)
            similarity_score = doc.get("similarity_score", 0)
            print(f"最终文档 {i+1} 得分: 强制={mandatory_score:.2f}, 关键词={keyword_score:.2f}, 相似度={similarity_score:.4f}, 内容: {doc['page_content'][:100]}...")
        
        return relevant_docs
    
    def generate_answer(self, query, relevant_docs):
        """基于检索到的文档生成回答"""
        if not relevant_docs:
            return {"type": "no_info", "message": "抱歉，我无法回答这个问题，请转人工客服处理。"}
        
        # 构建提示词
        context = "\n".join([doc["page_content"] for doc in relevant_docs])
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
            # 调用豆包API
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
            
            print(f"调用豆包API: {self.api_url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data, ensure_ascii=False), timeout=30)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            return {"type": "info", "message": answer}
            
        except Exception as e:
            print(f"调用豆包API失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"type": "error", "message": f"抱歉，系统暂时无法回答您的问题，请稍后再试。错误信息: {str(e)}"}
    
    def generate_general_answer(self, query):
        """调用豆包大模型自由回答问题"""
        # 构建提示词
        prompt = f"你是一个专业的客户服务助手，请自由回答以下问题：\n\n"
        prompt += f"问题：{query}\n\n"
        prompt += "要求：\n1. 用简洁明了的语言回答\n"
        prompt += "2. 提供准确、有用的信息\n"
        prompt += "3. 不要提及任何关于资料的内容\n"
        
        try:
            # 调用豆包API
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
            
            print(f"调用豆包API: {self.api_url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data), timeout=30)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            return {"type": "general", "message": answer}
            
        except Exception as e:
            print(f"调用豆包API失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"type": "error", "message": f"抱歉，系统暂时无法回答您的问题，请稍后再试。错误信息: {str(e)}"}
    
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
