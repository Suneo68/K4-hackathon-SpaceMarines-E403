# Sử dụng image Python chuẩn và siêu nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt một số thư viện hệ thống cần thiết (nếu có để build packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file thư viện vào và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào
COPY . .

# Lệnh chạy Bot
CMD ["python", "main.py"]
