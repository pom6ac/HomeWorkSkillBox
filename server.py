#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports

login_list = []
history_messages = []
max_size = 10

class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                if self.login in login_list:
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой\n".encode()
                    )
                    self.transport.close()
                else:
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    login_list.append(self.login)
                    HistoryManager.show_history(self)
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        message_enc = message.encode()
        HistoryManager.add_message(message_enc)

        for user in self.server.clients:
            user.transport.write(message_enc)


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


class HistoryManager:
    def add_message(data):
        size_history = history_messages.__len__()
        if size_history >= max_size:
            history_messages.pop(0)

        history_messages.append(data)

    def show_history(self):
        for i in history_messages:
            self.transport.write(i)

process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")