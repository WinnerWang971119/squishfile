import socket
import webbrowser
import uvicorn


def _find_port(start=8000, end=8100) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def main():
    host = "127.0.0.1"
    port = _find_port()
    print(f"\n  SquishFile is running at http://{host}:{port}\n")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run("squishfile.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
