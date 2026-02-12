import requests

def test_query():
    """测试系统对出差申请问题的回答"""
    url = "http://localhost:8000/api/query"
    data = {
        "text": "我怎么进行 出差申请？"
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        
        print("测试结果:")
        print(f"回答: {result.get('answer', '无回答')}")
        print(f"来源数量: {len(result.get('sources', []))}")
        
        if result.get('sources'):
            print("参考资料:")
            for i, source in enumerate(result['sources']):
                print(f"{i+1}. {source.get('source', '未知来源')}: {source.get('content', '无内容')[:100]}...")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_query()
