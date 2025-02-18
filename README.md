# AUTOMATION HAHA WALLET với Selenium python

## Chức năng

- **Faucet ETH từ Google**: Nhận ETH miễn phí từ trang faucet của Google.
- **Check-in hằng ngày**: Tự động thực hiện check-in trên các nền tảng hỗ trợ.
- **Chuyển ETH trên Sepolia**: Tự động gửi ETH từ ví chính sang ví thông minh trên mạng thử nghiệm Sepolia.

---

## Yêu cầu ban đầu

- **Google Account**: Cần đăng nhập sẵn vào tài khoản Google.
- **ETH Mainnet Balance**: Ví phải có tối thiểu **0.001 ETH** trên mạng chính để thực hiện faucet.
- **Haha Wallet**:
  - Đăng nhập sẵn vào **Haha Wallet**.
  - Chuyển sang mạng **Sepolia** trước khi chạy chương trình.

---

## File bao gồm:

- `extensions/HaHa-Wallet-Chrome-Web-Store.crx` - Tiện ích mở rộng Haha Wallet.
- `browser_automation.py` - Code tự động hóa trình duyệt.
- `utils.py` - Các hàm hỗ trợ chung.
- `hahawallet.py` - Code điều khiển Haha Wallet.
- `requirements.txt` - Các thư viện yêu cầu

---

## Hướng dẫn cài đặt

### 1 Tạo file `data.txt`

Mỗi dòng trong file **data.txt** chứa thông tin một profile, có cấu trúc:

```plaintext
[profile_tên]|[địa_chỉ_ví_tesnet]|[mã_code_đã_tạo]
```

#### Ví dụ:

```plaintext
profile1|0x23fb68d805ebb9d18e8d2e3a07f85ba5416eb2ed|12345678
profile2|0x23fb68d805ebb9d18e8d2e3a07f85ba5416eb2ed|12345678
```

### 2️ (Tùy chọn) Tạo file `token_tele.txt`

- Chứa **Telegram Bot Token** để chương trình gửi hình ảnh lỗi lên Telegram khi gặp sự cố.
- Nếu không có file này, ảnh lỗi sẽ lưu vào thư mục **snapshot**.

### 3 Cài đặt Python
Trước tiên, cần cài đặt Python (phiên bản 3.8 trở lên). Nếu chưa có, hãy tải và cài đặt từ [Python Official Site](https://www.python.org/downloads/).

Sau khi cài đặt, kiểm tra phiên bản Python bằng lệnh:

```sh
python --version
```
hoặc
```sh
python3 --version
```

### 4 Cài đặt thư viện yêu cầu

Chạy lệnh sau để cài đặt các thư viện cần thiết:

```sh
pip install -r requirements.txt
```

---

## Hướng dẫn sử dụng

### Chạy chương trình

```sh
python hahawallet.py
```
hoặc
```sh
python3 hahawallet.py
```

### Các lựa chọn trong chương trình

- 1> Chạy chế độ set up ban đầu và chọn profile (thực hiện các yêu cầu bên trên trước. ví dụ: Đăng nhập google và ví HahaWallet)
- 2> Chạy chế độ auto và chọn profile (thực hiện các tác vụ được thiết lập sẵn)
- 3> Thoát

## Tùy chỉnh cấu hình

Nếu muốn chương trình **tự động chạy tác vụ mà không cần chọn chế độ mỗi lần**, hãy chỉnh sửa file như sau:

1. Tìm dòng sau trong hahawallet.py:

   ```python
   manager.run_terminal(
       profiles=PROFILES,
       auto=False,
       max_concurrent_profiles=4
   )
   ```

2. Thay đổi `auto=False` thành `auto=True`:

   ```python
   manager.run_terminal(
       profiles=PROFILES,
       auto=True,
       max_concurrent_profiles=4
   )
   ```

Sau khi chỉnh sửa, chương trình sẽ **tự động chạy** mà không cần chọn menu mỗi lần khởi động.

---

## Thông tin khác

- **Chrome Version**: 131.0.6778.264

Telegram Channel: [Airdrop Automation](https://t.me/+8o9ebAT9ZSFlZGNl)