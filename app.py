
import tkinter as tk
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import json
import threading
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ParserApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.title("Rwandan Law Deterministic Parser")
        self.geometry("1100x700")

        # UI Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkLabel(self, text="RLRC 2022 Deterministic Parser", font=("Inter", 24, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=20)

        # Sidebar / Upload
        self.upload_frame = ctk.CTkFrame(self, width=200)
        self.upload_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        self.drop_label = ctk.CTkLabel(self.upload_frame, text="Drag & Drop PDF Here", width=180, height=100, fg_color="gray20", corner_radius=10)
        self.drop_label.pack(pady=20, padx=10)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

        # Preview Area
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("JSON Preview")
        self.tabview.add("CSV Preview")

        self.json_text = ctk.CTkTextbox(self.tabview.tab("JSON Preview"), font=("Consolas", 12))
        self.json_text.pack(expand=True, fill="both")

        # Progress Bar
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.progress.set(0)

        # Footer
        self.footer = ctk.CTkLabel(self, text="Status: Ready | Hybrid Python/Zig Engine", font=("Inter", 10))
        self.footer.grid(row=3, column=0, columnspan=2, pady=10)

    def handle_drop(self, event):
        file_path = event.data.strip('{}')
        self.start_parsing(file_path)

    def start_parsing(self, path):
        self.progress.set(0)
        threading.Thread(target=self.fake_parse_process).start()

    def fake_parse_process(self):
        for i in range(1, 101):
            time.sleep(0.02)
            self.progress.set(i/100)
        self.json_text.insert("0.0", json.dumps({"status": "success", "engine": "Zig-Core-v1", "nodes": 8}, indent=4))

if __name__ == "__main__":
    app = ParserApp()
    app.mainloop()
