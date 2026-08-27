import tkinter as tk
import re
from datetime import datetime
from .config import ANGEL_ICON, ICON_DIR
from PIL import Image, ImageTk

class AngelChat(tk.Toplevel):

    def __init__(self, parent, angel):
        super().__init__(parent)
        self.iconbitmap(str(ANGEL_ICON))
        self.title("FTMS FleetPro ANGEL")
        self.angel = angel
        img = Image.open(ICON_DIR/"angel.png")
        img = img.resize((40,40), Image.LANCZOS)
        self.angel_photo = ImageTk.PhotoImage(img)
        self.title("👼 FTMS FleetPro ANGEL")
        self.geometry("400x375")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # ===== Header =====
        header = tk.Frame(self, bg="#2E86C1", height=30)
        header.pack(fill="x")

        header_label = tk.Label(
            header, image= self.angel_photo,
            text="FTMS FleetPro ANGEL", compound="left",
            bg="#2E86C1",
            fg="white",
            font=("Calibri", 14, "bold")
        )
        header_label.pack(side="left", padx=10, pady=6)

        # ===== Chat Area =====
        self.chat = tk.Text(
            self, height = 10,
            wrap="word",
            state="normal",
            font=("Segoe UI Emoji", 11)
        )
         
        
        self.chat.pack(fill="x", padx=10, pady=10)        
        self.chat.insert(
            "end",
            "👼 ANGEL:\n"
            "Hello Sir!\n\n"
            f"Current Module : {angel.current_module}\n\n"
        )
        self.chat.config(state="disabled")
        
        #========== INPUT AREA ==================
        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=10)
        tk.Label(bottom, text="👼 Ask ANGEL", font = ("Calibri", 11,"bold")).pack(anchor="w")
        self.entry = tk.Entry(bottom, font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus_set()
        tk.Button(bottom, text="📤SEND", width=8,
        command = self.send_message).pack(side = "left", padx=5)
        self.entry.bind_all("<Return>", self.send_message)

    def is_greeting(self, text):
        """Check if the input is a greeting message."""
        text = re.sub(r"\s+", " ", text.lower()).strip()
        
        # Time-based greetings
        time_greetings = ["good morning", "good afternoon", "good evening", "good night", 
                         "morning", "afternoon", "evening", "night", "good after noon"]
        
        # Basic greetings
        basic_greetings = ["hi", "hey", "hello", "hai", "hii", "helo", "hellow"]
        
        # Farewells
        farewells = ["bye", "goodbye", "farewell", "see you", "take care"]
        
        # Special queries that greeting_reply handles
        special = ["how are you", "who are you", "who created you", "who developed you", 
                  "your mission", "your duty", "your capabilities", "what can you do",
                  "your responsibility", "your strength", "your name"]
        
        for greeting in time_greetings + basic_greetings + farewells + special:
            if greeting in text:
                return True
        return False
        
    def update_module(self, module_name):
        self.angel.current_module = module_name
         
    def clear_placeholder(self, event):
        if self.entry.get() == "Type your questions or instruction here...":
            self.entry.delete(0, "end")

    def send_message(self, event = None):
        question = self.entry.get().strip()
        if question == "":
            return
        self.add_message("You", question)
        
        # Route to greeting_reply if it's a greeting, otherwise use reply
        if self.is_greeting(question):
            reply = self.angel.greeting_reply(question)
        else:
            reply = self.angel.reply(question)
        
        self.add_message("👼ANGEL", reply)
        self.entry.delete(0, "end")
        self.entry.focus_set()

    def add_message(self, speaker, message):
        current_time = datetime.now().strftime("%I:%M %p")        
        self.chat.config(state="normal")
        self.chat.insert("end", f"{speaker}:{current_time}\n {message}\n\n")
        self.chat.config(state="disabled")
        self.chat.see("end")
