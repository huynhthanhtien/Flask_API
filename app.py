import os
import json
from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv  # Sử dụng python-dotenv
from google_auth_oauthlib.flow import Flow

# Nạp các biến môi trường từ .env
load_dotenv()

app = Flask(__name__)

# Lấy chuỗi JSON từ biến môi trường và giải mã nó thành dictionary
client_secret_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
client_secret = json.loads(client_secret_json)

# Trích xuất thông tin cần thiết từ client_secret
GOOGLE_CLIENT_ID = client_secret["web"]["client_id"]
GOOGLE_CLIENT_SECRET = client_secret["web"]["client_secret"]
GOOGLE_REDIRECT_URI = client_secret["web"]["redirect_uris"][0]  # Lấy URI chuyển hướng đầu tiên

# Initialize OAuth flow
flow = Flow.from_client_config(
    client_secret,  # Sử dụng thông tin client secret từ chuỗi JSON
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
    redirect_uri=GOOGLE_REDIRECT_URI
)

@app.route('/')
def index():
    # Redirect user to Google login
    authorization_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    # Lấy mã xác thực từ Google và lấy token
    flow.fetch_token(authorization_response=request.url)

    if not flow.credentials:
        return jsonify({"error": "Authentication failed"}), 400

    # Lưu trữ credentials và trả về token
    credentials = flow.credentials
    token = credentials.token

    # Tùy chọn: Lấy thông tin người dùng
    user_info = get_user_info(credentials)

    return jsonify({
        'access_token': token,
        'user_info': user_info
    })

def get_user_info(credentials):
    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    return user_info

if __name__ == '__main__':
    app.run(ssl_context=('server.crt', 'server.key'), host='0.0.0.0', port=5000)