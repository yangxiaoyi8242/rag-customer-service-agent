import json
import os
from collections import defaultdict

class KeywordManager:
    def __init__(self, keyword_file="keyword_library.json"):
        self.keyword_file = keyword_file
        self.keywords = self._load_keywords()
        self.keyword_weights = defaultdict(float)
        self._load_weights()
    
    def _load_keywords(self):
        """从文件加载关键词库"""
        if os.path.exists(self.keyword_file):
            try:
                with open(self.keyword_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载关键词库失败: {e}")
                return []
        else:
            # 初始化默认关键词
            default_keywords = [
                "出差申请", "提交", "出差申请单", "新建出差申请", "申请出差", 
                "发票导入", "导入发票", "票据夹", "报销明细", "登录", 
                "企业手机银行", "费控商旅", "新建", "申请单"
            ]
            self._save_keywords(default_keywords)
            return default_keywords
    
    def _save_keywords(self, keywords):
        """保存关键词库到文件"""
        try:
            with open(self.keyword_file, 'w', encoding='utf-8') as f:
                json.dump(keywords, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存关键词库失败: {e}")
            return False
    
    def _load_weights(self):
        """加载关键词权重"""
        # 初始化权重，默认值为1.0
        for keyword in self.keywords:
            self.keyword_weights[keyword] = 1.0
    
    def add_keyword(self, keyword):
        """添加新关键词"""
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            self.keyword_weights[keyword] = 1.0
            self._save_keywords(self.keywords)
            return True
        return False
    
    def add_keywords(self, keywords):
        """批量添加关键词"""
        added = False
        for keyword in keywords:
            if self.add_keyword(keyword):
                added = True
        return added
    
    def update_weight(self, keyword, increment=0.1):
        """更新关键词权重"""
        if keyword in self.keyword_weights:
            self.keyword_weights[keyword] += increment
            # 限制最大权重为5.0
            self.keyword_weights[keyword] = min(self.keyword_weights[keyword], 5.0)
            return True
        return False
    
    def get_keywords(self):
        """获取所有关键词"""
        return self.keywords
    
    def get_weighted_keywords(self):
        """获取带权重的关键词"""
        return dict(self.keyword_weights)
    
    def get_top_keywords(self, top_n=10):
        """获取权重最高的关键词"""
        sorted_keywords = sorted(self.keyword_weights.items(), 
                               key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_keywords[:top_n]]

# 测试代码
if __name__ == "__main__":
    manager = KeywordManager()
    print("当前关键词库:", manager.get_keywords())
    
    # 测试添加关键词
    manager.add_keyword("费用报销")
    manager.add_keyword("商旅预订")
    print("添加后关键词库:", manager.get_keywords())
    
    # 测试更新权重
    manager.update_weight("出差申请")
    manager.update_weight("发票导入")
    print("带权重的关键词:", manager.get_weighted_keywords())
    
    # 测试获取权重最高的关键词
    print("权重最高的关键词:", manager.get_top_keywords())
