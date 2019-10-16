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

    def get_empty_proc(self):
        self._set_response()
        self.wfile.write(
            f"<html>\n<center><h1><a href='http://10.13.1.4:9999/logs'>Logs</a>   <a href='http://10.13.1.4:9999/graph'>Graph</a></h1></center></html>".encode(
                "ascii"))

    def get_logs_proc(self):
        print(f"GET request logs from {self.client_address}")
        self._set_response()
        with open(LOG_FILE_NAME, 'r') as log_file:
            output = io.BytesIO()
            for line in log_file.readlines():
                output.write(bytes(line + "<br>", 'utf-8'))
            output.seek(0)
            self.wfile.write(output.read())

    def get_graph_proc(self):
        print(f"GET request graph from {self.client_address}")

        fig = Figure(figsize=(16, 8), dpi=80, facecolor='w', edgecolor='k')
        dummy = plt.figure()
        new_manager = dummy.canvas.manager
        new_manager.canvas.figure = fig
        fig.set_canvas(new_manager.canvas)

        # subplots = fig.subplots(1, len(self.data_frames))
        # fig, axs = fig.subplots(len(self.data_frames.keys()))
        dfl = len(self.data_frames.keys())
        if dfl == 0:
            ax = fig.subplots()
            ax.plot([0], [0])
        elif dfl == 1:
            dfk = list(self.data_frames.keys())[0]
            axs = fig.subplots()
            axs.plot(self.data_frames[dfk]['x'], self.data_frames[dfk]['y'])
            axs.set_title(dfk)
        else:
            f, axs = fig.subplots(dfl)
            for i, df in enumerate(self.data_frames.keys()):
                axs[i].plot(self.data_frames[df]['x'], self.data_frames[df]['y'])
                axs[i].set_title(df)
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
        # return f"<img src='data:image/png;base64,{data}'/>"

    def get_test_proc(self):
        print(f"GET request test from {self.client_address}")
        self._set_response()
        with open(".\\www\\sample-chartist-js.html", 'rb') as html_file:
            self.wfile.write(html_file.read())

    get_workers = {"/": get_empty_proc, "/logs": get_logs_proc, "/graph": get_graph_proc, "/test": get_test_proc}

    def log_message(self, format, *args):
        return

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        process_func = self.get_workers.get(self.path, None)
        if process_func is not None:
            process_func(self)

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
                x1 = self.data_frames[dataname]['x'][-1]
                x2 = ftime[0]
                if x1 < x2:
                    self.data_frames[dataname]['x'].extend(ftime)
                    self.data_frames[dataname]['y'].extend(fvalue)
                else:
                    self.data_frames[dataname]['x'] = ftime
                    self.data_frames[dataname]['y'] = fvalue
            else:
                self.data_frames[dataname] = {'x': ftime, 'y': fvalue}


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