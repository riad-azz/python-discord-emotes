import functools
import json
import time
from multiprocessing.pool import ThreadPool
from threading import Thread
from tkinter import StringVar
from tkinter.font import Font

from customtkinter import CTk, CTkLabel, CTkFrame, CTkButton, CTkEntry, CTkCanvas, CTkScrollbar, CTkOptionMenu
from customtkinter import set_appearance_mode as set_theme

from utils.dialog_box import MessageBox
from utils.discord_utils import *

# Set app theme
set_theme("dark")


class Downloader(CTk):
    def __init__(self):
        # -- Theme and window settings --
        super().__init__()
        self.title("Discord Emotes")
        self.WIDTH = 400
        self.HEIGHT = 200
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(self.WIDTH, self.HEIGHT)
        self.maxsize(self.WIDTH, self.HEIGHT)
        # -- App Vars --
        self.token = None
        self.data = {
            "token": None,
            "user": dict(),
            "servers": dict(),
        }
        self.check = {"user": False,
                      "servers": False,
                      "channels": False,
                      "emotes": False,
                      "download_avatar": False,
                      "download_emotes": False}
        self.emotes_urls = []
        self.download_thread = Thread(target=self._run_app)
        self.done = False
        # -- App Widgets --
        # - User input frame -
        self.input_frame = CTkFrame(self)
        self.input_frame.pack(fill="both", expand=True)
        # Info label
        self.label = CTkLabel(self.input_frame, text="Enter Discord Token", height=40, text_font=Font(size=18))
        self.label.pack(fill="x", expand=True)
        # User input
        self.entry = CTkEntry(self.input_frame, height=35, text_font=Font(size=12))
        self.entry.pack(fill="x", expand=False, padx=20)
        # Start the app
        self.button = CTkButton(self.input_frame, text="Run App", height=40, text_font=Font(size=16, weight="bold"),
                                command=self.run_app)
        self.button.pack(expand=True, pady=(10, 15))
        # - Progress frame -
        self.prog_frame = CTkFrame(self)
        self.prog_var = StringVar()
        self.prog_var.set("Getting ready, this might take some time")
        self.l_progress = CTkLabel(self.prog_frame, text_font=Font(size=14), textvariable=self.prog_var)
        self.l_progress.pack(fill="both", expand=True)

    def get_user(self):
        try:
            user = fetch_user(self.token)
        except Exception as e:
            MessageBox(self, "Error", e)
            return False

        _username = user['username']
        _avatar_url = f'https://cdn.discordapp.com/avatars/{user["id"]}/{user["avatar"]}.png'
        _user_tag = "#" + user['discriminator']

        self.data["token"] = self.token
        self.data["user"] = {"avatar_url": _avatar_url,
                             "username": _username,
                             "user_tag": _user_tag}

        self.check["user"] = True
        return True

    def get_servers(self):
        try:
            servers = fetch_servers(self.data["token"])
        except Exception as e:
            MessageBox(self, "Error", e)
            return False

        for server in servers:
            _id = server["id"]
            _name = server["name"]
            _icon = server["icon"]
            server_obj = {"id": _id,
                          "icon": _icon,
                          "channels": [],
                          "emotes": []}
            self.data["servers"][_name] = server_obj

        self.check["servers"] = True
        return True

    def get_channels(self):
        channels = dict()
        for server in self.data["servers"]:
            try:
                server_id = self.data["servers"][server]["id"]
                channels[server] = fetch_channels(self.data["token"], server_id)
            except Exception as e:
                MessageBox(self, "Error", e)
                return False

        for server in channels:
            for channel in channels[server]:
                # Ignore voice chat channels
                if channel["type"] != 0:
                    continue
                _id = channel["id"]
                _name = channel["name"]
                _server_id = channel["guild_id"]
                channel_obj = {"id": _id,
                               "name": _name,
                               "server_id": _server_id}
                self.data["servers"][server]["channels"].append(channel_obj)

        self.check["channels"] = True
        return True

    def get_emotes(self):
        emotes = dict()
        for server in self.data["servers"]:
            try:
                server_id = self.data["servers"][server]["id"]
                if server_id == "431131676798746624":
                    continue
                emotes[server] = fetch_server_emotes(self.data["token"], server_id)
            except Exception as e:
                MessageBox(self, "Error", e)
                return False

        for server in emotes:
            server_id = self.data["servers"][server]["id"]
            emotes_list = emote_fromJson(emotes[server], server_id)
            self.data["servers"][server]["emotes"] = emotes_list
            for emote in emotes_list:
                download_obj = {"file_name": emote["file_name"],
                                "url": emote["thumbnail"]}
                self.emotes_urls.append(download_obj)

        self.check["emotes"] = True
        return True

    def download_avatar(self):
        avatar_url = self.data["user"]["avatar_url"]

        try:
            download_avatar(avatar_url)
        except Exception as e:
            MessageBox(self, "Error", e)
            return False

        self.check["download_avatar"] = True
        return True

    def download_emotes(self):

        max_thread = 10
        download_list = [self.emotes_urls[i:i + max_thread] for i in range(0, len(self.emotes_urls), max_thread)]

        for chunk in download_list:
            try:
                [_ for _ in ThreadPool(len(chunk)).imap_unordered(func=download_emote, iterable=chunk)]
            except Exception as e:
                MessageBox(self, "Error", e)
                return False

        self.check["download_emotes"] = True
        return True

    def save_config(self):
        self.data["saved"] = True

        with open("./config.json", "w", encoding="utf-8") as file:
            json.dump(self.data, file)

        MessageBox(self, "Success", "Application setup complete, please restart the app.")
        self.done = True

    def update_progress(self, text="Loading"):
        dots = (".", "..", "...")
        i = 0
        try:
            while self.download_thread.is_alive():
                self.prog_var.set(text + dots[i % 3])
                i += 1
                sleep(1)
            else:
                self.prog_var.set("Please restart the application.")
        except:
            self.prog_var.set("Please restart the application.")

    def monitor_thread(self):
        if self.download_thread.is_alive():
            self.after(100, lambda: self.monitor_thread)
        else:
            if self.done:
                self.prog_var.set("Please restart the application.")
            else:
                self.prog_frame.pack_forget()
                self.input_frame.pack(fill="both", expand=True)

    def run_app(self):
        self.input_frame.pack_forget()
        self.prog_frame.pack(fill="both", expand=True)
        # Run downloader logic
        self.download_thread.start()
        # Monitor downloader thread
        self.after(1000, lambda: self.monitor_thread)

    def _run_app(self):
        # set the token
        if self.entry.get() == "":
            MessageBox(self, "Error", "Please enter your auth token")
            return
        progress_thread = Thread(target=self.update_progress, args=("Getting ready, this might take some time",))
        progress_thread.start()
        # check if new token entered
        if self.data["token"]:
            if self.data["token"] != self.token.get():
                # Reset check results for new token
                self.data["token"] = None
                for key in self.check:
                    self.check[key] = False

        # Set token for global use
        self.token = self.entry.get()

        # Fetch user info
        if not self.check["user"]:
            done = self.get_user()
            if not done:
                return
        # Fetch servers
        if not self.check["servers"]:
            done = self.get_servers()
            if not done:
                return
        # Fetch channels
        if not self.check["channels"]:
            done = self.get_channels()
            if not done:
                return
        # Fetch channels
        if not self.check["emotes"]:
            done = self.get_emotes()
            if not done:
                return

        # Download user avatar
        if not self.check["download_avatar"]:
            done = self.download_avatar()
            if not done:
                return

        # Download servers emotes
        if not self.check["download_emotes"]:
            done = self.download_emotes()
            if not done:
                return

        # Save everything
        self.save_config()


