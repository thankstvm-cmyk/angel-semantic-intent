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
            "Please type Hi to begin?\n\n"
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
        """CRITICAL: Check if input is a greeting - EXACT DETECTION."""
        text = re.sub(r"\s+", " ", text.lower()).strip()
        
        # Time-based greetings - EXACT MATCH
        if "good morning" in text or text == "morning":
            return True
        if "good afternoon" in text or "good after noon" in text or text == "afternoon":
            return True
        if "good evening" in text or text == "evening":
            return True
        if "good night" in text or text == "night":
            return True
        
        # Basic greetings - EXACT MATCH
        if text in ("hi", "hey", "hello", "hai", "hii", "helo", "hellow"):
            return True
        # With punctuation
        if any(term in text for term in ("hi.", "hi!", "hey.", "hello.", "hai.", "hellow.")):
            return True
        if any(term in text for term in ("hi ", " hi", "hey ", " hey", "hello ", " hello", "hai ", " hai")):
            return True
        
        # Farewells
        if any(term in text for term in ("bye", "goodbye", "farewell", "see you", "take care")):
            return True
        
        # Special knowledge queries
        special = ["how are you", "who are you", "who created you", "who developed you", 
                  "your mission", "your duty", "your capabilities", "what can you do",
                  "your responsibility", "your strength", "your name"]
        for term in special:
            if term in text:
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
        
        # CRITICAL: Check greeting FIRST - ALWAYS
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
