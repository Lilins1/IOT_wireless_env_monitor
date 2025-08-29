const { Storage } = require('@google-cloud/storage');
const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
const port = 3000;

const bucketName = 'pub-sub-senso';
const storage = new Storage({ 
  keyFilename: ".env/data-segment-450509-s6-cab3f8e582fc.json" 
});

// 新增：按小时获取合并数据的接口
app.get('/api/hour-data', async (req, res) => {
  //console.log('Received hour-data request')
  try {
    const { date, hour } = req.query;
    
    // 参数验证
    if (!date || !hour) {
      return res.status(400).json({ error: "Missing date or hour parameter" });
    }

    // 构建文件前缀
    const prefix = `DataInJson/${date}/${hour.padStart(2, '0')}`;
    
    // 获取文件列表
    const [files] = await storage.bucket(bucketName).getFiles({ prefix });
    
    // 过滤目录和非JSON文件
    const validFiles = files.filter(file => 
      !file.name.endsWith('/') && 
      file.name.endsWith('.json')
    );

    // 并行获取所有文件内容
    const dataPromises = validFiles.map(async file => {
      try {
        const [content] = await file.download();
        return JSON.parse(content.toString());
      } catch (e) {
        console.error(`Error processing ${file.name}:`, e);
        return null;
      }
    });

    // 等待所有请求完成
    const allData = await Promise.all(dataPromises);
    
    // 合并和清洗数据
    const mergedData = allData
      .filter(Boolean) // 移除失败的数据
      .flat()          // 展平数组
      .map(item => ({
        ...item,
        Temp: parseFloat(item.Temp),
        Humidity: parseFloat(item.Humidity),
        Light: parseInt(item.Light, 10),
        TimeUnix: parseFloat(item.TimeUnix)
      }))
      .sort((a, b) => a.TimeUnix - b.TimeUnix); // 按时间排序

    res.json({
      date,
      hour,
      dataCount: mergedData.length,
      data: mergedData
    });

  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ 
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined 
    });
  }
});

// API to list files
app.get('/api/files', async (req, res) => {
  try {
    const date = req.query.date;
    const prefix = date ? `DataInJson/${date}/` : 'DataInJson/';
    const [files] = await storage.bucket(bucketName).getFiles({ prefix });
    
    const filteredFiles = files
      .filter(file => !file.name.endsWith('/'))
      .map(file => ({
        name: file.name.split('/').pop(),
        path: file.name
      }));
    
    res.json(filteredFiles);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// API to get file content
app.get('/api/file', async (req, res) => {
  try {
    const filePath = req.query.path;
    const [file] = await storage.bucket(bucketName).file(filePath).download();
    res.json(JSON.parse(file.toString()));
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});

