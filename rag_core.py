import requests
import json
import numpy as np

class RAGCore:
    def __init__(self, data_loader, doubao_api_key):
        self.data_loader = data_loader
        self.doubao_api_key = doubao_api_key
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    
    def retrieve_relevant_docs(self, query, top_k=3):
        """检索与查询相关的文档"""
        if not self.data_loader.vector_store:
            return []
        
        # 计算查询向量
        query_embedding = self.data_loader.simple_embed(query)
        query_embedding = np.array([query_embedding]).astype('float32')
        
        # 检索最相似的文档
        distances, indices = self.data_loader.vector_store.search(query_embedding, top_k)
        
        relevant_docs = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.data_loader.documents):
                doc = self.data_loader.documents[idx]
                doc["distance"] = distances[0][i]
                relevant_docs.append(doc)
        
        # 过滤掉相似度太低的文档
        relevant_docs = [doc for doc in relevant_docs if doc["distance"] < 1.0]
        
        return relevant_docs
    
    def generate_answer(self, query, relevant_docs):
        """基于检索到的文档生成回答"""
        if not relevant_docs:
            return "抱歉，我无法回答这个问题，请转人工客服处理。"
        
        # 构建提示词
        context = "\n".join([doc["page_content"] for doc in relevant_docs])
        prompt = f"你是一个专业的客户服务助手，只能基于以下提供的资料回答问题，禁止使用资料外的信息：\n\n"
        prompt += f"资料：\n{context}\n\n"
        prompt += f"问题：{query}\n\n"
        prompt += "要求：\n1. 严格基于提供的资料回答，不添加任何资料外的信息\n"
        prompt += "2. 用简洁明了的语言回答\n"
        prompt += "3. 如果资料中没有相关信息，直接回答'抱歉，我无法回答这个问题，请转人工客服处理。'\n"
        prompt += "4. 不要提及'根据资料'、'资料显示'等引导性短语，直接给出答案\n"
        
        try:
            # 调用豆包API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.doubao_api_key}"
            }
            
            data = {
                "model": "ep-20260211150348-9wkmx",
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
            
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data), timeout=30)
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            return answer
            
        except Exception as e:
            print(f"调用豆包API失败: {str(e)}")
            return "抱歉，系统暂时无法回答您的问题，请稍后再试。"
    
    def process_query(self, query):
        """处理用户查询的完整流程"""
        # 检索相关文档
        relevant_docs = self.retrieve_relevant_docs(query)
        
        # 生成回答
        answer = self.generate_answer(query, relevant_docs)
        
        return answer, relevant_docs
