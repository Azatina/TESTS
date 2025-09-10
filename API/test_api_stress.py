import time
from multiprocessing.dummy import Pool as ThreadPool
from threading import current_thread

from test_api import *


def api_test(args):
    global GUID_LIST
    connection, arg = args
    f_st_time = time.time()
    data = send_request(connection, check_api(*arg))
    GUID = json.loads(data.split("\r\n")[-1])["id"]
    print(GUID)
    GUID_LIST.append(GUID)
    send_request(connection, upload(quote(GUID), next(files_iter)))
    status_api = 'status'
    while status_api != 'failed':  # 'processed'
        data = send_request(connection, status(quote(GUID)))
        parsed = json.loads(data.split("\r\n")[-1])
        status_api = parsed.get('status', None)
        time.sleep(0.1)
    GUID_LIST.remove(GUID)
    print(f"Thread ID {current_thread().ident} worktime {(time.time() - f_st_time):.3f} sec")


GUID_LIST = []
soc = [connector() for _ in range(THREADS)]

files = file_list(TEST_PATH)
users = user_list(USERSFILE)

files_iter = cycle(files)
users_iter = cycle(users)

start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
st = time.time()

i = 1
while i <= ITERATIONS:
    with ThreadPool(THREADS) as pool:
        results = pool.map(api_test, [(soc[k], (f"file",
                                                None,
                                                None,
                                                f"{next(users_iter)}",
                                                f"computer{i}-{k}.zecurion.local",
                                                f"{split_path(next(files_iter))[-1]}",
                                                None,
                                                None))
                                      for k in range(THREADS)])
        pool.close()
        pool.join()
    i += 1

finish = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
print(f"\r\nStart time: {start}\r\nFinish time: {finish}")
print(f"Work time: {(time.time() - st):.3f} sec")

for sock in soc:
    sock.close()
