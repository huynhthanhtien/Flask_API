# Sử dụng hình ảnh chính thức của Python
FROM python:3.9-slim

# Cài đặt các thư viện cần thiết
RUN pip install --upgrade pip
RUN pip install flask python-dotenv google-auth google-auth-oauthlib google-auth-httplib2

# Sao chép mã nguồn vào container
WORKDIR /app
COPY . /app

# Thiết lập biến môi trường cho Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Chạy Flask app
CMD ["flask", "run"]
