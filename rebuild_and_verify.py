from data_loader import DataLoader
import os

def rebuild_and_verify():
    """重建索引并验证有效性"""
    config = {
        'data_dir': os.path.join(os.path.dirname(__file__), '审核后资料文件夹'),
        'vector_db_path': os.path.join(os.path.dirname(__file__), 'vector_db', 'faiss_index.bin')
    }
    
    loader = DataLoader(config['data_dir'], config['vector_db_path'])
    
    print("=== 步骤1: 重新加载文件 ===")
    files = loader.load_files()
    print(f"文件加载完成，共加载 {len(files)} 个有效文件")
    
    print("\n=== 步骤2: 重新切分文本 ===")
    documents = loader.split_text(files)
    print(f"文本切分完成，共生成 {len(documents)} 个文档块")
    
    # 验证操作步骤是否被正确分块
    print("\n=== 验证操作步骤分块 ===")
    operation_found = False
    for i, doc in enumerate(documents):
        content = doc["page_content"]
        if "登录企业手机银行" in content and "进入费控商旅" in content and "点击出差申请" in content:
            print(f"文档块 {i+1}: 包含完整操作步骤 - {content}")
            operation_found = True
            break
    
    if not operation_found:
        print("警告：未找到包含完整操作步骤的文档块")
    else:
        print("成功：找到包含完整操作步骤的文档块")
    
    print("\n=== 步骤3: 计算嵌入向量 ===")
    embeddings = loader.compute_embeddings(documents)
    print(f"嵌入向量计算完成，共生成 {len(embeddings)} 个向量")
    
    print("\n=== 步骤4: 重建向量库 ===")
    loader.build_vector_store(documents, embeddings)
    print("向量库重建完成")
    
    print("\n=== 步骤5: 验证索引有效性 ===")
    # 重新加载向量库
    loader2 = DataLoader(config['data_dir'], config['vector_db_path'])
    success = loader2.load_vector_store()
    print(f"向量库加载状态: {'成功' if success else '失败'}")
    print(f"重新构建的向量库中的文档数: {len(loader2.documents)}")
    
    # 验证操作步骤是否在向量库中
    operation_in_index = False
    for i, doc in enumerate(loader2.documents):
        content = doc["page_content"]
        if "登录企业手机银行" in content and "进入费控商旅" in content and "点击出差申请" in content:
            print(f"索引中的文档 {i+1}: 包含完整操作步骤 - {content}")
            operation_in_index = True
            break
    
    if not operation_in_index:
        print("警告：向量库中未找到包含完整操作步骤的文档")
    else:
        print("成功：向量库中找到包含完整操作步骤的文档")
    
    print("\n=== 步骤6: 生成索引校验报告 ===")
    print("索引校验报告")
    print("-" * 50)
    print(f"1. 文档加载: 成功加载 {len(files)} 个文件")
    print(f"2. 文本切分: 成功生成 {len(documents)} 个文档块")
    print(f"3. 操作步骤分块: {'成功' if operation_found else '失败'}")
    print(f"4. 嵌入向量计算: 成功生成 {len(embeddings)} 个向量")
    print(f"5. 向量库重建: {'成功' if success else '失败'}")
    print(f"6. 索引有效性: {'成功' if operation_in_index else '失败'}")
    print("-" * 50)
    print("索引校验完成")

if __name__ == "__main__":
    rebuild_and_verify()
