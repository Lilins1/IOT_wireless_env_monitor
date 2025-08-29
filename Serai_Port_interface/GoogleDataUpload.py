import serial
import datetime
import os
import time
import threading
import json
from queue import Queue
import re
from google.cloud import storage  


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

        # 配置 Google Cloud Storage
        self.bucket_name = "pub-sub-senso"  # 你的 GCS 存储桶
        self.storage_client = storage.Client.from_service_account_json(".env/data-segment-450509-s6-cab3f8e582fc.json")
        self.bucket = self.storage_client.bucket(self.bucket_name)


    def _extract_data(self, message):
        print(repr(message))
        message = message.replace("\n", " ").replace("\r", " ")
        message = re.sub(r"\s+", " ", message).strip()

        print(repr(message))
        """Extracting Data"""
        patterns = {
            "Packet": r"#\s*(\d+)\s*\|",
            "Node": r"Node\s*(\d+)\s*\|",
            # "TX ID": r"TX ID\s+([-\w]+)",
            "Temp": r"Temp\s*([\d.]+)\s*F\s*\|",
            "Light": r"Light\s*([\d.]+)\s*lx",
            # "Time": r"Time\s+([\d:]+)",
            "dT": r"dT\s*([\d:]+)\s*\|",
            "RSSI": r"RSSI\s*([-\d.]+|---)mW\s*\|",
            "Humidity": r"Humidity\s*([\d.]+)\s*%\s*\|",
            "Extrnl": r"Extrnl\s*([\d.]+)\s*mV"
        }

        extracted_data = {}
        # 初始化所有字段为 'Unreceived'
        extracted_data = {key: '---' for key in patterns.keys()}  # 修复1：直接遍历键

        for key, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                extracted_data[key] = match.group(1)

        
        extracted_data["TimeStamp"] = time.strftime("%H:%M:%S", time.localtime())  # 可读时间格式
        extracted_data["TimeUnix"] = time.time()  # 当前 Unix 时间戳
        

        # return extracted_data if len(extracted_data) == len(patterns) else None
        # return extracted_data if extracted_data else None
        return extracted_data


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
        date_folder = now.strftime('%Y-%m-%d')
        time_stamp = now.strftime('%H%M')

        local_dir = os.path.join("Data", date_folder)
        os.makedirs(local_dir, exist_ok=True)

        filename = os.path.join(local_dir, f"{time_stamp}.json")

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

        print(f"[{now}] Save{len(messages)} Messages into {filename}")

        self._upload_to_gcs(filename, date_folder, time_stamp)

    def _upload_to_gcs(self, local_file_path, date_folder, time_stamp):
        """上传 JSON 文件到 Google Cloud Storage"""
        try:
            # 构造 GCS 存储路径：dataintxt/YYYY-MM-DD/HHMM.json
            destination_blob_name = f"DataInJson/{date_folder}/{time_stamp}.json"

            # 上传文件
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_file_path)

            print(f"Upload Sucess: {destination_blob_name}")
        except Exception as e:
            print(f"Upload Failed: {e}")


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
