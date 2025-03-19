import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter, Transformation
import os

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    messagebox.showerror("Error", "Please install tkinterdnd2: pip install tkinterdnd2")
    exit()

class PDFMergerApp(TkinterDnd2.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger Pro")
        self.geometry("800x600")
        self.file_list = []
        self.watermark = None
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # File List with Drag & Drop
        list_frame = ttk.LabelFrame(main_frame, text="PDF Files (Drag to Reorder)")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.listbox = tk.Listbox(list_frame, activestyle='none')
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.add_files)

        # Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)

        btn_add = ttk.Button(controls_frame, text="Add Files", command=self.browse_files)
        btn_add.pack(side=tk.LEFT, padx=2)
        btn_remove = ttk.Button(controls_frame, text="Remove Selected", command=self.remove_file)
        btn_remove.pack(side=tk.LEFT, padx=2)
        btn_up = ttk.Button(controls_frame, text="Move Up", command=lambda: self.move_file(-1))
        btn_up.pack(side=tk.LEFT, padx=2)
        btn_down = ttk.Button(controls_frame, text="Move Down", command=lambda: self.move_file(1))
        btn_down.pack(side=tk.LEFT, padx=2)

        # Advanced Options
        options_frame = ttk.LabelFrame(main_frame, text="Advanced Options")
        options_frame.pack(fill=tk.X, pady=5)

        # Watermark
        ttk.Label(options_frame, text="Watermark PDF:").grid(row=0, column=0, sticky=tk.W)
        self.watermark_entry = ttk.Entry(options_frame, width=50)
        self.watermark_entry.grid(row=0, column=1, padx=5)
        ttk.Button(options_frame, text="Browse", command=self.browse_watermark).grid(row=0, column=2)

        # Password Protection
        ttk.Label(options_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(options_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, sticky=tk.W)

        # Compression
        self.compression_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Compress Output", variable=self.compression_var).grid(row=2, column=0, columnspan=3, sticky=tk.W)

        # Merge Button
        btn_merge = ttk.Button(main_frame, text="Merge PDFs", command=self.merge_pdfs)
        btn_merge.pack(pady=10)

    def browse_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        self.add_files(files)

    def add_files(self, event=None):
        files = event.data.split() if hasattr(event, 'data') else event
        for f in files:
            if f.endswith('.pdf') and f not in self.file_list:
                self.file_list.append(f.strip('{').strip('}'))
                self.listbox.insert(tk.END, os.path.basename(f))

    def remove_file(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            del self.file_list[index]
            self.listbox.delete(index)

    def move_file(self, direction):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            new_index = index + direction
            if 0 <= new_index < len(self.file_list):
                self.file_list.insert(new_index, self.file_list.pop(index))
                self.listbox.insert(new_index, self.listbox.get(index))
                self.listbox.delete(index + (1 if direction < 0 else 0))
                self.listbox.select_set(new_index)

    def browse_watermark(self):
        file = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file:
            self.watermark_entry.delete(0, tk.END)
            self.watermark_entry.insert(0, file)
            self.watermark = file

    def apply_watermark(self, writer, page):
        if self.watermark:
            watermark_reader = PdfReader(self.watermark)
            watermark_page = watermark_reader.pages[0]
            
            # Scale watermark to fit page
            transformation = Transformation().scale(
                page.mediabox.width / watermark_page.mediabox.width,
                page.mediabox.height / watermark_page.mediabox.height
            )
            watermark_page.add_transformation(transformation)
            
            page.merge_page(watermark_page)
        return page

    def merge_pdfs(self):
        if not self.file_list:
            messagebox.showerror("Error", "No PDF files selected!")
            return

        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not output_file:
            return

        writer = PdfWriter()
        try:
            for pdf_path in self.file_list:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    # Apply watermark to each page
                    processed_page = self.apply_watermark(writer, page)
                    writer.add_page(processed_page)

            # Set encryption if password provided
            password = self.password_entry.get()
            if password:
                writer.encrypt(password)

            # Set compression
            if self.compression_var.get():
                for page in writer.pages:
                    page.compress_content_streams()

            with open(output_file, "wb") as f:
                writer.write(f)

            messagebox.showinfo("Success", "PDFs merged successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

if __name__ == "__main__":
    app = PDFMergerApp()
    app.mainloop()
