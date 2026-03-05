"""
Hey Dongle — Entry Point
A zero-setup, USB-portable agentic coding assistant for offline environments.
"""

from hey_dongle.app import HeyDongleApp


def main():
    app = HeyDongleApp()
    app.run()


if __name__ == "__main__":
    main()
