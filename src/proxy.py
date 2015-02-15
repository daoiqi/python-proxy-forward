#!/usr/bin/env python
# coding: utf-8

import time
import socket
import socks  #third part plugin
import threading,signal,os,sys
import ConfigParser,copy,re

def log(msg):
    print '[%s] %s' % (time.ctime(),msg)

def pid_exists(pid):
    """
    from http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
    """
    if os.name == 'posix':
        """Check whether pid exists in the current process table."""
        import errno
        if pid < 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError as e:
            return e.errno == errno.EPERM
        else:
            return True
    else:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x100000

        process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
        if process != 0:
            kernel32.CloseHandle(process)
            return True
        else:
            return False


is_exit = False

class ForwardServer(object):
    PAGE_SIZE = 4096
    def __init__(self):
        self.listen_host = None
        self.listen_port = None
        self.remote_host = None
        self.remote_port = None
        self.proxy_host = None
        self.proxy_port = None



    def setListen(self,host,port):
        self.listen_host = host
        self.listen_port = port
        return self

    def setRemote(self,host,port):
        self.remote_host = host
        self.remote_port = port
        return self

    def setProxySocks5(self,host,port):
        self.proxy_host = host
        self.proxy_port = port
        return self

    def _listen(self):
        sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #tcp
        sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_server.bind((self.listen_host, self.listen_port))
        sock_server.listen(5)
        log('Listening at %s:%d ...' % (self.listen_host, self.listen_port))
        return sock_server

    def serve(self):
        sock_server = self._listen()

        while not is_exit:
            try:
                sock, addr = sock_server.accept()
            except (KeyboardInterrupt, SystemExit):
                log('Closing...')
                sock_server.shutdown(socket.SHUT_RDWR)
                sock_server.close()
                #sys.exit(0)
                break
            except Exception:
                log('exception exit')
                sock_server.shutdown(socket.SHUT_RDWR)
                sock_server.close()
                #sys.exit(-1)
                break

            threading.Thread(target=self._forward, args=(sock,) ).start()
            log('New clients from %s:%d' % addr)

        log('exit server')

    def _forward(self,sock_in):
        sock_out = None
        try:
            print self.remote_host,self.remote_port
            sock_out = ForwardClient(self.remote_host,self.remote_port,self.proxy_host,self.proxy_port).getClient()
            log('get the client socks done')
        except Exception, e:
            log('get Remote Client error: %s' % str(e))
            raise e
            return

        threading.Thread(target=self._do_data_forward, args=(sock_in, sock_out)).start()
        threading.Thread(target=self._do_data_forward, args=(sock_out, sock_in)).start()

    def _do_data_forward(self,sock_in,sock_out):
        addr_in = '%s:%d' % sock_in.getpeername()
        addr_out = '%s:%d' % sock_out.getpeername()

        while True:
            try:
                data = sock_in.recv( ForwardServer.PAGE_SIZE )
            except Exception, e:
                log('Socket read error of %s: %s' % (addr_in, str(e)))
                break

            if not data:
                log('Socket closed by ' + addr_in)
                break

            try:
                sock_out.sendall(data)
            except Exception, e:
                log('Socket write error of %s: %s' % (addr_out, str(e)))
                break

            log('%s -> %s (%d B)' % (addr_in, addr_out, len(data)))

        sock_in.close()
        sock_out.close()


class ForwardClient(object):
    def __init__(self,host,port,proxy_host=None,proxy_port=None):
        self.remote_host = host
        self.remote_port = port
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def setRemote(self,host,port):
        self.remote_host = host
        self.remote_port = port
        return self

    def setProxySocks5(self,host,port):
        self.proxy_host = host
        self.proxy_port = port
        return self

    def getClient(self):
        sock_out = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        if self.proxy_host is not None and self.proxy_port is not None:
            sock_out.setproxy(socks.PROXY_TYPE_SOCKS5, self.proxy_host, self.proxy_port)
            log('using socks proxy %s:%d' % ( self.proxy_host,self.proxy_port))

        try:
            print 'remote,=',(self.remote_host, self.remote_port)
            sock_out.connect((self.remote_host, self.remote_port))
        except socket.error, e:
            sock_out.close()
            log('Remote connect error: %s' % str(e))
            raise Exception,'Remote connect error: %s' % str(e)

        return sock_out


class Config(object):
    def parser(self,filename):
        config = ConfigParser.SafeConfigParser()
        config.read(filename)

        dictionary = {}
        for section in config.sections():
            dictionary[section] = {}
            for option in config.options(section):
                dictionary[section][option] = config.get(section, option)
        return dictionary


def handler(signum, frame):
    print signum , frame
    global is_exit
    is_exit = True
    print "receive a signal %d, is_exit = %d"%(signum, is_exit)

def start():
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            log('parent process exit')
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

        ## write pid
    pid = str(os.getpid())
    pidfile = "./proxy_daemon.pid"

    if os.path.isfile(pidfile):
        f = open(pidfile,'r')
        filePid = int(f.read())
        log('read pid file pid=%s' % filePid)
        if pid_exists(filePid):
            log( "%s already exists, and pid=%s exists exiting" % (pidfile , filePid ) )
            sys.exit()
        else:
            log('the pid file pid=%s not exists' % filePid)
        f.close()

    file(pidfile, 'w').write(pid)
    log('write pid to %s' % pidfile)

    log('now is child process do')

    re_ip_port = r'^(?P<addr>.+:)?(?P<port>[0-9]{1,5})$'
    conf = Config()
    data = conf.parser('proxy.ini')
    for key in data.keys():
        print key
        print data[key]
        listen = data[key].get('listen')
        remote = data[key].get('remote')
        proxy = data[key].get('socks5',None)

        local_addr,local_port = None,None
        remote_addr,remote_port = None,None
        socks5_addr,socks5_port = None,None

        x = re.match(re_ip_port, listen)
        if not x:
            log('listen format error!')
            exit(-1)
        local_addr = x.group('addr') or '0.0.0.0'
        local_addr = local_addr.rstrip(':')
        local_port = int(x.group('port'))

        x = re.match(re_ip_port, remote)
        if not x:
            log('listen format error!')
            exit(-1)
        remote_addr = x.group('addr') or '0.0.0.0'
        remote_addr = remote_addr.rstrip(':')
        remote_port = int(x.group('port'))

        if proxy:
            x = re.match(re_ip_port, proxy)
            if not x:
                log('listen format error!')
                exit(-1)
            socks5_addr = x.group('addr') or '0.0.0.0'
            socks5_addr = socks5_addr.rstrip(':')
            socks5_port = int(x.group('port'))

        def proxy(local_addr,local_port,remote_addr,remote_port,socks5_addr,socks5_port):
            serv = ForwardServer()
            print local_addr,local_port,remote_addr,remote_port,socks5_addr,socks5_port
            serv.setListen(local_addr,local_port).setRemote(remote_addr,remote_port).setProxySocks5(socks5_addr,socks5_port)
            serv.serve()


        threading.Thread(target=proxy,args=(local_addr,local_port,remote_addr,remote_port,socks5_addr,socks5_port)).start()

    log('start all proxy done')

def exit():
    pidfile = "./proxy_daemon.pid"
    os.remove(pidfile)
    log('exit')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    #options = Config().parser('proxy.ini')
    #print options
    #serv = ForwardServer()
    #serv.serve()
    start()


