import os
import json
from flask import Flask, redirect, request, jsonify, Response
from dotenv import load_dotenv  # Sử dụng python-dotenv
from google_auth_oauthlib.flow import Flow
from flask_cors import CORS

# Nạp các biến môi trường từ .env
load_dotenv()

app = Flask(__name__)

CORS(app, origins=["chrome-extension://*"])
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
    # scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/calendar"],
     scopes=[
        "openid",  # Thêm OpenID
        "https://www.googleapis.com/auth/userinfo.profile", 
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/calendar"
    ],
    redirect_uri=GOOGLE_REDIRECT_URI
)

@app.route('/login')
def login():
    # Redirect user to Google login
    authorization_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    return Response(
        json.dumps({"url": authorization_url}), 
        status=200, 
        mimetype='application/json'
    )

@app.route('/')
def index():
    # Redirect user to Google login
    authorization_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    return redirect(authorization_url)

# @app.route('/callback')
# def callback():
#     # Lấy mã xác thực từ Google và lấy token
#     flow.fetch_token(authorization_response=request.url)

#     if not flow.credentials:
#         return jsonify({"error": "Authentication failed"}), 400

#     # Lưu trữ credentials và trả về token
#     credentials = flow.credentials
#     token = credentials.token
#     print(token)
#     # Tùy chọn: Lấy thông tin người dùng
#     user_info = get_user_info(credentials)
#     print(user_info)
    
#     response_data = {
#         'access_token': token,
#         'user_info': user_info
#     }

#     return Response(
#         json.dumps(response_data), 
#         status=200, 
#         mimetype='application/json'
#     )
from flask import render_template_string

@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Code not found"}), 400

    flow.redirect_uri = GOOGLE_REDIRECT_URI
    authorization_response = request.url

    try:
        flow.fetch_token(authorization_response=authorization_response)

        if not flow.credentials:
            return jsonify({"error": "Authentication failed"}), 400

        credentials = flow.credentials
        token = credentials.token
        user_info = get_user_info(credentials)

        # Render một HTML page trả về kết quả cho frontend (qua postMessage)
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Auth Success</title></head>
        <body>
            <script>
                window.opener.postMessage({
                    access_token: "%s",
                    user_info: %s
                }, "*");
                window.close();
            </script>
        </body>
        </html>
        """ % (token, json.dumps(user_info))

        return render_template_string(html_content)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/get_token", methods=["POST"])
def get_token():
    # Lấy mã code từ yêu cầu POST
    url = request.json.get("url")
    # state = request.json.get("state")
    if not url:
        return jsonify({"error": "Code is required"}), 400

    # Thiết lập URL callback và mã code
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    authorization_response = url
    try:
        # Lấy token từ mã code
        flow.fetch_token(authorization_response=authorization_response)

        if not flow.credentials:
            return jsonify({"error": "Authentication failed"}), 400

        # Lưu trữ credentials và trả về token
        credentials = flow.credentials
        token = credentials.token
        print(token)

        # Tùy chọn: Lấy thông tin người dùng
        user_info = get_user_info(credentials)
        print(user_info)

        response_data = {
            'access_token': token,
            'user_info': user_info
        }

        return Response(
            json.dumps(response_data),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def get_user_info(credentials):
    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    return user_info

if __name__ == '__main__':
    app.run(ssl_context=('server.crt', 'server.key'), host='0.0.0.0', port=5000, debug=True)
