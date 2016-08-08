import httplib2
import asyncio
import webbrowser
import http.server
import urllib.parse

from oauth2client.client import OAuth2WebServerFlow
import os


class myHandler(http.server.BaseHTTPRequestHandler):
    # Handler for the GET requests
    taskCompletion = asyncio.Future()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.finish()
        self.taskCompletion.set_result(self.path)
        return


def wait_for_request(server_class=http.server.HTTPServer,
                     handler_class=myHandler):
    server_address = (
        '', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.handle_request()
    return handler_class.taskCompletion


os.environ['http_proxy'] = '127.0.0.1'
os.environ['https_proxy'] = '127.0.0.1'
CLIENT_ID = "6weYFmrx2x"
CLIENT_SECRET = "edTAkTDeKehKvykzmq7yQr "
SCOPES = ("read",)
AUTH_URL = "https://quizlet.com/authorize"
TOKEN_URL = "https://api.quizlet.com/oauth/token"
DEVICE_URL = "https://quizlet.com/authorize"
REDIRECT_URL = "http://localhost:8000/red"

flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, " ".join(SCOPES), auth_uri=AUTH_URL, token_uri=TOKEN_URL,
                           device_uri=DEVICE_URL, redirect_uri=REDIRECT_URL,
                           authorization_header="Basic NndlWUZtcngyeDplZFRBa1REZUtlaEt2eWt6bXE3eVFy",
                           kwargs={"response_type": "code", "state": "telrkjdsf"})

# Step 1: get user code and verification URL
# https://developers.google.com/accounts/docs/OAuth2ForDevices#obtainingacode
flow_info = flow.step1_get_authorize_url(state="asdlfkjew")
webbrowser.open(flow_info)
result = asyncio.get_event_loop().run_until_complete(wait_for_request())
url = urllib.parse.parse_qs(urllib.parse.urlparse(result).query)
# Step 2: get credentials
# https://developers.google.com/accounts/docs/OAuth2ForDevices#obtainingatoken
credentials = flow.step2_exchange(code="".join(url["code"]))
print("Access token:  {0}".format(credentials.access_token))
print("Refresh token: {0}".format(credentials.refresh_token))
http = httplib2.Http()
credentials.authorize(http)
http.

# Get YouTube service
# https://developers.google.com/accounts/docs/OAuth2ForDevices#callinganapi
youtube = build("youtube", "v3", http=credentials.authorize(httplib2.Http()))
