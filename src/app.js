/**
 * Directly fetches and displays the content of DataSet_test.TXT.
 */
// 导入storage实例
import { storage } from './firebase.js';
import { ref, uploadBytes } from "firebase/storage";

async function uploadFile() {
  const fileInput = document.getElementById('fileInput');
  const statusDiv = document.getElementById('uploadStatus');
  
  if (!fileInput.files[0]) {
    statusDiv.innerHTML = '<div class="error">请先选择文件</div>';
    return;
  }

  const file = fileInput.files[0];
  const storageRef = ref(storage, `uploads/${file.name}`);

  try {
    await uploadBytes(storageRef, file);
    statusDiv.innerHTML = '<div class="success">文件上传成功！</div>';
  } catch (error) {
    console.error('上传失败:', error);
    statusDiv.innerHTML = `<div class="error">上传失败: ${error.message}</div>`;
  }
}

// 暴露函数到全局作用域以便HTML调用
window.uploadFile = uploadFile;

function fetchAndDisplayData() {
    // 这里使用相对路径，假设 DataSet_test.TXT 与 index.html、app.js 位于同一目录下
    fetch('DataSet_test.TXT')
      .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.text();
      })
      .then(text => {
        // 直接显示文件内容，保持原格式（换行符等）
        document.getElementById('packetContainer').innerText = text;
      })
      .catch(error => {
        console.error('Fetch Error:', error);
        document.getElementById('packetContainer').innerHTML = `
          <div class="error">
            Failed to load data: ${error.message}<br>
            Please check that:<br>
            1. The server is running from the correct directory.<br>
            2. The file "DataSet_test.TXT" exists in the same directory.<br>
            3. File name case sensitivity.
          </div>
        `;
      });
  }
  
  // 当 DOM 加载完成后，加载数据；若需要定时刷新，可添加 setInterval
  document.addEventListener('DOMContentLoaded', () => {
    fetchAndDisplayData();
    // 如果需要每 5 秒自动刷新，可以取消下一行的注释
    setInterval(fetchAndDisplayData, 20000);
  });
  