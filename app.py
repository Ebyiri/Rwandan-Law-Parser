
import tkinter as tk
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import json
import threading
import time
import sys
import os
import ctypes
import fitz

# Load Zig Core
try:
    lib = ctypes.CDLL('./libparser_core.so')
    lib.build_ast.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
    lib.build_ast.restype = ctypes.c_int32
except:
    lib = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ParserApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkinterDnD_Version = TkinterDnD._require(self)
        self.title("Rwandan Law Deterministic Parser")
        self.geometry("1100x700")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkLabel(self, text="RLRC 2022 Deterministic Parser", font=("Inter", 24, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=20)

        self.upload_frame = ctk.CTkFrame(self, width=200)
        self.upload_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.drop_label = ctk.CTkLabel(self.upload_frame, text="Drag & Drop PDF Here", width=180, height=100, fg_color="gray20", corner_radius=10)
        self.drop_label.pack(pady=20, padx=10)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("JSON Preview")
        
        self.json_text = ctk.CTkTextbox(self.tabview.tab("JSON Preview"), font=("Consolas", 12))
        self.json_text.pack(expand=True, fill="both")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.progress.set(0)

        self.footer = ctk.CTkLabel(self, text="Status: Ready", font=("Inter", 10))
        self.footer.grid(row=3, column=0, columnspan=2, pady=10)

    def handle_drop(self, event):
        file_path = event.data.strip('{}')
        self.start_parsing(file_path)

    def start_parsing(self, path):
        self.progress.set(0)
        self.footer.configure(text=f"Status: Parsing {os.path.basename(path)}...")
        threading.Thread(target=self.process_pdf, args=(path,)).start()

    def process_pdf(self, path):
        try:
            doc = fitz.open(path)
            text_content = "".join([page.get_text() for page in doc])
            encoded_text = text_content.encode('utf-8')
            
            self.progress.set(0.5)
            
            if lib:
                found_nodes = lib.build_ast(encoded_text, len(encoded_text))
            else:
                found_nodes = -1

            self.progress.set(1.0)
            result = {
                "status": "success",
                "file": os.path.basename(path),
                "engine": "Zig-Core-v1",
                "detected_nodes": found_nodes
            }
            
            self.json_text.delete("0.0", "end")
            self.json_text.insert("0.0", json.dumps(result, indent=4))
            self.footer.configure(text="Status: Success")
        except Exception as e:
            self.footer.configure(text=f"Status: Error - {str(e)}")

if __name__ == '__main__':
    app = ParserApp()
    app.mainloop()