class MyApp(CTk):
    def __init__(self, data):
        # -- Theme and window settings --
        super().__init__()
        self.title("Discord Emotes")
        self.resizable(False, False)
        self.geometry("500x550")
        # App Vars
        self.token = data['token']
        self.user = data["user"]
        self.servers = data["servers"]
        self.emotes_widgets = []
        self.images = dict()
        self.curr_server = None
        self.curr_channel = None
        self.last_sent = 0
        self.send_result = None
        # ---- App Widgets ----
        # -- User widgets --
        # User info labels
        self.user_frame = CTkFrame(self)
        self.user_frame.place(x=0, y=0, relwidth=1, relheight=0.15)
        self.avatar = load_avatar()
        self.l_avatar = CTkLabel(self.user_frame, image=self.avatar)
        self.l_avatar.place(relx=0.01, rely=0.5, relheight=0.8, relwidth=0.15, anchor="w")
        self.l_username = CTkLabel(self.user_frame, text=self.user["username"], text_font=Font(size=26), anchor="w")
        self.l_username.place(x=80, y=30, anchor="w")
        self.l_user_tag = CTkLabel(self.user_frame, text=self.user["user_tag"], text_font=Font(size=14),
                                   text_color="grey", anchor="w")
        self.l_user_tag.place(x=80, y=62, anchor="w")
        # Emote server Label
        self.l_emote_server = CTkLabel(self.user_frame, text="Emotes Server", text_font=Font(size=18))
        self.l_emote_server.place(x=300, y=22, anchor="w")
        # Filter servers that have no custom emotes
        emote_server_options = [server for server in self.servers if len(self.servers[server]["emotes"]) >= 1]
        # Option menu for selecting where to get emotes from
        self.op_emote_server = CTkOptionMenu(self.user_frame, values=emote_server_options, text_font=Font(size=12),
                                             command=self.emote_server_option)
        self.op_emote_server.place(x=300, y=58, relwidth=0.32, anchor="w")
        # -- Emotes widgets --
        self.em_frame = CTkFrame(self, fg_color="grey10", border_color="grey10")
        self.em_frame.place(x=0, y=90, relwidth=1, relheight=0.74)
        self.em_canvas = CTkCanvas(self.em_frame, bg="grey10")
        self.scrollbar = CTkScrollbar(self.em_frame, command=self.em_canvas.yview)
        self.em_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.em_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.update_idletasks()
        canvas_width = self.em_canvas.winfo_width()
        self.cv_frame = CTkFrame(self.em_canvas, fg_color="grey10", border_color="grey10")
        self.em_canvas.create_window((0, 0), window=self.cv_frame, anchor='nw',
                                     width=canvas_width - (canvas_width * 0.18))
        self.cv_frame.bind("<Configure>", lambda e: self.em_canvas.configure(scrollregion=self.em_canvas.bbox("all")))
        # -- Target server widgets --
        self.l_target_server = CTkLabel(self, text="Target Server", text_font=Font(size=16))
        self.l_target_server.place(x=0, y=525, anchor="w")
        # List of servers that can receive the emotes
        target_server_options = list(self.servers.keys())
        self.curr_server = target_server_options[0]
        # Target server selector
        self.op_target_server = CTkOptionMenu(self, values=target_server_options, text_font=Font(size=12),
                                              command=self.target_server_option)
        self.op_target_server.place(x=150, y=525, relwidth=0.32, anchor="w")
        # List of channels for current server
        server_channels_options = [channel["name"] for channel in self.servers[self.curr_server]["channels"]]
        # Target channel selector
        self.op_target_channel = CTkOptionMenu(self, text_font=Font(size=12), values=server_channels_options,
                                               command=self.target_channel_option)
        self.op_target_channel.place(x=330, y=525, relwidth=0.32, anchor="w")
        self.curr_channel = self.servers[self.curr_server]["channels"][0]["id"]
        # -- Preload all images --
        images_thread = Thread(target=self.load_images)
        images_thread.start()

    def emote_server_option(self, server):
        # Remove previous widgets
        for button in self.emotes_widgets:
            button.destroy()
        self.emotes_widgets.clear()
        # Display selected server widgets
        self.get_emotes(server)

    def target_server_option(self, server):
        self.curr_server = server
        server_channels_options = [channel["name"] for channel in self.servers[server]["channels"]]
        self.curr_channel = self.servers[server]["channels"][0]["id"]
        self.op_target_channel.configure(values=server_channels_options)
        self.op_target_channel.set(server_channels_options[0])

    def target_channel_option(self, channel):
        for c in self.servers[self.curr_server]["channels"]:
            if c["name"] == channel:
                self.curr_channel = c["id"]

    def load_images(self):
        emotes_path = "./data/emotes/"
        for file_name in os.listdir(emotes_path):
            file_path = os.path.join(emotes_path, file_name)
            if os.path.isfile(file_path) and file_path.endswith(".png"):
                image = PhotoImage(file=f"./data/emotes/{file_name}")
                # Save PhotoImages using the image file name without the (.png)
                self.images[file_name[:-4]] = image
        # Load all emotes for curr server
        self.get_emotes(self.curr_server)

    def get_emotes(self, server):
        curr_row = 0
        curr_col = 0
        curr_height = 0
        emote_per_row = 3
        self.update_idletasks()
        frame_width = self.cv_frame.winfo_width()
        emote_list = sorted(self.servers[server]["emotes"], key=lambda d: not d['is_gif'])
        for emote in emote_list:
            color = "grey10"
            btn = CTkButton(self.cv_frame, image=self.images[emote["file_name"][:-4]], text=emote["name"],
                            fg_color=color, compound="top", width=(frame_width // 3) - 20,
                            command=functools.partial(self.send_emote, emote["url"]))
            btn.grid(row=curr_row, column=curr_col, pady=10, padx=10, sticky="nesw")
            curr_col += 1
            self.emotes_widgets.append(btn)
            self.update_idletasks()

            if curr_height < btn.winfo_height():
                curr_height = btn.winfo_height() + 20
            if curr_col >= emote_per_row:
                curr_row += 1
                curr_col = 0

        # Reposition first button with correct padding
        self.emotes_widgets[0].grid(row=0, column=0, padx=10, pady=10, sticky="nesw")

        self.cv_frame.configure(height=curr_height * len(emote_list))

    def monitor_sender_thread(self, thread):
        if thread.is_alive():
            self.after(500, self.monitor_sender_thread, thread)
        else:
            if self.send_result == 403:
                MessageBox(self, "Error", "You don't have permission for this Text Channel")
            elif self.send_result != 200:
                MessageBox(self, "Error", "Failed to send emote")

            self.send_result = None

    def send_emote(self, url):
        # Delay timer to stop request spamming
        if time.time() > self.last_sent + 2:
            # Send request on a new thread to avoid application freezing
            thread = Thread(target=self._send_message, args=(url,))
            thread.start()
            self.after(100, self.monitor_sender_thread, thread)

    def _send_message(self, message):
        HEADERS = {
            "authorization": self.token,
            "content-type": "application/json"
        }

        MESSAGE = {"content": message}

        URL = f"https://discord.com/api/channels/{self.curr_channel}/messages"

        try:
            response = requests.post(url=URL, headers=HEADERS, json=MESSAGE)
            self.send_result = response.status_code
        except:
            self.send_result = 0
