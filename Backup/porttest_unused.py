import serial
import datetime
import os
import time
import threading
from queue import Queue

class SerialDataLogger:
    def __init__(self):
        """配置串口参数"""
        self.ser = serial.Serial(
            port='COM8',
            baudrate=19200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1  # 设置超时以确保流畅读取
        )
        self.data_queue = Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._save_worker)

    def _save_worker(self):
        """后台存储工作线程"""
        messages = []
        while self.running or not self.data_queue.empty():
            try:
                # 获取数据（非阻塞）
                message = self.data_queue.get(timeout=0.5)
                messages.append(message)

                # 每10条数据保存一次
                if len(messages) >= 10:
                    self._save_to_file(messages)
                    messages = []
            except:
                continue
        
        # 保存剩余数据
        if messages:
            self._save_to_file(messages)

    def _save_to_file(self, messages):
        """存储数据到文件"""
        now = datetime.datetime.now()
        save_path = os.path.join(
            now.strftime('%Y%m%d'),
            now.strftime('%H%M')
        )
        os.makedirs(save_path, exist_ok=True)
        
        filename = os.path.join(save_path, 'data.txt')
        with open(filename, 'a', encoding='utf-8') as f:
            f.write('\n'.join(messages) + '\n')
        print(f"[{now}] 已保存{len(messages)}条数据到 {filename}")

    def run(self):
        """主运行循环"""
        self.worker_thread.start()
        print("开始监听串口数据...")

        try:
            while self.running:
                if self.ser.in_waiting > 0:
                    # 读取所有可用数据
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    print(data.strip())  # 控制台输出
                    self.data_queue.put(data.strip())  # 直接存储所有数据
                
                time.sleep(0.1)  # 轮询间隔

        except KeyboardInterrupt:
            self.stop()
        finally:
            self.ser.close()

    def stop(self):
        """安全停止程序"""
        self.running = False
        self.worker_thread.join()
        print("服务已安全停止")

if __name__ == "__main__":
    logger = SerialDataLogger()
    try:
        logger.run()
    except Exception as e:
        print(f"发生错误：{str(e)}")
        logger.stop()
