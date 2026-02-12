from data_loader import DataLoader
import os

def check_and_rebuild():
    """检查向量库中是否包含特定内容的文档，并尝试重新构建向量库"""
    config = {
        'data_dir': os.path.join(os.path.dirname(__file__), '审核后资料文件夹'),
        'vector_db_path': os.path.join(os.path.dirname(__file__), 'vector_db', 'faiss_index.bin')
    }
    
    loader = DataLoader(config['data_dir'], config['vector_db_path'])
    
    # 1. 检查当前向量库
    print("=== 检查当前向量库 ===")
    success = loader.load_vector_store()
    print(f"向量库加载状态: {'成功' if success else '失败'}")
    print(f"当前向量库中的文档数: {len(loader.documents)}")
    
    # 检查是否有文档包含"登录企业手机银行"相关内容
    found = False
    for i, doc in enumerate(loader.documents):
        content = doc["page_content"]
        if "登录企业手机银行" in content:
            print(f'文档 {i+1}: 包含相关内容 - {content}')
            found = True
    
    if not found:
        print('没有找到包含"登录企业手机银行"相关内容的文档')
    
    # 2. 重新加载文件并构建向量库
    print("\n=== 重新构建向量库 ===")
    print("正在加载文件...")
    files = loader.load_files()
    print(f"文件加载完成，共加载 {len(files)} 个有效文件")
    
    print("\n正在切分文本...")
    documents = loader.split_text(files)
    print(f"文本切分完成，共生成 {len(documents)} 个文档块")
    
    # 检查切分后的文档是否包含相关内容
    print("\n检查切分后的文档是否包含相关内容:")
    found_in_new = False
    for i, doc in enumerate(documents):
        content = doc["page_content"]
        if "登录企业手机银行" in content:
            print(f'文档块 {i+1}: 包含相关内容 - {content}')
            found_in_new = True
    
    if not found_in_new:
        print('切分后的文档中也没有找到包含"登录企业手机银行"相关内容的文档块')
    
    # 3. 计算嵌入向量并构建向量库
    print("\n正在计算嵌入向量...")
    embeddings = loader.compute_embeddings(documents)
    print(f"嵌入向量计算完成，共生成 {len(embeddings)} 个向量")
    
    print("\n正在构建向量库...")
    loader.build_vector_store(documents, embeddings)
    print("向量库构建完成")
    
    # 4. 再次检查重新构建的向量库
    print("\n=== 检查重新构建的向量库 ===")
    loader2 = DataLoader(config['data_dir'], config['vector_db_path'])
    success2 = loader2.load_vector_store()
    print(f"向量库加载状态: {'成功' if success2 else '失败'}")
    print(f"重新构建的向量库中的文档数: {len(loader2.documents)}")
    
    # 检查是否有文档包含"登录企业手机银行"相关内容
    found_after_rebuild = False
    for i, doc in enumerate(loader2.documents):
        content = doc["page_content"]
        if "登录企业手机银行" in content:
            print(f'文档 {i+1}: 包含相关内容 - {content}')
            found_after_rebuild = True
    
    if not found_after_rebuild:
        print('重新构建的向量库中也没有找到包含"登录企业手机银行"相关内容的文档')
    else:
        print('成功在重新构建的向量库中找到包含"登录企业手机银行"相关内容的文档')

if __name__ == "__main__":
    check_and_rebuild()
