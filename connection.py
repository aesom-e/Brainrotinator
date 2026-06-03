import bluetooth

class BTServer:
    def __init__(self, name="PiServer"):
        self.name = name
        self.mac = bluetooth.read_local_bdaddr()
        self.server_sock = None
        self.client_sock = None

    def start(self) -> None:
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)
        port = self.server_sock.getsockname()[1]
        bluetooth.advertise_service(
            self.server_sock,
            self.name,
            service_classes=[bluetooth.SERIAL_PORT_CLASS]
        )
        print(f"Server MAC: {self.mac}")
        print(f"Waiting for connection on port {port}...")
        self.client_sock, info = self.server_sock.accept()
        print(f"Connected: {info}")

    def send(self, message: str) -> None:
        self.client_sock.send(message.encode())

    def receive(self, buffer=1024) -> str:
        return self.client_sock.recv(buffer).decode()

    def close(self) -> None:
        if self.client_sock is not None: self.client_sock.close()
        if self.server_sock is not None: self.server_sock.close()

class BTClient:
    def __init__(self, server_mac: str, port=1):
        self.server_mac = server_mac
        self.port = port
        self.sock = None

    def connect(self) -> None:
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((self.server_mac, self.port))
        print(f"Connected to {self.server_mac}")

    def send(self, message: str) -> None:
        self.sock.send(message.encode())

    def receive(self, buffer=1024) -> str:
        return self.sock.recv(buffer).decode()

    def close(self) -> None:
        if self.sock is not None: self.sock.close()