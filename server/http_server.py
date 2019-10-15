import sys
import io
import base64
import socket
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

LOG_FILE_NAME = 'server_logs.txt'


class RequestHandler(BaseHTTPRequestHandler):
    data_frames = {}

    def log_message(self, format, *args):
        return

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if self.path == "/logs":
            print(f"GET request logs from {self.client_address}")
            self._set_response()
            with open(LOG_FILE_NAME, 'r') as log_file:
                output = io.BytesIO()
                for line in log_file.readlines():
                    output.write(bytes(line+"<br>", 'utf-8'))
                output.seek(0)
                self.wfile.write(output.read())
        elif self.path == "/graph":
            print(f"GET request graph from {self.client_address}")

            fig = Figure(figsize=(16, 8), dpi=80, facecolor='w', edgecolor='k')
            dummy = plt.figure()
            new_manager = dummy.canvas.manager
            new_manager.canvas.figure = fig
            fig.set_canvas(new_manager.canvas)

            #subplots = fig.subplots(1, len(self.data_frames))
            ax = fig.subplots()
            ax.plot(self.data_frames['fps']['x'], self.data_frames['fps']['y'])
            ax.set_title('fps')
            # for i, df in enumerate(self.data_frames):
            #     #ax = fig.add_subplot(len(self.data_frames), 1, i)
            #     ax = fig.add_subplot()
            #     ax.plot(self.data_frames[df]['x'], self.data_frames[df]['y'])
            #     ax.set_title(df)

            plt.close(fig)

            # Save it to a temporary buffer.
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            # with open("result.png", 'wb') as output:
            #     fig.savefig(output, format="png")
            # Embed the result in the html output.
            data = base64.b64encode(buf.getbuffer()).decode("ascii")

            self._set_response()
            self.wfile.write(f"<html>\n<img src='data:image/png;base64,{data}'/>\n</html>".encode("ascii"))
            #return f"<img src='data:image/png;base64,{data}'/>"
        else:
            self._set_response()
            self.wfile.write(f"<html>\n<center><h1><a href='http://10.13.1.4:9999/logs'>Logs</a>   <a href='http://10.13.1.4:9999/graph'>Graph</a></h1></center></html>".encode("ascii"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self.process_post_data(self.client_address, post_data.decode('utf-8'))
        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

    def process_post_data(self, address, data):
        # logging.info(f"{address} {data}")
        try:
            obj = json.loads(data, encoding='utf8')
        except json.decoder.JSONDecodeError:
            logging.info(f"{address} {data}")
            return

        if obj['MsgType'] == 'log':
            device = obj['DeviceName']
            log_msg = obj['data']
            logging.info(f"{address} {device} {log_msg}")
        elif obj['MsgType'] == 'dataframe':
            dataname = obj['dataname']
            ftime = obj['time']
            fvalue = obj['value']
            if dataname in self.data_frames:
                self.data_frames[dataname]['x'].append(ftime)
                self.data_frames[dataname]['y'].append(fvalue)
            else:
                self.data_frames[dataname] = {'x': [ftime], 'y': [fvalue]}


def setup_logging():
    logging.basicConfig(filename=LOG_FILE_NAME, level=logging.INFO, format="[%(asctime)s] %(message)s")
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
    handler.setLevel(logging.INFO)
    root.addHandler(handler)


def run(server_class=HTTPServer, handler_class=RequestHandler, port=9999):
    host = socket.gethostname()
    server_address = ("10.13.1.4", port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting http server under: {server_address}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('Stopping httpd...')


if __name__ == '__main__':
    setup_logging()
    run()