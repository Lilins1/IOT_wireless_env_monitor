import serial
import datetime
import os
import time
import threading
import json
from queue import Queue
import re
from google.cloud import pubsub_v1

# Google Cloud 配置


class SerialDataLogger:
    def __init__(self):
        """配置串口参数"""
        self.ser = serial.Serial(
            port='COM8',
            baudrate=19200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1  # 确保流畅读取
        )
        self.data_queue = Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._save_worker)

    def _extract_data(self, message):
        message = message.replace("\n", " ").replace("\r", " ")
        """Extracting Data"""
        patterns = {
            "Packet": r"#\s+(\d+)",
            "Node": r"Node\s+(\d+)",
            "TX ID": r"TX ID\s+([-\w]+)",
            "Temp": r"Temp\s+([\d.]+)\s*F",
            "Light": r"Light\s+([\d.]+)\s*lx",
            "Time": r"Time\s+([\d:]+)",
            "dT": r"dT\s+([\d:]+)",
            "RSSI": r"RSSI\s+([-\d.]+|---)mW",
            "Humidity": r"Humidity\s+([\d.]+)\s*%",
            "Extrnl": r"Extrnl\s+([\d.]+)\s*mV"
        }

        extracted_data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                extracted_data[key] = match.group(1)

        extracted_data["TimeUnix"] = time.time()  # 当前 Unix 时间戳
        extracted_data["TimeStamp"] = time.strftime("%H:%M:%S", time.localtime())  # 可读时间格式

        #return extracted_data if len(extracted_data) == len(patterns) else None
        return extracted_data if extracted_data else None


    def _save_worker(self):
        """后台存储工作线程"""

        rawMessage = []  # 存储未完整解析的数据
        messages = []
        last_save_time = time.time() 
        while self.running or not self.data_queue.empty():
            try:
                # 获取数据（非阻塞）
                new_data = self.data_queue.get(timeout=0.5)
                rawMessage.append(new_data)

                # 定义匹配模式
                patterns = {
                    "Packet": r"#\s+(\d+)",
                    "END": r"mV"
                }

                # 处理完整的数据块（检查是否包含 "mV"）
                combined_message = "".join(rawMessage)  # 组合所有数据
                if re.search(patterns["END"], combined_message):
                    # 分割数据，取 "mV" 之前的部分（包括 "mV"）
                    message, remaining_data = combined_message.rsplit("mV", 1)
                    message += "mV"  # 重新加上 "mV"

                    # 解析数据
                    parsed_data = self._extract_data(message)
                    if parsed_data:
                        messages.append(parsed_data)

                    # 保留 "mV" 之后的部分，等待下一次循环处理
                    rawMessage = [remaining_data.strip()] if remaining_data.strip() else []

                # 每 10 条数据保存一次 或 每 10 秒保存一次
                if len(messages) >= 10 or (time.time() - last_save_time) > 10:
                    self._save_to_file(messages)
                    messages = []
                    last_save_time = time.time()

            except Exception as e:
                pass

        # 退出循环后，保存剩余的数据
        if messages:
            self._save_to_file(messages)

    

    def _save_to_file(self, messages):
        """存储数据到 JSON 文件"""
        now = datetime.datetime.now()
        save_path = os.path.join(
            now.strftime('%Y%m%d'),
            now.strftime('%H%M')
        )
        os.makedirs(save_path, exist_ok=True)
        
        filename = os.path.join(save_path, 'data.json')

        # 读取已有的 JSON 数据（如果文件已存在）
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        # 添加新数据
        existing_data.extend(messages)

        # 重新写入 JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        print(f"[{now}] 已保存{len(messages)}条数据到 {filename}")

    def run(self):
        """主运行循环"""
        self.worker_thread.start()
        print("开始监听串口数据...")

        try:
            while self.running:
                if self.ser.in_waiting > 0:
                    # 读取所有可用数据
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore').lstrip()
                    print(data.strip())  # 控制台输出
                    self.data_queue.put(data.strip())  # 直接存储所有数据
                
                time.sleep(0.2)  # 轮询间隔

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
