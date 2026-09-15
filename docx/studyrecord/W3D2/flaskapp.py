import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route('/alarm/do', methods=['POST'])
    def receive_alarm():
        data = request.json or {}
        print(f'[Flask] Received Alarm: beltID={data.get("beltID")} dist={data.get("distance")} angle={data.get("angle")}')
        return jsonify({'status': 'success', 'msg': 'alarm received'}), 200

    def run_server(host='0.0.0.0', port=5000):
        app.run(host=host, port=port)

except ImportError:
    class AlarmHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/alarm/do':
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                try:
                    data = json.loads(body.decode('utf-8'))
                    print(f'[MockServer] Received Alarm: beltID={data.get("beltID")} dist={data.get("distance")} angle={data.get("angle")}')
                except Exception as e:
                    print(f'[MockServer] JSON parse error: {e}')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success", "msg": "alarm received"}')
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass

    def run_server(host='0.0.0.0', port=5000):
        server = HTTPServer((host, port), AlarmHandler)
        print(f'Starting alarm server on {host}:{port}...')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_server('0.0.0.0', port)
