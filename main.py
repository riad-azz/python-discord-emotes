from json import load as load_json
from os import path

from utils.app import MyApp, Downloader


def is_ready():
    if not path.exists("./config.json"):
        return False

    with open("config.json", "r", encoding="utf-8") as file:
        try:
            conf = load_json(file)
        except:
            return False

    return conf.get("saved", False)


def run_app():
    with open("config.json", "r", encoding="utf-8") as file:
        data = load_json(file)

    app = MyApp(data)
    app.mainloop()
    # Close the app upon exit
    quit()


def run_downloader():
    downloader = Downloader()
    downloader.mainloop()


def main():
    if is_ready():
        run_app()
    else:
        run_downloader()


if __name__ == '__main__':
    main()
