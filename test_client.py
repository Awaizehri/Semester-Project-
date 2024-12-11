import sys
import threading
import socket
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets

# from client import Recieve

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None
        self.messages = None

    def start(self):
        try:
            self.sock.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            self.name = input("Your name: ")
            print(f"Welcome, {self.name}! Type 'Quit' to exit the chat.")
            
            send = Send(self.sock, self.name)
            receive = Recieve(self.sock, self.name)
            
            send.start()
            receive.start()
            
            self.sock.sendall(f"Server: {self.name} has joined the chat.".encode('ascii'))
            return receive
        except Exception as e:
            print("Unable to connect to the server:", e)
            sys.exit()

    def send(self, textInput):
        message = textInput.text()
        textInput.clear()
        self.messages.addItem(f"{self.name}: {message}")
        
        if message.lower() == "quit":
            self.sock.sendall(f"Server: {self.name} has left the chat room.".encode('ascii'))
            print("Quitting...")
            self.sock.close()
            sys.exit(0)
        else:
            self.sock.sendall(f"{self.name}: {message}".encode('ascii'))

class Send(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock  # Client socket for sending messages to the server
        self.name = name  # Username of the client

    def run(self):
        # Continuously prompts user for input and sends messages to the server
        while True:
            message = sys.stdin.readline()[:-1]  # Read input from the user

            # If the user types "Quit," it notifies the server and exits
            if message == "Quit":
                self.sock.sendall(f"server {self.name} has left the chat.".encode('ascii'))
                break

            # Sends the user's message to the server
            self.sock.sendall(f"{self.name}: {message}".encode('ascii'))
        
        # Cleanup actions upon quitting
        print('\n Quitting...')
        self.sock.close()
        sys.exit(0)

# This thread handles receiving messages from the server and displaying them in the GUI.
class Recieve(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock  # Client socket for receiving messages from the server
        self.name = name  # Username of the client
        self.messages = None  # GUI element to display messages

    def run(self):
        # Continuously listens for incoming messages from the server
        while True:
            message = self.sock.recv(1024).decode('ascii')  # Decode incoming messages

            # Display received messages in both the terminal and the GUI if available
            if message:
                if self.messages:
                    self.messages.addItem(message)  # Insert message into the ListView in the GUI
                    print(f'{message}\n{self.name}: ', end='')

                print(f'{message}\n{self.name}: ', end='')

            else:
                # If connection is lost, notify the user and close the socket
                print('We have lost the connection to the server')
                print('\nConnection closed')

                self.sock.close()
                sys.exit(0)

def main(host, port):
    client = Client(host, port)
    receive = client.start()

    app = QtWidgets.QApplication(sys.argv)

    window = QtWidgets.QWidget()
    window.setWindowTitle("Chat Room")

    # Create layout
    layout = QtWidgets.QHBoxLayout(window)

    # Left side for receiving messages
    leftPanel = QtWidgets.QWidget(window)
    leftLayout = QtWidgets.QVBoxLayout(leftPanel)

    messages = QtWidgets.QListWidget()
    leftLayout.addWidget(messages)
    leftPanel.setLayout(leftLayout)

    # Right side for sending messages
    rightPanel = QtWidgets.QWidget(window)
    rightLayout = QtWidgets.QVBoxLayout(rightPanel)

    # Input field for text
    textInput = QtWidgets.QLineEdit()
    rightLayout.addWidget(textInput)

    # Send button
    btnSend = QtWidgets.QPushButton("Send")
    rightLayout.addWidget(btnSend)

    rightPanel.setLayout(rightLayout)

    # Add the panels to the main layout
    layout.addWidget(leftPanel)
    layout.addWidget(rightPanel)

    # Set up the window and start the GUI
    window.setLayout(layout)
    window.show()

    client.messages = messages
    receive.messages = messages

    # Bind the Send button and enter key to the send action
    btnSend.clicked.connect(lambda: client.send(textInput))
    textInput.returnPressed.connect(lambda: client.send(textInput))

    sys.exit(app.exec_())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chatroom client")
    parser.add_argument("host", help="Interface the server listens at")
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    args = parser.parse_args()

    main(args.host, args.p)
