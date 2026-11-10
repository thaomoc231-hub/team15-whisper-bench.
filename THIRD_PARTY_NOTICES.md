# Sources and licenses — phạm vi Hưng

| Thành phần | Vai trò | Giấy phép / nguồn |
|---|---|---|
| Whisper | Nhận dạng âm thanh | MIT — https://github.com/openai/whisper |
| FFmpeg | Trích và chuyển đổi audio | Phụ thuộc build LGPL/GPL — https://ffmpeg.org/legal.html |
| PyTorch | Runtime Whisper | BSD-style — https://github.com/pytorch/pytorch/blob/main/LICENSE |

Script không sao chép mô hình nhận dạng và không đóng gói trọng số trong bản giao.
Audio mẫu jfk.flac được lấy từ tests/ của kho Whisper, kèm đầy đủ MIT notice của OpenAI
trong examples/sample/WHISPER_LICENSE.txt; nguồn và hash nằm trong source.json.
Giữ nguyên giấy phép/thông báo của bên thứ ba khi phân phối lại; kiểm tra ffmpeg -version
để xác định build thực tế. Phụ thuộc gián tiếp được ghi trong lock môi trường sau cài đặt.
Giấy phép MIT ở LICENSE áp dụng cho phần mã tích hợp trong gói này.

Tham khảo: Radford et al., Robust Speech Recognition via Large-Scale Weak Supervision, ICML 2023,
https://proceedings.mlr.press/v202/radford23a.html .
