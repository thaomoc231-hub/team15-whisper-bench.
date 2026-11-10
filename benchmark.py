import csv
import time
import psutil
import resource  # Dùng trên Linux / WSL để đo Peak RAM chuẩn xác
import torch
from jiwer import wer

# 1. Hàm đo lượng RAM đỉnh (Peak RAM) chuẩn xác trên Linux/WSL
def get_peak_ram_mb():
    max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return max_rss / 1024.0

# 2. Hàm tính WER (đã thêm chuẩn hóa chữ thường và làm sạch khoảng trắng)
def calculate_wer(reference_text, hypothesis_text):
    ref = reference_text.lower().strip()
    hyp = hypothesis_text.lower().strip()
    return wer(ref, hyp)

# 3. Hàm lưu kết quả ra file CSV
def save_results_to_csv(filename, data):
    headers = ["Model", "Audio_File", "Execution_Time_Sec", "Peak_RAM_MB", "WER"]
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # Ghi header nếu file mới
            writer.writerow(headers)
        writer.writerow(data)

# 4. Hàm mẫu đo một tiến trình benchmark
def run_benchmark_example(model_name, audio_path, ref_text, transcribe_func):
    start_time = time.perf_counter()
    
    # Thực hiện nhận diện giọng nói
    hyp_text = transcribe_func(audio_path)
    
    execution_time = time.perf_counter() - start_time
    peak_ram = get_peak_ram_mb()
    current_wer = calculate_wer(ref_text, hyp_text)
    
    return [model_name, audio_path, round(execution_time, 4), round(peak_ram, 2), round(current_wer, 4)]

if __name__ == "__main__":
    print("Benchmark Script Ready!")
