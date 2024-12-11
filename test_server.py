import sys
import threading
import socket
import argparse

class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.connections = []

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(1)
        print("Listening at", sock.getsockname())

        while True:
            # Accepting new connection
            sc, sockname = sock.accept()
            print(f"Accepting new connection from {sc.getpeername()} to {sc.getsockname()}")

            # Creating a new thread for the client connection
            server_socket = ServerSocket(sc, sockname, self)
            server_socket.start()

            # Add the thread to active connections
            self.connections.append(server_socket)
            print("Ready to receive messages from", sc.getpeername())

    def broadcast(self, message, source):
        for connection in self.connections:
            # Send to all connected clients except the source client
            if connection.sc != source:
                connection.send(message)

    def remove_connection(self, connection):
        self.connections.remove(connection)


class ServerSocket(threading.Thread):
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server

    def run(self):
        while True:
            message = self.sc.recv(1024).decode('ascii')
            if message:
                print(f"{self.sockname} says {message}")
                self.server.broadcast(message, self.sc)
            else:
                print(f"{self.sockname} has closed the connection")
                self.sc.close()
                # Remove the connection from the server's list
                self.server.remove_connection(self)
                return

    def send(self, message):
        self.sc.sendall(message.encode('ascii'))


def shutdown_server(server):
    while True:
        ipt = input("")
        if ipt == "exit":
            print("Closing all connections")
            for connection in server.connections:
                connection.sc.close()
            print("Shutting down the server...")
            sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chatroom server")
    parser.add_argument("host", help="Interface the server listens at")
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    args = parser.parse_args()

    # Create and start server thread
    server = Server(args.host, args.p)
    server.start()

    # Create and start the shutdown thread
    exit_thread = threading.Thread(target=shutdown_server, args=(server,))
    exit_thread.start()
