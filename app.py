
import tkinter as tk
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
import json
import threading
import os
import ctypes
import fitz 

try:
    lib_path = './parser_core.dll' if os.name == 'nt' else './libparser_core.so'
    lib = ctypes.CDLL(lib_path)
    lib.build_ast.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
    lib.build_ast.restype = ctypes.c_char_p # Now returns a JSON string pointer
except:
    lib = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ParserApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkinterDnD_Version = TkinterDnD._require(self)
        self.title("Rwandan Law Deterministic Parser")
        self.geometry("1100x750")
        self.current_json = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.select_btn = ctk.CTkButton(self.sidebar, text="Browse Local File", command=self.browse_file)
        self.select_btn.pack(pady=20, padx=20)

        self.download_btn = ctk.CTkButton(self.sidebar, text="Download JSON", state="disabled", command=self.save_json)
        self.download_btn.pack(pady=10, padx=20)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("AST Output")
        
        self.json_text = ctk.CTkTextbox(self.tabview.tab("AST Output"), font=("Consolas", 12))
        self.json_text.pack(expand=True, fill="both")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.progress.set(0)

        self.footer = ctk.CTkLabel(self, text="Status: Ready", font=("Inter", 10))
        self.footer.grid(row=3, column=0, columnspan=2, pady=10)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path: self.start_parsing(path)

    def save_json(self):
        if self.current_json:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if path:
                with open(path, 'w') as f:
                    json.dump(self.current_json, f, indent=4)

    def start_parsing(self, path):
        self.footer.configure(text=f"Status: Processing...")
        threading.Thread(target=self.process_pdf, args=(path,)).start()

    def process_pdf(self, path):
        try:
            doc = fitz.open(path)
            text = " ".join([p.get_text() for p in doc])
            encoded = text.encode('utf-8')
            
            if lib:
                res_ptr = lib.build_ast(encoded, len(encoded))
                res_str = ctypes.string_at(res_ptr).decode('utf-8')
                self.current_json = json.loads(res_str)
            else:
                self.current_json = {"error": "Engine not loaded"}

            self.json_text.delete("0.0", "end")
            self.json_text.insert("0.0", json.dumps(self.current_json, indent=4))
            self.download_btn.configure(state="normal")
            self.footer.configure(text="Status: Success")
            self.progress.set(1.0)
        except Exception as e:
            self.footer.configure(text=f"Error: {str(e)}")

if __name__ == '__main__':
    app = ParserApp()
    app.mainloop()
