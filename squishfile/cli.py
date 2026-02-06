import webbrowser
import uvicorn


def main():
    host = "127.0.0.1"
    port = 8000
    print(f"\n  SquishFile is running at http://{host}:{port}\n")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run("squishfile.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
