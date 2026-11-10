# Giao diện tích hợp v1.0 — Hưng ↔ Huệ

## Phạm vi

Chương trình Hưng cung cấp chuẩn hóa audio và Whisper CPU; chương trình Huệ gọi tiến trình đó rồi đo,
tính WER và lưu CSV. Bộ đo không nằm trong gói này.

## Input

- prepare: video/audio có audio track đầu tiên, đường dẫn đầu ra WAV mới.
- transcribe: WAV mono PCM signed 16-bit 16000 Hz không rỗng/không bị cắt payload;
  checkpoint Whisper .pt tải sẵn, ngôn ngữ ISO (`ko`, `vi`, `en`), threads và beam-size dương.
- model chuẩn ban đầu: tiny **đa ngôn ngữ**. Cấu hình mặc định: CPU, fp32, threads=4, beam_size=5,
  temperature=0, task=transcribe, condition_on_previous_text=False. Không đổi giữa các lần so sánh.
- Không có tải model trong worker. Mỗi lần gọi cần một thư mục output chưa tồn tại.

## Process contract

```bash
python -m subtitle_bench.cli transcribe --audio AUDIO.wav --model TINY.pt --language ko --threads 4 --beam-size 5 --output NEW_RESULT_DIR
```

Mã 0: các file đã ghi đủ và result.json có status=complete. Mã 1: lỗi cài đặt/đầu vào/runtime được xử lý;
mã 2: argparse báo cú pháp sai; tín hiệu hoặc lỗi runtime bất ngờ cũng có thể trả mã khác 0.
Partner coi **mọi mã khác 0 là thất bại**, lưu stdout/stderr, không dùng làm mẫu đo thành công.
stdout thành công là đường dẫn thư mục kết quả; thông báo lỗi đi stderr.
Chạy mỗi phép đo bằng tiến trình Python mới. Không đo nhiều engine song song trên một máy.

## Output

| File | Nội dung |
|---|---|
| transcript.txt | UTF-8, ghép text segment bằng khoảng trắng, giữ chữ/dấu câu; không tự chuẩn hóa WER |
| subtitles.srt | timestamp dạng HH:MM:SS,mmm, text theo segment Whisper |
| segments.json | metadata và list {start, end, text} tính bằng giây |
| result.json | schema_version=1.0, status=complete, audio_seconds, settings, outputs |

settings có audio/model path và SHA-256, device/precision/language/threads/beam_size và phiên bản tích hợp.
outputs có đường dẫn **tương đối** của ba file, bytes và SHA-256. Partner dùng `verify_result(output)`
hoặc `lecture-subtitles verify OUTPUT` để kiểm tra trước khi sử dụng. Kiểm tra hash phát hiện thay đổi file,
không thay thế việc người nghe xác nhận nội dung/timestamp.
Manifest của audio không lời vẫn có thể complete nhưng TXT/SRT rỗng: đó là một kết quả kỹ thuật hợp lệ;
phép acceptance trên mẫu có giọng nói yêu cầu đầu ra không rỗng.

## Đo quanh chỗ nào?

Xem examples/partner_adapter.py: đo quanh subprocess chạy transcribe; verify và tính WER thực hiện sau.
Thời gian này bao gồm khởi động Python, import, kiểm tra/đọc WAV, nạp mô hình, nhận dạng, hash và xuất file.
Không gọi là thời gian suy luận thuần. Không bao gồm tải model, FFmpeg hoặc tính WER.
Nếu muốn loại bước hash/IO hoặc chỉ đo inference, cần thống nhất một giao diện đo khác cho cả hai engine.
Máy, model family, audio, ngôn ngữ, số luồng và tùy chọn giải mã phải được lưu với CSV của Huệ.
Giống cấu hình không bảo đảm hai engine có cùng toàn bộ chi tiết giải mã hoặc kết quả giống hệt.

## Việc cả nhóm còn cần chốt

Ai triển khai faster-whisper; cỡ model cuối; clip và bản chuẩn do cả hai kiểm tra; chuẩn hóa WER;
số lần lặp; định nghĩa warmup; cách tính RAM. Không lấy phụ đề Whisper làm bản chuẩn.
