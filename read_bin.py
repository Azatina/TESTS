import socket
import time

FILE = 'post.bin'
SERVER = '192.168.1.203'
PORT = 1344
delimiter = b'\r\n\r\n'

with open('post.bin', 'rb') as f:
        request = f.read()
idx = request.index(delimiter)
http_hdr = request[:idx] + delimiter
body = request[(idx + len(delimiter)):-1]

# http_hdr = request.split(delimiter)[0] + delimiter
# body = request.split(delimiter)[1:]

http_hdr = (f"POST /web-api/upload-attachment/liza1 HTTP/1.1\r\n"
            f"Host: mail.yandex.ru\r\n"
            f"Content-Type: multipart/form-data; boundary=------------------------kdfc64x3m5gcactq\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n").encode()

icap_hdr = (f"REQMOD icap://{SERVER}:{PORT}/icap/reqmod ICAP/1.0\r\n"
            f"Host: {SERVER}\r\n"
            f"Allow: 204\r\n"
            f"X-Authenticated-User: V2luTlQ6Ly96ZWN1cmlvbi5sb2NhbFxhemF0\r\n"
            f"X-Client-IP: 192.168.0.121\r\n"
            f"Encapsulated: req-hdr=0, req-body={len(http_hdr)}\r\n"
            f"\r\n").encode()

print(len(body))

with socket.socket() as soc:
    soc.connect((SERVER, PORT))
    soc.send(icap_hdr)
    soc.send(http_hdr)
    soc.send(f"{hex(len(body)).split('x')[-1]}\r\n".encode())
    soc.send(body)
    soc.send(b'\r\n0\r\n\r\n')
    while True:
        data = soc.recv(4096)
        print(data.decode())
        if not data:
            break
