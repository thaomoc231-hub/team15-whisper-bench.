import csv
import time
import psutil
import torch
from jiwer import wer

# 1. Hàm đo lượng RAM tối đa (MB)
def get_peak_ram():
    return psutil.Process().memory_info().rss / (1024 * 1024)

# 2. Hàm tính WER
def calculate_wer(reference_text, hypothesis_text):
    return wer(reference_text, hypothesis_text)

# 3. Hàm lưu kết quả ra file CSV
def save_results_to_csv(filename, data):
    headers = ["Model", "Audio_File", "Execution_Time_Sec", "Peak_RAM_MB", "WER"]
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # Nếu file chưa có nội dung thì ghi header
            writer.writerow(headers)
        writer.writerow(data)

if __name__ == "__main__":
    print("Benchmark Script Ready!")
