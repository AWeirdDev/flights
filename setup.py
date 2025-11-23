from setuptools import setup

if __name__ == "__main__":
    setup(
        entry_points={
            "console_scripts": [
                "flights-cli=fast_flights.cli:main",
            ],
        }
    )

# testing
