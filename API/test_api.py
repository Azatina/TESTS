from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from itertools import cycle
from multiprocessing.dummy import Pool as ThreadPool
from os import listdir
from os.path import isfile, join, abspath, getsize
from os.path import split as split_path
from threading import current_thread
from urllib.parse import quote

import base64
import configparser
import json
import smtplib
import ssl
import socket
import time


config = configparser.ConfigParser()
config.read('test_api.cfg', encoding='utf-8')
SERVER = config.get('DEFAULT', 'host')
PORT = int(config.get('DEFAULT', 'port'))
TEST_PATH = config.get('DEFAULT', 'send_files_from_dir')
USER = base64.b64encode(config.get('DEFAULT', 'user').encode()).decode()
USERSFILE = config.get('DEFAULT', 'usersfile')
THREADS = int(config.get('THREADS', 'threads'))
ITERATIONS = int(config.get('THREADS', 'iterations'))
CHUNK_SIZE = eval(config.get('DEFAULT', 'chunks'))
GUID_LIST = []

# GET /api/policies
# POST /api/check
# POST /api/upload?id={request-guid}
# GET /api/status?id={request-guid}

Additional_Headers = (f"Connection: keep-alive\r\n"
                      # f"Host: {SERVER}:{PORT}\r\n"
                      # f"Transfer-Encoding: chunked\r\n"
                      # f"Content-Type: application/octet-stream\r\n"
                      f""
                      )


def policies_api():
    request = (f"GET /api/policies HTTP/1.1\r\n"
               f"{Additional_Headers}"
               f"\r\n").encode()
    return request, None


def check_api(method='file',
              policies=None,
              content64=None,
              username=None,
              computer=None,
              filename=None,
              direction=None,
              channel=None):
    payload_base = {'method': method,
                    'policies': policies,
                    'content': content64,
                    'user': username,
                    'computer': computer,
                    'filename': filename,
                    'direction': direction,
                    'channel': channel
                    }
    for arg in [policies, content64, username, computer, filename, direction, channel]:
        payload = json.dumps({k: arg for k, arg in payload_base.items() if arg})
    request = (f"POST /api/check HTTP/1.1\r\n"
               f"Content-Length: {len(payload)}\r\n"
               f"{Additional_Headers}"
               f"\r\n"
               f"{payload}").encode()
    return request, None


def upload(guid, filename):
    request = (f"POST /api/upload?id={guid} HTTP/1.1\r\n"
               f"Content-Length: {getsize(filename)}\r\n"
               f"{Additional_Headers}"
               f"\r\n").encode()
    return request, filename


'''-----------------------------------TO DO-----------------------------------'''


def upload_MIME(guid, filename):
    msg = MIMEMultipart()
    msg['From'] = 'atereg@tst.local'
    msg['To'] = 'azat_test@tst.local'
    msg['Subject'] = 'simple email in python'
    message = 'here is the email12312312312356785678567'
    msg.attach(MIMEText(message))

    with open(filename, 'rb') as f:
        attached_file = MIMEApplication(f.read())
        attached_file.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(attached_file)

    # msg.attach(filename)

    Additional_Headers = f"Content-Length: {len(msg.as_string())}\r\n"
    request = (f"POST /api/upload?id={guid} HTTP/1.1\r\n"
               f"{Additional_Headers}\r\n").encode() + msg.as_string().encode()
    return request, None


'''-----------------------------------TO DO------------------------------------'''


def status(guid):
    request = (f"GET /api/status?id={guid} HTTP/1.1\r\n"
               f"{Additional_Headers}\r\n").encode()
    return request, None


def file_list(path):
    if isfile(path):
        files = [path]
    else:
        files = [abspath(join(path, f)) for f in listdir(path) if isfile(join(path, f))]
    return files


def user_list(path):
    with open(path, 'r') as f:
        users = f.read().split()
    return users


def connector():
    conn = socket.socket()
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 1)
    # conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    try:
        conn.connect((SERVER, PORT))
    except socket.error as msg:
        print(f"Error: {msg}")
    # conn = ssl.wrap_socket(socket.socket())
    # conn.connect((SERVER, PORT))
    return conn


