document.addEventListener('DOMContentLoaded', function() {
    // 加载系统状态
    loadStatus();
    
    // 绑定查询表单提交事件
    document.getElementById('query-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const input = document.getElementById('query-input');
        const chatContainer = document.getElementById('chat-container');
        const query = input.value.trim();
        
        if (!query) return;
        
        // 添加用户消息
        addMessage('user', query);
        
        // 清空输入框
        input.value = '';
        
        // 显示加载状态
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading';
        loadingElement.id = 'loading-indicator';
        chatContainer.appendChild(loadingElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        try {
            // 发送查询
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'text': query
                })
            });
            
            if (!response.ok) {
                throw new Error('查询失败');
            }
            
            const data = await response.json();
            
            // 移除加载状态
            document.getElementById('loading-indicator').remove();
            
            // 添加机器人回复
            addMessage('bot', data.answer, data.sources);
        } catch (error) {
            // 移除加载状态
            document.getElementById('loading-indicator').remove();
            
            // 显示错误消息
            addMessage('bot', '抱歉，处理您的请求时出错，请稍后重试。');
            console.error(error);
        }
    });
    
    // 绑定上传表单提交事件
    document.getElementById('upload-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('file-input');
        const uploadStatus = document.getElementById('upload-status');
        
        if (!fileInput.files.length) {
            uploadStatus.textContent = '请选择要上传的文件';
            return;
        }
        
        // 显示上传状态
        uploadStatus.textContent = '正在上传...';
        
        try {
            // 逐个上传文件
            for (let i = 0; i < fileInput.files.length; i++) {
                // 创建FormData对象
                const formData = new FormData();
                formData.append('file', fileInput.files[i]);
                
                // 发送上传请求
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('上传失败');
                }
                
                const data = await response.json();
            }
            
            // 显示上传成功消息
            uploadStatus.textContent = '文件上传成功，向量库已更新';
            
            // 重置文件输入
            fileInput.value = '';
            
            // 重新加载状态
            loadStatus();
        } catch (error) {
            uploadStatus.textContent = '上传失败: ' + error.message;
            console.error(error);
        }
    });
    
    // 添加消息到聊天容器
    function addMessage(type, content, sources = []) {
        const chatContainer = document.getElementById('chat-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        // 添加消息内容
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
        
        // 添加来源信息
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.textContent = '参考资料:';
            
            sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.textContent = `${source.source}: ${source.content.substring(0, 100)}...`;
                sourcesDiv.appendChild(sourceItem);
            });
            
            messageDiv.appendChild(sourcesDiv);
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // 加载系统状态
    async function loadStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error('获取状态失败');
            }
            
            const data = await response.json();
            const statusInfo = document.getElementById('status-info');
            
            statusInfo.innerHTML = `
                <p>向量库状态: ${data.vector_store_status}</p>
                <p>文档数量: ${data.document_count}</p>
                <p>资料目录: ${data.data_dir}</p>
            `;
        } catch (error) {
            console.error('加载状态失败:', error);
        }
    }
});