
import socket
import struct

from flask import request


def get_client_ip():
    try:
        ip = request.headers['X-Forwarded-For'].split(',')[0]
    except:
        ip = request.remote_addr
    return ip


def get_ip_address(ifname):
    '''根据网卡获取IP地址

    :param ifname: 网口名称
    '''
    import fcntl
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def get_local_ip():
    '''获取本机内网IP'''
    local_ip = ''
    try:
        socket_objs = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
        ip_from_ip_port = [(s.connect(('8.8.8.8', 53)), s.getsockname()[
            0], s.close()) for s in socket_objs][0][1]
        local_ip = ip_from_ip_port
        ip_from_host_name = [ip for ip in socket.gethostbyname_ex(
            socket.gethostname())[2] if not ip.startswith('127.')][:1]
        local_ip = [l for l in (ip_from_ip_port, ip_from_host_name) if l][0]
    except (Exception) as e:
        print('get_local_ip found exception : %s local_ip: %s' % (e, local_ip))

    return local_ip if ('' != local_ip and None != local_ip) else '127.0.0.1'


def ip2long(ip):
    '''Convert an IP string to long'''
    packedIP = socket.inet_aton(ip)
    return struct.unpack('!L', packedIP)[0]


def long2ip(num):
    '''Convert an long to IP string'''
    return socket.inet_ntoa(struct.pack('!L', num))


if __name__ == '__main__':
    print(get_local_ip())
