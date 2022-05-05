


import socket, sys, datetime, time
from _thread import start_new_thread


class ProxyServer:
    def __init__(self, blacklisted_ips=False, blacklist_websites=False):
        self.max_conn = 0
        self.buffer_size = 0
        self.socket = 0
        self.port = 0
        self.black_IP = blacklisted_ips
        self.black_web = blacklist_websites

    def write_in_log(self, msg):
        with open("log.txt", "a+") as file:
            file.write(msg)
            file.write("\n")


    def start_server(self, conn=5, buffer=4096, port=8080):
        try:
            self.write_in_log("   \n\nStarting ProxyServer\n\n")

            self.listen(conn, buffer, port)

        except KeyboardInterrupt:
            self.write_in_log("   Interrupting ProxyServer.")

        finally:
            self.write_in_log("   Stopping ProxyServer")
            sys.exit()

    def listen(self, No_of_conn, buffer, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', port))
            s.listen(No_of_conn)
            print("   Listening...")
            self.write_in_log(
                "   Listening...")

        except:
            self.write_in_log("   Error: Cannot start listening...")
            sys.exit(1)

        while True:
            try:
                conn, addr = s.accept()
                self.write_in_log(
                    "   Request received from: " + addr[0] + " at port: " + str(addr[1]))
                start_new_thread(self.connection_read_request, (conn, addr, buffer))

            except Exception as e:
                print("  Error: Cannot establish connection..." + str(e))
                self.write_in_log("  Error: Cannot establish connection..." + str(e))
                sys.exit(1)

        s.close()

    def generate_header_lines(self, code, length):
        header = ''
        if code == 200:
            header = 'HTTP/1.1 200 OK\n'
            header += 'Server: Jarvis\n'

        elif code == 404:
            header = 'HTTP/1.1 404 Not Found\n'
            header += 'Date: ' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) + '\n'
            header += 'Server: Jarvis\n'

        header += 'Content-Length: ' + str(length) + '\n'
        header += 'Connection: close\n\n'

        return header

    def connection_read_request(self, conn, addr, buffer):
        try:
            request = conn.recv(buffer)
            header = request.split(b'\n')[0]
            requested_file = request
            requested_file = requested_file.split(b' ')
            url = header.split(b' ')[1]

            host = url.find(b"://")
            if host == -1:
                temp = url
            else:
                temp = url[(host + 3):]

            portIndex = temp.find(b":")

            serverIndex = temp.find(b"/")
            if serverIndex == -1:
                serverIndex = len(temp)

            webserver = ""
            port = -1
            if (portIndex == -1 or serverIndex < portIndex):
                port = 80
                webserver = temp[:serverIndex]
            else:
                port = int((temp[portIndex + 1:])[:serverIndex - portIndex - 1])
                webserver = temp[:portIndex]

            requested_file = requested_file[1]

            method = request.split(b" ")[0]

            if addr[0] in self.black_IP:
                self.write_in_log("   IP Blacklisted")
                conn.close()

            target = webserver
            target = target.replace(b"http://", b"").split(b".")[1].decode("utf-8")
            try:
                if target in self.black_web:
                    self.write_in_log("   Website Blacklisted")
                    conn.close()
            except:
                pass

            if method == b"CONNECT":
                self.write_in_log("   HTTPS Connection request")
                self.https_proxy(webserver, port, conn, request, addr, buffer, requested_file)

            else:
                self.write_in_log("   HTTP Connection request")
                self.http_proxy(webserver, port, conn, request, addr, buffer, requested_file)

        except Exception as e:
            self.write_in_log(str(e))
            return

    def http_proxy(self, webserver, port, conn, request, addr, buffer_size, requested_file):
        requested_file = requested_file.replace(b".", b"").replace(b"http://", b"").replace(b"/", b"")

        try:

            file_handler = open(b"cache/" + requested_file, 'rb')
            self.write_in_log("  Cache Hit")
            response_content = file_handler.read()
            file_handler.close()
            response_headers = self.generate_header_lines(200, len(response_content))
            conn.send(response_headers.encode("utf-8"))
            time.sleep(1)
            conn.send(response_content)
            conn.close()

        except Exception as e:
            print(e)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((webserver, port))
                s.send(request)

                self.write_in_log(
                    "  Forwarding request from " + addr[0] + " to host..." + str(webserver))
                file_object = s.makefile('wb', 0)
                file_object.write(b"GET " + b"http://" + requested_file + b" HTTP/1.0\n\n")
                file_object = s.makefile('rb', 0)
                buff = file_object.readlines()
                temp_file = open(b"cache/" + requested_file, "wb+")
                for i in range(0, len(buff)):
                    temp_file.write(buff[i])
                    conn.send(buff[i])

                self.write_in_log("  Request of client " + str(addr[0]) + " completed...")
                s.close()
                conn.close()

            except Exception as e:
                self.write_in_log(str(e))
                return

    def https_proxy(self, webserver, port, conn, request, addr, buffer_size, requested_file):
        requested_file = requested_file.replace(b".", b"").replace(b"http://", b"").replace(b"/", b"")

        try:
            file_handler = open(b"cache/" + requested_file, 'rb')
            self.write_in_log("  Cache Hit\n")
            response_content = file_handler.read()
            file_handler.close()
            response_headers = self.generate_header_lines(200, len(response_content))
            conn.send(response_headers.encode("utf-8"))
            time.sleep(1)
            conn.send(response_content)
            conn.close()

        except:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((webserver, port))
                reply = "HTTP/1.0 200 Connection established\r\n"
                reply += "Proxy-agent: Jarvis\r\n"
                reply += "\r\n"
                conn.sendall(reply.encode())
            except socket.error as err:
                pass

            conn.setblocking(0)
            s.setblocking(0)
            self.write_in_log("  HTTPS Connection Established")
            while True:
                try:
                    request = conn.recv(buffer_size)
                    s.sendall(request)
                except socket.error as err:
                    pass

                try:
                    reply = s.recv(buffer_size)
                    conn.sendall(reply)
                except socket.error as e:
                    pass


if __name__ == "__main__":
    server = ProxyServer(['127.0.0.81'],['facebook'])
    server.start_server()