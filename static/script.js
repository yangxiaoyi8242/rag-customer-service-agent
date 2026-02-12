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
        
        // 处理不同类型的回答
        if (typeof content === 'object') {
            contentDiv.textContent = content.message;
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        
        // 如果是no_info类型，显示询问用户是否需要调用豆包回答的按钮
        if (typeof content === 'object' && content.type === 'no_info') {
            const buttonDiv = document.createElement('div');
            buttonDiv.className = 'button-container';
            
            const generalButton = document.createElement('button');
            generalButton.className = 'general-button';
            generalButton.textContent = '调用豆包回答';
            generalButton.addEventListener('click', function() {
                console.log('调用豆包回答按钮被点击');
                // 尝试获取用户查询内容
                const userMessages = document.querySelectorAll('.user-message');
                if (userMessages.length > 0) {
                    // 获取最后一条用户消息
                    const lastUserMessage = userMessages[userMessages.length - 1];
                    const messageContent = lastUserMessage.querySelector('.message-content');
                    if (messageContent) {
                        const userQuery = messageContent.textContent;
                        console.log('用户查询内容:', userQuery);
                        handleGeneralQuery(userQuery);
                        return;
                    }
                }
                
                // 如果找不到用户查询，尝试从当前消息中提取
                console.error('找不到用户查询内容，尝试从当前消息中提取');
                // 显示错误消息
                addMessage('bot', '抱歉，无法获取您的查询内容，请重新发送问题。');
            });
            
            buttonDiv.appendChild(generalButton);
            messageDiv.appendChild(buttonDiv);
            console.log('按钮已添加到DOM');
        }
        
        // 添加来源信息
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            
            // 创建标题栏
            const sourcesHeader = document.createElement('div');
            sourcesHeader.className = 'sources-header';
            sourcesHeader.textContent = '参考资料 (点击展开)';
            sourcesHeader.style.cursor = 'pointer';
            sourcesHeader.style.fontWeight = 'bold';
            sourcesDiv.appendChild(sourcesHeader);
            
            // 创建内容容器
            const sourcesContent = document.createElement('div');
            sourcesContent.className = 'sources-content';
            sourcesContent.style.display = 'none';
            
            sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.textContent = `${source.source}: ${source.content.substring(0, 100)}...`;
                sourcesContent.appendChild(sourceItem);
            });
            
            sourcesDiv.appendChild(sourcesContent);
            
            // 添加点击事件监听器
            sourcesHeader.addEventListener('click', function() {
                if (sourcesContent.style.display === 'none') {
                    sourcesContent.style.display = 'block';
                    sourcesHeader.textContent = '参考资料 (点击收起)';
                } else {
                    sourcesContent.style.display = 'none';
                    sourcesHeader.textContent = '参考资料 (点击展开)';
                }
            });
            
            messageDiv.appendChild(sourcesDiv);
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // 处理通用查询
    async function handleGeneralQuery(query) {
        console.log('handleGeneralQuery 函数被调用，查询内容:', query);
        const chatContainer = document.getElementById('chat-container');
        
        // 显示加载状态
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading';
        loadingElement.id = 'loading-indicator';
        chatContainer.appendChild(loadingElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        console.log('加载状态已显示');
        
        try {
            // 发送通用查询
            console.log('开始发送通用查询请求');
            const response = await fetch('/api/general_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'text': query
                })
            });
            
            console.log('响应状态码:', response.status);
            if (!response.ok) {
                throw new Error('查询失败，状态码:', response.status);
            }
            
            const data = await response.json();
            console.log('响应数据:', data);
            
            // 移除加载状态
            document.getElementById('loading-indicator').remove();
            console.log('加载状态已移除');
            
            // 添加通用查询的回答
            console.log('开始添加通用查询回答');
            addGeneralMessage(data.answer);
            console.log('通用查询回答已添加');
        } catch (error) {
            // 移除加载状态
            document.getElementById('loading-indicator').remove();
            console.log('加载状态已移除（错误情况）');
            
            // 显示错误消息
            addMessage('bot', '抱歉，处理您的请求时出错，请稍后重试。');
            console.error('错误详情:', error);
        }
    }
    
    // 添加通用查询的回答
    function addGeneralMessage(content) {
        const chatContainer = document.getElementById('chat-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message general-message';
        
        // 添加消息内容
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content.message;
        messageDiv.appendChild(contentDiv);
        
        // 添加来源信息
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'message-source';
        sourceDiv.textContent = '来源: 豆包大模型';
        messageDiv.appendChild(sourceDiv);
        
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