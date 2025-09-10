import os.path
from itertools import cycle
from multiprocessing.dummy import Pool as ThreadPool
from os import listdir
from os.path import isfile, getsize, join, abspath
from os.path import split as split_path
from threading import current_thread
from urllib.parse import quote

import base64
import configparser
import random
import socket
import string

import threading  # ????

import time

config = configparser.ConfigParser()
config.read('icap_client.cfg', encoding='utf-8')
SERVER = config.get('DEFAULT', 'host')
PORT = int(config.get('DEFAULT', 'port'))
CLIENT_IP = config.get('DEFAULT', 'clientip')
TEST_PATH = config.get('DEFAULT', 'send_files_from_dir')
THREADS = int(config.get('THREADS', 'threads'))
ITERATIONS = int(config.get('THREADS', 'iterations'))
CHUNK_SIZE = eval(config.get('DEFAULT', 'chunks'))
USER = base64.b64encode(config.get('DEFAULT', 'user').encode()).decode()
USERSFILE = config.get('DEFAULT', 'usersfile')

if CHUNK_SIZE == 0:
    CHUNK_SIZE = 1*1024*1024*1024

if isfile(TEST_PATH):
    files = [TEST_PATH]
else:
    files = [abspath(join(TEST_PATH, f)) for f in listdir(TEST_PATH) if isfile(join(TEST_PATH, f))]

with open(USERSFILE, 'rb') as f:
    users_plain = f.read().split(b'\r\n')
    users = [base64.b64encode(u).decode() for u in users_plain]


def add_hdr_http():
    add_http_hdr = (f"Connection: keep-alive\r\n"
                    # f"X-Authenticated-Groups: \r\n"
                    # f"X-Authenticated-User: {USER}\r\n"
                    # f"X-Client-IP: 192.168.0.121\r\n"
                    # f"X-Client-Username: {USER_PLAIN}\r\n"
                    # f"X-Filename: asdadsasdasd\r\n"
                    # f"X-Forwarded-For: 192.168.0.121\r\n"
                    # f"X-Server: 1.1.1.2\r\n"
                    )
    return add_http_hdr


def add_hdr_icap(username):
    add_icap_hdr = (f"Host: {SERVER}:{PORT}\r\n"
                    f"Allow: 204\r\n"
                    # f"Preview: 1024\r\n"
                    # f"Connection: keep-alive\r\n"
                    # f"X-Authenticated-Groups: \r\n"
                    # f"X-Authenticated-User: {username}\r\n"
                    f"X-Client-IP: {CLIENT_IP}\r\n"
                    # f"X-Client-Username: {USER_PLAIN}\r\n"
                    # f"X-Filename: {quote('zxc   zxc')}\r\n"
                    # f"X-Filename: zxc%20%20%20zxc\r\n"
                    # f"X-Forwarded-For: 192.168.0.121\r\n"
                    # f"X-Server: 1.1.1.1\r\n"
                    )
    return add_icap_hdr


def search_request(filename, username):
    http_hdr = (f"GET /search/?text=123qweee{quote(split_path(filename)[-1])}-{i} HTTP/1.1\r\n"
                f"Host: ya.ru\r\n"
                f"Referer: https://ya.ru/\r\n"
                f"{add_hdr_http()}"
                f"\r\n").encode()
    icp_hdr = (f"REQMOD icap://{SERVER}:{PORT}/reqmod ICAP/1.0\r\n"
               f"{add_hdr_icap(username)}"
               f"Encapsulated: req-hdr=0, null-body={len(http_hdr)}\r\n"
               f"\r\n").encode()
    return icp_hdr + http_hdr


def download_request(filename, username):
    http_head_req = (f"GET /message_part_real/{quote(split_path(filename)[-1])}"
                     f"?name={quote(split_path(filename)[-1])}"
                     f" HTTP/1.1\r\n"
                     f"Host: webattach.mail.yandex.net\r\n"
                     f"Connection: keep-alive\r\n"
                     f"Referer: https://mail.yandex.ru/\r\n"
                     f"\r\n").encode()
    http_head_resp = (f"HTTP/1.1 200 OK\r\n"
                      f"Connection: keep-alive\r\n"
                      f"Content-Type: application/octet-stream;"
                      f"filename=\"{split_path(filename)[-1]}\";charset=\"US-ASCII\"\r\n"
                      f"Content-Length: {getsize(filename)}\r\n"
                      f"Content-Disposition: attachment;"
                      f"filename=\"{split_path(filename)[-1]}\"\r\n"
                      f"\r\n").encode()
    icap_head_req = (f"RESPMOD icap://{SERVER}:{PORT}/icap/respmod ICAP/1.0\r\n"
                     f"{add_hdr_icap(username)}"
                     f"Encapsulated: "
                     f"req-hdr=0, "
                     f"res-hdr={len(http_head_req)}, "
                     f"res-body={len(http_head_req + http_head_resp)}\r\n"
                     f"\r\n").encode()
    return icap_head_req + http_head_req + http_head_resp


