import socket

host = '192.168.0.121'        # Symbolic name meaning all available interfaces
port = 1344     # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
print(host , port)
s.listen(1)
conn, addr = s.accept()
print('Connected by', addr)

while True:
    try:
        data = conn.recv(1024)
        if not data:
            break
        elif '123qwe' in data.decode().lower():
        #print("Client Says: " + data.decode())
            conn.sendall(b"ICAP/1.0 200 OK\r\nService-ID: ZgateICAPProxy\r\n\
Service: Zgate_ICAP_Proxy\r\n\
X-Include: X-Client-IP, X-Client-Username, X-Authenticated-User\r\n\
Methods: REQMOD\r\n\
Connection: close\r\n\
ISTag: 'W3E4R7U9-L2E4-2'\r\n\
X-Need-Response: no\r\n\
Encapsulated: res-hdr=0, res-body=119\r\n\
\r\n\
HTTP/1.0 403 Forbidden\r\n\
Service: Zgate_ICAP_Proxy\r\n\
Connection: close\r\n\
Content-Type: text/html\r\n\
Content-Language: en\r\n\
\r\n\
18\r\n\
Blocked by ICAP-server\x20\x20\r\n\
0\r\n\
\r\n")
        else:
            conn.sendall(b"ICAP/1.0 204 OK\r\n\
Methods: REQMOD\r\n\
ISTag: 'W3E4R7U9-L2E4-2'\r\n\
Server: Zgate_ICAP_Proxy\r\n\
X-Need-Response: no\r\n\
Connection: close\r\n\
\r\n")
    except socket.error as err:
        print(err)
        pass
    
    except KeyboardInterrupt:
        break

    data = None
    conn, addr = s.accept()
conn.close()
