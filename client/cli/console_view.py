from client.events import ViewEvent, ViewEventKind, ClientStatus

class ConsoleView:
    async def show_event(self, event: ViewEvent) -> None:
        if event.kind is ViewEventKind.USERS:
            print(f"users: {event.text}")
        elif event.kind is ViewEventKind.ERROR:
            print(f"error: {event.text}")
        elif event.kind is ViewEventKind.DISCONNECTED:
            print(f"disconnected: {event.text}")
        else:
            print(event.text)

    async def show_status(self, status: ClientStatus) -> None:
        print(f"status: {status.value}")

    async def show_local_error(self, message: str) -> None:
        print(f"error: {message}")