def upload_request(filename, username):
    WebKitBoundary = "".join(random.SystemRandom().choice(string.ascii_letters + string.digits)
                             for _ in range(16))
    multi_head = (f"------WebKitFormBoundary{WebKitBoundary}\r\n"
                  f"Content-Disposition: form-data; name=\"Filename\"\r\n"
                  f"\r\n"
                  f"{split_path(filename)[-1]}\r\n"
                  f"------WebKitFormBoundary{WebKitBoundary}\r\n"
                  f"Content-Disposition: form-data; name=\"file\";"
                  f" filename=\"{split_path(filename)[-1]}\"\r\n"
                  f"Content-Type: application/octet-stream\r\n"
                  # f"Transfer-Encoding: chunked\r\n"
                  f"\r\n").encode()
    multi_tail = (f"\r\n------WebKitFormBoundary{WebKitBoundary}--\r\n"
                  f"").encode()
    contlen_req = len(multi_head + multi_tail) + getsize(filename)
    http_head_req = (f"POST /web-api/upload-attachment/liza1 HTTP/1.1\r\n"
                     f"Host: mail.yandex.ru\r\n"
                     f"{add_hdr_http()}"
                     # f"Transfer-Encoding: chunked\r\n"
                     f"Content-Length: {contlen_req}\r\n"
                     f"Content-Type: multipart/form-data;"
                     f" boundary=----WebKitFormBoundary{WebKitBoundary}\r\n"
                     f"\r\n").encode()
    icap_head_req = (f"REQMOD icap://{SERVER}:{PORT}/icap/reqmod ICAP/1.0\r\n"
                     f"{add_hdr_icap(username)}"
                     f"Encapsulated: req-hdr=0, req-body={len(http_head_req)}\r\n"
                     f"\r\n").encode()
    hdr = icap_head_req + http_head_req
    return hdr, multi_head, multi_tail


def upload_request_stream(filename, username):
    contlen_req = getsize(filename)
    http_head_req = (f"POST /web-api/upload-attachment/liza1 HTTP/1.1\r\n"
                     f"Host: mail.yandex.ru\r\n"
                     f"{add_hdr_http()}"
                     # f"Transfer-Encoding: chunked\r\n"
                     f"Content-Length: {contlen_req}\r\n"
                     f"Content-Type: application/octet-stream\r\n"
                     f"\r\n").encode()
    icap_head_req = (f"REQMOD icap://{SERVER}:{PORT}/icap/reqmod ICAP/1.0\r\n"
                     f"{add_hdr_icap(username)}"
                     f"Encapsulated: req-hdr=0, req-body={len(http_head_req)}\r\n"
                     f"\r\n").encode()
    hdr = icap_head_req + http_head_req
    return hdr


def upload_request_nextcloud(filename, username):
    contlen_req = getsize(filename)
    http_head_req = (f"PUT http://dev.nextcloud.mts.ru/remote.php/dav/files"
                     f"/{quote('az az t@zecurion999')}/{quote(split_path(filename)[-1])} HTTP/1.1\r\n"
                     f"Host: dev.nextcloud.mts.ru\r\n"
                     f"X-Request-ID: ba39b3d1-0a8d-4d1b-9c73-175b3b528996\r\n"
                     f"X-Real-IP: {CLIENT_IP}\r\n"
                     f"X-Forwarded-For: {CLIENT_IP}\r\n"
                     f"X-Forwarded-Host: nextcloud.mts.ru\r\n"
                     f"X-Forwarded-Port: 443\r\n"
                     f"X-Forwarded-Proto: https\r\n"
                     f"X-Forwarded-Scheme: https\r\n"
                     f"X-Scheme: https\r\n"
                     f"X-Original-Forwarded-For: 1.1.1.1\r\n"
                     f"X-Client-IP: {CLIENT_IP}\r\n"
                     f"Destination: /asdasdasd/asdasdas/asdasd123/123 asdasd.ttx\r\n"
                     f"User-Agent: Mozilla/5.0 (Macintosh) mirall/3.13.0git (build 22490)"
                     f" (Nextcloud, osx-24.4.0 ClientArchitecture: arm64 OsArchitecture: arm64)\r\n"
                     f"{add_hdr_http()}"
                     # f"Transfer-Encoding: chunked\r\n"
                     f"Content-Length: {contlen_req}\r\n"
                     f"Content-Type: application/octet-stream\r\n"
                     f"\r\n").encode()
    icap_head_req = (f"REQMOD icap://{SERVER}:{PORT}/icap/reqmod ICAP/1.0\r\n"
                     f"{add_hdr_icap(username)}"
                     f"Encapsulated: req-hdr=0, req-body={len(http_head_req)}\r\n"
                     f"\r\n").encode()
    hdr = icap_head_req + http_head_req
    return hdr