def send_request(conn, request):
    # print(f"Thread ID {current_thread().ident}")
    # st = time.time()
    req_hdr, req_body = request
    conn = check_sockets(conn)
    if req_body is not None:
        if CHUNK_SIZE > 0:
            req_hdr = req_hdr.rstrip(b'\r\n')
            req_hdr += (b'Transfer-Encoding: chunked\r\n'
                        # b'Expect: 100-continue\r\n'
                        b'\r\n')
            conn.send(req_hdr)
            with open(req_body, 'rb') as f:
                conn.send(hdr)
                data = f.read(CHUNK_SIZE)
                while data:
                    data_len = hex(len(data)).split('x')[-1]
                    conn.send(f"{data_len}\r\n".encode())
                    conn.send(data)
                    conn.send(f"\r\n".encode())
                    data = f.read(CHUNK_SIZE)
                conn.send(b'0\r\n')
        else:
            conn.send(req_hdr)
            with open(req_body, 'rb') as f:
                file = f.read()
            conn.send(file)
    else:
        conn.send(req_hdr)
    # print(f"Request send time: {time.time() - st}")
    return get_response(conn)


def find_length(resp_data):
    cnt_len = b'Content-Length:'
    content_length = -1
    header_delimiter = b'\r\n\r\n'
    headers = resp_data.split(header_delimiter)[0]
    for line in headers.split(b'\r\n'):
        if cnt_len in line:
            content_length = (int(line[len(cnt_len):]))
    return content_length


def find_index_body(resp_data):
    header_delimiter = b'\r\n\r\n'
    idx = -1
    if header_delimiter in resp_data:
        idx = resp_data.index(header_delimiter) + len(header_delimiter)
    return idx


def get_response(conn):
    content_length = -1
    idx = -1
    len_body = -2
    header_delimiter = b'\r\n\r\n'
    index_delimiter = len(header_delimiter)
    response_data = b''
    # st = time.time()
    while len_body < content_length:
        response_chunk = conn.recv(1024)
        response_data += response_chunk
        if content_length < 0:
            content_length = find_length(response_data)
        if idx < 0:
            idx = find_index_body(response_data)
        len_body = len(response_data[idx:])
        if len_body == content_length:
            break
    if b'Connection: keep-alive' not in response_data:
        conn.close()
    # print(f"Answer received after: {time.time() - st}")
    return response_data.decode()


def check_sockets(socket_list):
    if isinstance(socket_list, socket.socket):
        if socket_list.fileno() == -1:
            return connector()
        return socket_list
    else:
        for socket_item in socket_list:
            if socket_item.fileno() == -1:
                socket_item = connector()


if __name__ in "__main__":

    file_test = file_list(TEST_PATH)
    user_test = user_list(USERSFILE)
    conn_keep_alive = connector()

    data = send_request(conn_keep_alive, policies_api())
    parsed_data = json.loads(data.split("\r\n")[-1])
    print('\r\nПолитики')
    for element in parsed_data:
        print('\t'.join(f"{item}" for item in element.values()))

    time.sleep(0.5)

    data = send_request(conn_keep_alive, check_api(f"MIME",
                                                   None,
                                                   None,
                                                   f"{user_test[0]}",
                                                   f"azat.zecurion.local",
                                                   f"{split_path(file_test[0])[-1]}",
                                                   'internal',
                                                   'mail'
                                                   ))
    parsed_data = json.loads(data.split('\r\n')[-1])
    print('\r\n', '\t'.join(f"{item}" for item in parsed_data.values()))

    time.sleep(0.5)

    data = send_request(conn_keep_alive, upload_MIME(quote(parsed_data['id']), file_test[0]))
    parsed_data = json.loads(data.split('\r\n')[-1])
    print('\r\n', '\t'.join(f"{item}" for item in parsed_data.values()))

    time.sleep(0.5)

    status_api = 'status'
    while status_api != 'processed':  # 'failed':
        data = send_request(conn_keep_alive, status(quote(parsed_data['id'])))
        parsed_data = json.loads(data.split("\r\n")[-1])
        print('\r\n', ''.join(f"{parsed_data['id']}\t{parsed_data['status']}"))
        status_api = parsed_data.get('status', None)
        time.sleep(0.5)

    conn_keep_alive.close()

    '''
    Parse JSON response from API server
    '''

    print('\r\nЖурнал анализа с условиями\r\n')

    for element in parsed_data['log']:
        if element.get('applied', False):
            print(f"{element['applied']}\t{element['name']}")
            print('\r\n'.join(f"\t\t{events['ext_info']['condition']['description']}"
                              for events in element['events']
                              if events.get('ext_info', False)))

    print('\r\nСработавшие политики\r\n')

    print(''.join(f"{element['applied']}\t{element['name']}\r\n"
                  for element in parsed_data['log']
                  if element.get('applied', False)))

    print(f"\r\n{parsed_data['start']}\r\n{parsed_data['finish']}")
else:
    print(f"Imported {__name__}")
