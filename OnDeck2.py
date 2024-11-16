"""
Main file for the OnDeck project. This file starts all the necessary
processes for the project to run. It uses processes instead of threading
because blocking processes can mess with the hub75 display timings.
"""

from multiprocessing import Process
import time

from on_deck2.fetcher import Fetcher
from on_deck2.server import Server
from on_deck2.scoreboard import Scoreboard

def start_fetcher():
    """
    Starts the fetcher
    """
    fetcher = Fetcher()
    fetcher.start()

def start_server():
    """
    Starts the server
    """
    server = Server()
    server.start()

def start_scoreboard():
    """
    Starts the scoreboard
    """
    scoreboard = Scoreboard()
    scoreboard.start()

def main():
    """
    Main function
    """
    try:
        fetcher_process = Process(target=start_fetcher)
        server_process = Process(target=start_server)

        fetcher_process.start()
        server_process.start()

        print('Make sure to start the scoreboard manually as sudo')

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        fetcher_process.terminate()
        server_process.terminate()

        fetcher_process.join()
        server_process.join()

if __name__ == '__main__':
    main()
