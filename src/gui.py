import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import sys
import os
from pathlib import Path

# Redirect stdout to Tkinter text widget
class PrintLogger:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, text):
        self.textbox.insert(tk.END, text)
        self.textbox.see(tk.END)
        self.textbox.update_idletasks()

    def flush(self):
        pass

class FileCategorizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Categorizer")
        self.root.geometry("600x500")

        # PDF Path Selection
        tk.Label(root, text="PDF File:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.pdf_entry = tk.Entry(root, width=50)
        self.pdf_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.browse_pdf).grid(row=0, column=2, padx=5, pady=5)

        # Output Path Selection
        tk.Label(root, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.output_entry = tk.Entry(root, width=50)
        self.output_entry.insert(0, "./output")
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        # Run Button
        self.run_button = tk.Button(root, text="Run Categorizer", bg="green", fg="white", font=("Arial", 12, "bold"), command=self.run_pipeline)
        self.run_button.grid(row=2, column=0, columnspan=3, pady=15)

        # Log Output
        tk.Label(root, text="Logs:").grid(row=3, column=0, sticky="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=18)
        self.log_area.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

        # Redirect standard output
        self.logger = PrintLogger(self.log_area)
        self.original_stdout = sys.stdout
        sys.stdout = self.logger

    def browse_pdf(self):
        filename = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, filename)

    def browse_output(self):
        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, dirname)

    def run_pipeline(self):
        pdf_path = self.pdf_entry.get().strip()
        output_dir = self.output_entry.get().strip()

        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid input PDF file.")
            return

        self.run_button.config(state=tk.DISABLED, text="Running...")
        self.log_area.delete(1.0, tk.END)

        # Run in a separate thread to avoid freezing GUI
        thread = threading.Thread(target=self._execute, args=(pdf_path, output_dir), daemon=True)
        thread.start()

    def _execute(self, pdf_path, output_dir):
        try:
            from dotenv import load_dotenv
            from src.pipeline import Pipeline
            from src.organizer import FileOrganizer

            load_dotenv()
            
            api_keys_str = os.getenv("GEMINI_API_KEYS")
            api_keys = [k.strip() for k in api_keys_str.split(",")] if api_keys_str else None

            pipeline = Pipeline(api_keys=api_keys)
            
            print(f"Loading PDF from: {pdf_path}")
            documents = pipeline.process_pdf(pdf_path)
            print(f"Identified {len(documents)} documents.")

            organizer = FileOrganizer()
            summary = organizer.organize(documents, pdf_path, Path(output_dir))

            if summary:
                house_number = organizer._resolve_house_number(documents)
                num_residents = len(organizer._build_resident_order(documents))
                out_dir = Path(output_dir) / house_number
                
                print(f"\n{'='*50}")
                print(f"  House: {house_number}")
                print(f"  Residents: {num_residents}")
                print(f"  PDFs generated: {len(summary)}")
                print(f"  Output: {out_dir}")
                print(f"{'='*50}")
            print("\nProcessing Complete!")
            messagebox.showinfo("Success", "File categorization complete!")
            
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.root.after(0, lambda: self.run_button.config(state=tk.NORMAL, text="Run Categorizer"))

    def on_closing(self):
        sys.stdout = self.original_stdout
        self.root.destroy()

def launch_gui():
    root = tk.Tk()
    app = FileCategorizerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
