from tkinter.font import Font

from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkToplevel, StringVar


class MessageBox:
    def __init__(self, master, title="Message", msg="This is a message"):
        self.master = master
        self.var = StringVar()
        self.var.set(msg)

        self.WIDTH = 300
        self.HEIGHT = 100

        self.top = CTkToplevel(master=master)
        self.top.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.top.title(title)
        self.top.lift()
        self.top.focus_force()
        self.top.grab_set()
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.top.after(10, self.create_widgets)

        master.wait_window(self.top)

    def create_widgets(self):
        # -- Widgets --
        # Widgets Container
        frame = CTkFrame(master=self.top, width=220, height=200)
        # Message label
        label = CTkLabel(frame, textvariable=self.var,
                         anchor="center",
                         wraplength=300,
                         text_font=Font(size=10))
        label.pack(ipadx=10, ipady=10, fill='both', expand=True)
        # Ok Button
        button = CTkButton(frame, text="Ok",
                           width=40, height=30,
                           command=self.on_closing)
        button.pack(expand=True, pady=(0, 10))
        # Adjust window height according to the text length
        self.top.update()
        self.HEIGHT = label.winfo_reqheight() + button.winfo_reqheight() + 30  # extra 30 for the padding
        frame.configure(height=self.HEIGHT)
        frame.pack(fill='both', expand=True)
        # Get Root position
        x = self.master.winfo_x() + 100
        y = self.master.winfo_y() + 50
        # Set window size and position it inside the root window
        self.top.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self.top.minsize(self.WIDTH, self.HEIGHT)
        self.top.maxsize(self.WIDTH, self.HEIGHT)
        # disable root
        self.master.attributes('-disabled', 'true')

    def on_closing(self):
        # Enable root and close Pop up
        self.master.attributes('-disabled', 'false')
        self.top.destroy()