def sender(conn, headers, filename):
    print(f"Thread ID {current_thread().ident}")
    st = time.time()
    conn = check_sockets(conn)
    if not isinstance(headers, bytes):
        conn.send(headers[0])
        body = headers[1]
    else:
        conn.send(headers)
        body = b''
        if 'null-body=' in headers.decode():
            req_time = time.time() - st
            print(f"Request send time: {req_time}.")
            return get_response(conn)
    with open(filename, 'rb') as f:
        body += f.read(CHUNK_SIZE)
        while body:
            if len(body) < CHUNK_SIZE and len(headers) < 4:
                body += headers[2]
            data_len = hex(len(body)).split('x')[-1]
            conn.send(f"{data_len}\r\n".encode())
            conn.send(body)
            conn.send(b'\r\n')
            body = f.read(CHUNK_SIZE)
        conn.send(b'0\r\n\r\n')
    req_time = time.time() - st
    print(f"Request send time: {req_time:.3f}.")
    return get_response(conn)


def get_response(conn):
    print(f"Thread ID {current_thread().ident}")
    st = time.time()
    data, data_chunk = b'', b''
    header_delimiter = b'\r\n\r\n'
    while True:
        data_chunk = conn.recv(1024)
        data += data_chunk
        if data.rfind(b'\r\n0\r\n\r\n') > -1:
            break
        elif data.find(b'204', 9, 12) > -1:
            if data.rfind(b'\r\n\r\n'):
                break
    if data.split(header_delimiter)[0].find(b'\r\nConnection: close\r\n') > -1:
        conn.close()
    resp_time = time.time() - st
    print(f"Response received after: {resp_time:.3f} seconds\r\n{data[:12]}")
    return data


def check_sockets(socket_list):
    if isinstance(socket_list, socket.socket):
        if socket_list.fileno() == -1:
            return connector()
        return socket_list
    else:
        for socket_item in socket_list:
            if socket_item.fileno() == -1:
                socket_item = connector()


def threads_sender(packet_list):
    with ThreadPool(THREADS) as pool:
        pool.map(lambda s: sender(*s), packet_list)
        pool.close()
        pool.join()
    return


if __name__ in "__main__":
    soc = [socket.socket() for _ in range(THREADS)]
    for sock in soc:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((SERVER, PORT))

    start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    st = time.time()

    i = 1
    files_iter = cycle(files)
    users_iter = cycle(users)
    # while True:
    while i < ITERATIONS+1:
        print(f"Итерация {i}")
        file_i = next(files_iter)
        user_i = next(users_iter)
        #check_sockets(soc)
        #arg_list = []
        #print(arg_list)
        #for k in range(THREADS):
        #    file_i = next(files_iter)
        #    user_i = next(users_iter)
        #    arg_list.append((soc[k], search_request(file_i, user_i), file_i))
        #threads_sender(arg_list)
        #time.sleep(0.1)
        #threads_sender([(soc[k],
        #                 search_request(file_i, user_i),
        #                 file_i) for k in range(THREADS)])
        #time.sleep(0.1)
        #threads_sender([(soc[k],
        #                 upload_request(file_i, next(users_iter)),
        #                 file_i) for k in range(THREADS)])
        #time.sleep(0.1)
        #threads_sender([(soc[k],
        #                 upload_request_stream(file_i, next(users_iter)),
        #                 file_i) for k in range(THREADS)])
        #time.sleep(0.1)
        #threads_sender([(soc[k], download_request(file_i, next(users_iter)),
        #                 file_i) for k in range(THREADS)])
        time.sleep(0.1)
        threads_sender([(soc[k], upload_request_nextcloud(file_i, next(users_iter)),
                         file_i) for k in range(THREADS)])
        #check_sockets(soc)
        #with ThreadPool(THREADS) as pool:
        #    pool.map(lambda s: send_chunks(*s), [(soc[k], FILE) for k in range(THREADS)])
        #    pool.close()
        #    pool.join()
        i += 1

    for sock in soc:
        sock.close()

    finish = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print(f"\r\nStart time: {start}\r\nFinish time: {finish}\r\nTest time: {(time.time() - st):.3f} sec.")
else:
    print(f"Imported {__name__}")
