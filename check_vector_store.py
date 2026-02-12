from data_loader import DataLoader
import os

def check_vector_store():
    """检查向量库状态和加载的文档"""
    config = {
        'data_dir': os.path.join(os.path.dirname(__file__), '审核后资料文件夹'),
        'vector_db_path': os.path.join(os.path.dirname(__file__), 'vector_db', 'faiss_index.bin')
    }
    
    loader = DataLoader(config['data_dir'], config['vector_db_path'])
    
    # 加载向量库
    success = loader.load_vector_store()
    print(f"向量库加载状态: {'成功' if success else '失败'}")
    print(f"当前向量库中的文档数: {len(loader.documents)}")
    
    # 打印前10个文档的内容预览
    print('\n前10个文档的内容预览:')
    for i, doc in enumerate(loader.documents[:10]):
        content = doc["page_content"]
        print(f'文档 {i+1}: {content[:150]}...')
        # 检查是否包含出差申请相关内容
        if "出差申请" in content:
            print(f"  注意: 此文档包含出差申请相关内容")
    
    # 检查文档中是否包含"登录企业手机银行"相关内容
    print('\n检查是否有文档包含"登录企业手机银行"相关内容:')
    found = False
    for i, doc in enumerate(loader.documents):
        if "登录企业手机银行" in doc["page_content"]:
            print(f'文档 {i+1}: 包含相关内容 - {doc["page_content"][:150]}...')
            found = True
    
    if not found:
        print('没有找到包含"登录企业手机银行"相关内容的文档')

if __name__ == "__main__":
    check_vector_store()
