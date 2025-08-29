import serial
import datetime
import os
import time
import threading
from queue import Queue

class SerialDataLogger:
    def __init__(self):
        # 配置串口参数
        self.ser = serial.Serial(
            port='COM8',
            baudrate=19200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout= 5  # 更灵敏的超时设置
        )
        self.buffer = ''
        self.data_queue = Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._save_worker)

    def _process_buffer(self):
        """处理缓冲区中的完整消息"""
        while True:
            start = self.buffer.find('#package')
            if start == -1:
                break

            end = self.buffer.find('mV', start + 8)
            if end == -1:
                break

            # 提取并发送有效消息
            message = self.buffer[start+8:end].strip()
            print(message)#consloe输出
            self.data_queue.put(message)
            
            # 更新缓冲区
            self.buffer = self.buffer[end+2:]

    def _save_worker(self):
        """后台存储工作线程"""
        messages = []
        while self.running or not self.data_queue.empty():
            try:
                # 非阻塞获取数据
                message = self.data_queue.get(timeout=0.5)
                messages.append(message)

                # 达到10条时保存
                if len(messages) >= 10:
                    self._save_to_file(messages)
                    messages = []
            except:
                continue
        
        # 保存剩余数据
        if messages:
            self._save_to_file(messages)

    def _save_to_file(self, messages):
        """实际存储操作"""
        now = datetime.datetime.now()
        save_path = os.path.join(
            now.strftime('%Y%m%d'),
            now.strftime('%H%M')
        )
        os.makedirs(save_path, exist_ok=True)
        
        filename = os.path.join(save_path, 'data.txt')
        with open(filename, 'a', encoding='utf-8') as f:  # 改为追加模式
            f.write('\n'.join(messages) + '\n')
        print(f"[{now}] Save{len(messages)} message to {filename}")

    def run(self):
        """主运行循环"""
        self.worker_thread.start()
        print("Listening...")
        
        try:
            while self.running:
                # 持续读取数据
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')

                    # **先打印所有收到的数据**
                    #print(f"Raw Data:____________________________________{data}Raw END____________________________________")

                    self.buffer += data
                    self._process_buffer()
                
                time.sleep(0.2)  # 更灵敏的轮询间隔

        except KeyboardInterrupt:
            self.stop()
        finally:
            self.ser.close()

    def stop(self):
        """安全停止服务"""
        self.running = False
        self.worker_thread.join()
        print("Stoped")

if __name__ == "__main__":
    logger = SerialDataLogger()
    try:
        logger.run()
    except Exception as e:
        print(f"发生错误：{str(e)}")
        logger.stop()