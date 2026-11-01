from nova.core.session import Session
from nova.core.events import Event

def main() -> None:
    s = Session()
    s.emit(Event(type="user_message", data={"text": "hello"}))
    s.patch_state({"foo": 123})
    s.emit(Event(type="assistant_message", data={"text": "hi there"}))

    print("Session id:", s.id)
    print("State:", s.state)
    print("Events:")
    for e in s.events:
        print(f"- {e.ts.isoformat()} {e.type} {e.data}")

if __name__ == "__main__":
    main()
