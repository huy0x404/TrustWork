"""
Local development server for TrustWork.
Starts an HTTP server on port 3000 and prints friendly access links.
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Clean logging
        sys.stdout.write(f"[TrustWork HTTP] {self.address_string()} - {format % args}\n")

def run():
    os.chdir(DIRECTORY)
    # Find free port if 3000 is taken
    port = PORT
    for attempt in range(10):
        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                url = f"http://localhost:{port}"
                print("=" * 60)
                print(" ⚖️  TrustWork - AI-Arbitrated Freelance Escrow on GenLayer")
                print("=" * 60)
                print(f" Web dApp live at:  {url}")
                print(f" Directory:         {DIRECTORY}")
                print(f" Interactive Demo:  Ready in browser")
                print("=" * 60)
                print("Press Ctrl+C to stop the server.\n")
                
                try:
                    webbrowser.open(url)
                except Exception:
                    pass

                httpd.serve_forever()
                break
        except OSError:
            port += 1

if __name__ == "__main__":
    run()

