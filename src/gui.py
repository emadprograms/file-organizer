import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import sys
import os
import queue
from pathlib import Path

# Add project root to sys.path to allow 'src' module imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
        
        self.telemetry_queue = queue.Queue()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="Tab 1: Categorizer")
        self.notebook.add(self.tab2, text="Tab 2: Telemetry")

        self.setup_tab1()
        self.setup_tab2()

        # Redirect standard output
        self.logger = PrintLogger(self.log_area)
        self.original_stdout = sys.stdout
        sys.stdout = self.logger

        self.poll_telemetry()

    def setup_tab1(self):
        root = self.tab1
        tk.Label(root, text="PDF File(s):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.pdf_entry = tk.Entry(root, width=50)
        self.pdf_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.browse_pdf).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(root, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.output_entry = tk.Entry(root, width=50)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        self.run_button = tk.Button(root, text="Run Categorizer", bg="green", fg="white", font=("Arial", 12, "bold"), command=self.run_pipeline)
        self.run_button.grid(row=2, column=0, columnspan=3, pady=15)

        tk.Label(root, text="Logs:").grid(row=3, column=0, sticky="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=18)
        self.log_area.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

    def setup_tab2(self):
        root = self.tab2
        columns = ("Key ID", "Total Requests", "Current RPM", "Current TPM", "Strikes", "Status")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

    def browse_pdf(self):
        filenames = filedialog.askopenfilenames(title="Select PDFs", filetypes=[("PDF Files", "*.pdf")])
        if filenames:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, ";".join(filenames))
            
            first_file_dir = os.path.dirname(filenames[0])
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, first_file_dir)

    def browse_output(self):
        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, dirname)

    def run_pipeline(self):
        pdf_path = self.pdf_entry.get().strip()
        output_dir = self.output_entry.get().strip()

        if not pdf_path:
            messagebox.showerror("Error", "Please select valid input PDF file(s).")
            return
            
        if not output_dir:
            output_dir = os.path.dirname(pdf_path.split(";")[0])
            self.output_entry.insert(0, output_dir)

        self.run_button.config(state=tk.DISABLED, text="Running...")
        self.log_area.delete(1.0, tk.END)

        thread = threading.Thread(target=self._execute, args=(pdf_path, output_dir), daemon=True)
        thread.start()

    def _execute(self, pdf_paths_str, output_dir):
        import time
        try:
            from dotenv import load_dotenv
            from src.pipeline import Pipeline
            from src.organizer import FileOrganizer

            load_dotenv()
            
            api_keys_str = os.getenv("GEMINI_API_KEYS")
            api_keys = [k.strip() for k in api_keys_str.split(",")] if api_keys_str else None

            pipeline = Pipeline(api_keys=api_keys, telemetry_queue=self.telemetry_queue)
            
            pdf_paths = [p.strip() for p in pdf_paths_str.split(";") if p.strip()]
            
            for pdf_path in pdf_paths:
                try:
                    if not os.path.exists(pdf_path):
                        print(f"File not found: {pdf_path}, skipping.")
                        continue

                    print(f"\n{'='*50}")
                    print(f"Loading PDF from: {pdf_path}")
                    documents = pipeline.process_pdf(pdf_path)
                    print(f"Identified {len(documents)} documents.")

                    organizer = FileOrganizer()
                    summary = organizer.organize(documents, pdf_path, Path(output_dir))

                    if summary:
                        house_number = organizer._resolve_house_number(pdf_path)
                        num_residents = len(organizer._build_resident_order(documents))
                        out_dir = Path(output_dir) / house_number
                        
                        print(f"\n{'='*50}")
                        print(f"  House: {house_number}")
                        print(f"  Residents: {num_residents}")
                        print(f"  PDFs generated: {len(summary)}")
                        print(f"  Output: {out_dir}")
                        print(f"{'='*50}")
                except Exception as e:
                    error_msg = str(e).lower()
                    print(f"\nFailed to process {pdf_path}: {e}")
                    print("Progress has been saved to cache.")
                    if "rate limit" in error_msg or "429" in error_msg or "too many requests" in error_msg or "retryerror" in error_msg or "aborted" in error_msg:
                        print("Pausing for 3 minutes before proceeding to the next file...")
                        time.sleep(180)
                    else:
                        print("Pausing for 3 minutes before proceeding to the next file...")
                        time.sleep(180)
                    continue

            print("\nProcessing Complete!")
            messagebox.showinfo("Success", "File categorization complete!")
            
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.root.after(0, lambda: self.run_button.config(state=tk.NORMAL, text="Run Categorizer"))

    def poll_telemetry(self):
        try:
            while True:
                state = self.telemetry_queue.get_nowait()
                for item in self.tree.get_children():
                    self.tree.delete(item)
                for key_data in state.get("keys", []):
                    self.tree.insert("", tk.END, values=(
                        key_data["id"],
                        key_data["total_reqs"],
                        key_data["rpm"],
                        key_data["tpm"],
                        key_data["strikes"],
                        key_data["status"]
                    ))
        except queue.Empty:
            pass
        finally:
            self.root.after(500, self.poll_telemetry)

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
