import sys
import io
import base64
import socket
import json
from http.server import HTTPServer
from RequestHandler import HTTPRequestHandler, request, route
import logging
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from DataFramesStorage import DataFrames
import numpy as np

LOG_FILE_NAME = 'server_logs.txt'
data_frames=DataFrames()

@request
class RequestHandler(HTTPRequestHandler):
    @route("get", path="/")
    def get_empty_proc(self):
        self._set_response()
        self.wfile.write(
            f"<html>\n<center><h1><a href='http://10.13.1.4:9999/logs'>Logs</a>   <a href='http://10.13.1.4:9999/graph'>Graph</a></h1></center></html>".encode(
                "ascii"))

    @route("get", path="/logs")
    def get_logs_proc(self):
        print(f"GET request logs from {self.client_address}")
        self._set_response()
        with open(LOG_FILE_NAME, 'r') as log_file:
            output = io.BytesIO()
            for line in log_file.readlines():
                output.write(bytes(line + "<br>", 'utf-8'))
            output.seek(0)
            self.wfile.write(output.read())

    @route("get", path="/graph")
    def get_graph_proc(self):
        print(f"GET request graph from {self.client_address}")

        fig = Figure(figsize=(16, 8), dpi=80, facecolor='w', edgecolor='k')
        dummy = plt.figure()
        new_manager = dummy.canvas.manager
        new_manager.canvas.figure = fig
        fig.set_canvas(new_manager.canvas)

        # subplots = fig.subplots(1, len(self.data_frames))
        # fig, axs = fig.subplots(len(self.data_frames.keys()))
        #result = f"<html>\n"
        devices = data_frames.get
        for device_name in devices:
            #result += f"<center>{device_name}</center><br>"
            graphs = devices[device_name]
            dfl = len(graphs.keys())
            if dfl == 0:
                ax = fig.subplots()
                ax.plot([0], [0])
            elif dfl == 1:
                dfk = list(graphs.keys())[0]
                axs = fig.subplots()
                axs.plot(graphs[dfk]['times'], graphs[dfk]['values'])
                axs.set_title(dfk)
            else:
                f, axs = fig.subplots(dfl)
                for i, df in enumerate(graphs.keys()):
                    axs[i].plot(graphs[df]['times'], graphs[df]['values'])
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
        try:
            self.wfile.write(f"<html>\n<img src='data:image/png;base64,{data}'/>\n</html>".encode("ascii"))
        except Exception as e:
            print(e)
        # return f"<img src='data:image/png;base64,{data}'/>"

    @route("get", path="/test")
    def get_test_proc(self):
        print(f"GET request test from {self.client_address}")
        self._set_response()
        with open(".\\www\\sample-chartist-js.html", 'rb') as html_file:
            self.wfile.write(html_file.read())

    @route("get", path="/dataframes")
    def get_dataframes_proc(self):
        #print(f"GET request test from {self.client_address}")
        self._set_json_response()
        self.wfile.write(json.dumps(data_frames.get_json).encode("utf-8"))

    @route("post", path="/dataframe")
    def post_dataframe(self):
        if self.process_post_dataframe():
            self._set_response()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        else:
            self._set_400_response()

    @route("post", path="/logs")
    def post_logs(self):
        if self.process_post_logs():
            self._set_response()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        else:
            self._set_400_response()

    def process_post_log(self):
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length).decode('utf-8')

        try:
            obj = json.loads(data, encoding='utf8')
        except json.decoder.JSONDecodeError:
            logging.info(f"{self.client_address} {data}")
            return False

        if obj['MsgType'] == 'log':
            device = obj['DeviceName']
            log_msg = obj['data']
            logging.info(f"{self.client_address} {device} {log_msg}")
            return True

        return False

    def process_post_dataframe(self):
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length).decode('utf-8')

        try:
            obj = json.loads(data, encoding='utf8')
        except json.decoder.JSONDecodeError:
            logging.info(f"Data error {self.client_address} {data}")
            return False

        try:
            if obj['MsgType'] == 'dataframe':
                devicename = obj['DeviceName']
                dataname = obj['DataName']
                ftime = obj['Time']
                fvalue = obj['Value']
                data_frames.append(devicename, dataname, ftime, fvalue)
                return True
        except:
            logging.info(f"Data error {self.client_address} {data}")
            return False

        return False

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