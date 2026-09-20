"""Tkinter Desktop UI with dual capabilities: Reconstruction and Tree Generation."""

import io
import os
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Ensure the package root is in sys.path when executed directly
repo_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ascii_tree_reorg.core.auditor import StructureAuditor
from ascii_tree_reorg.core.generator import DirectoryTreeGenerator, GeneratorOptions
from ascii_tree_reorg.core.parser import AsciiTreeParser
from ascii_tree_reorg.engine.reorganizer import DirectoryReorganizer


class TextRedirector(io.StringIO):
    """Redirects stdout/stderr streams to a Tkinter Text widget safely."""

    def __init__(self, widget: tk.Text):
        super().__init__()
        self.widget = widget

    def write(self, s: str):
        self.widget.configure(state="normal")
        self.widget.insert(tk.END, s)
        self.widget.see(tk.END)
        self.widget.configure(state="disabled")

    def flush(self):
        pass


class AsciiTreeReorgApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASCII Tree Reorganizer & Generator v0.2.0")
        self.geometry("980x820")
        self.minsize(800, 640)

        # Apply clean ttk theme if available
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self._build_notebook()

    def _build_notebook(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Reconstruct Directory Structure
        reconstruct_frame = ttk.Frame(notebook, padding=10)
        notebook.add(reconstruct_frame, text=" 🔨 Reconstruct from Tree ")
        self._init_reconstruct_tab(reconstruct_frame)

        # Tab 2: Generate Tree from Folder
        generate_frame = ttk.Frame(notebook, padding=10)
        notebook.add(generate_frame, text=" 📝 Generate Tree from Folder ")
        self._init_generate_tab(generate_frame)

    # -------------------------------------------------------------------------
    # TAB 1: RECONSTRUCTION LOGIC
    # -------------------------------------------------------------------------
    def _init_reconstruct_tab(self, parent: ttk.Frame):
        # Paths frame
        paths_frame = ttk.LabelFrame(parent, text="Directories", padding=10)
        paths_frame.pack(fill=tk.X, pady=5)

        ttk.Label(paths_frame, text="Source Folder (Flat Files):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.src_entry = ttk.Entry(paths_frame, width=65)
        self.src_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        default_src = (repo_root / "data" / "inputs" / "raw_archive").resolve()
        self.src_entry.insert(0, str(default_src))
        ttk.Button(paths_frame, text="Browse...", command=self._browse_src).grid(row=0, column=2, padx=2)

        ttk.Label(paths_frame, text="Target Output Root:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.dest_entry = ttk.Entry(paths_frame, width=65)
        self.dest_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        default_dst = (repo_root / "data" / "outputs").resolve()
        self.dest_entry.insert(0, str(default_dst))
        ttk.Button(paths_frame, text="Browse...", command=self._browse_dest).grid(row=1, column=2, padx=2)

        paths_frame.columnconfigure(1, weight=1)

        # Options frame
        opts_frame = ttk.LabelFrame(parent, text="Reconstruction Settings", padding=10)
        opts_frame.pack(fill=tk.X, pady=5)

        self.move_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=True)
        self.clean_relocated_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(opts_frame, text="Move files (delete source)", variable=self.move_var).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Checkbutton(opts_frame, text="Overwrite existing files", variable=self.overwrite_var).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Checkbutton(opts_frame, text="Clean relocated old files", variable=self.clean_relocated_var).pack(
            side=tk.LEFT, padx=6
        )

        ttk.Label(opts_frame, text="Indent Width:").pack(side=tk.LEFT, padx=(15, 2))
        self.indent_var = tk.IntVar(value=4)
        ttk.Spinbox(opts_frame, from_=2, to=8, textvariable=self.indent_var, width=4).pack(side=tk.LEFT)

        # ASCII Tree Text Editor
        tree_frame = ttk.LabelFrame(parent, text="ASCII Tree Specification", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_toolbar = ttk.Frame(tree_frame)
        btn_toolbar.pack(fill=tk.X, pady=2)
        ttk.Button(btn_toolbar, text="Load Tree File...", command=self._load_tree_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_toolbar, text="Clear", command=lambda: self.tree_text.delete("1.0", tk.END)).pack(
            side=tk.LEFT, padx=2
        )

        self.tree_text = tk.Text(tree_frame, height=10, wrap=tk.NONE, font=("Consolas", 10))
        self.tree_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree_text.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_text.configure(yscrollcommand=tree_scroll.set)

        default_tree = (
            "my_project/\n"
            "├── configs/\n"
            "│   ├── config.yaml\n"
            "│   └── params.json\n"
            "├── data/\n"
            "│   ├── dataset.csv\n"
            "│   └── records.parquet\n"
            "├── models/\n"
            "│   └── model.pkl\n"
            "└── src/\n"
            "    └── main.py\n"
        )
        self.tree_text.insert(tk.END, default_tree)

        # Progress Bar & Status Line
        progress_frame = ttk.Frame(parent, padding=(0, 4))
        progress_frame.pack(fill=tk.X)

        self.prog_var = tk.DoubleVar(value=0.0)
        self.prog_bar = ttk.Progressbar(progress_frame, variable=self.prog_var, maximum=100)
        self.prog_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 2))

        self.lbl_status = ttk.Label(progress_frame, text="Ready", font=("Segoe UI", 9))
        self.lbl_status.pack(side=tk.LEFT)

        # Action Buttons
        action_box = ttk.Frame(parent, padding=(0, 4))
        action_box.pack(fill=tk.X)

        self.reorg_btn = ttk.Button(
            action_box, text="🚀 Reconstruct Directory Structure", command=self._start_reconstruction
        )
        self.reorg_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.open_dest_btn = ttk.Button(
            action_box, text="📂 Open Destination Folder", command=self._open_destination, state="disabled"
        )
        self.open_dest_btn.pack(side=tk.RIGHT)

        # Logs Console
        log_frame = ttk.LabelFrame(parent, text="Execution Logs & Audit", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(
            log_frame, height=8, state="disabled", font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # TAB 2: TREE GENERATION LOGIC
    # -------------------------------------------------------------------------
    def _init_generate_tab(self, parent: ttk.Frame):
        gen_paths = ttk.LabelFrame(parent, text="Target Directory", padding=10)
        gen_paths.pack(fill=tk.X, pady=5)

        ttk.Label(gen_paths, text="Folder to Model:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.gen_folder_entry = ttk.Entry(gen_paths, width=65)
        self.gen_folder_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        self.gen_folder_entry.insert(0, str(Path.cwd()))
        ttk.Button(gen_paths, text="Browse...", command=self._browse_gen_folder).grid(row=0, column=2, padx=2)
        gen_paths.columnconfigure(1, weight=1)

        # Scan Controls
        gen_opts = ttk.LabelFrame(parent, text="Scan Controls", padding=10)
        gen_opts.pack(fill=tk.X, pady=5)

        self.include_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            gen_opts, text="Include files (uncheck for folders only)", variable=self.include_files_var
        ).pack(side=tk.LEFT, padx=10)

        ttk.Label(gen_opts, text="Max Depth:").pack(side=tk.LEFT, padx=(15, 2))
        self.max_depth_spin = ttk.Spinbox(gen_opts, from_=0, to=20, width=5)
        self.max_depth_spin.set("0")  # 0 = Unlimited
        self.max_depth_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(gen_opts, text="(0 = unlimited)").pack(side=tk.LEFT, padx=2)

        ttk.Button(gen_opts, text="⚡ Scan and Generate ASCII", command=self._generate_ascii_tree).pack(
            side=tk.RIGHT, padx=5
        )

        # Output Text View
        out_frame = ttk.LabelFrame(parent, text="Generated ASCII Output", padding=10)
        out_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        tool_bar = ttk.Frame(out_frame)
        tool_bar.pack(fill=tk.X, pady=2)

        ttk.Button(tool_bar, text="📋 Copy to Clipboard", command=self._copy_generated_to_clipboard).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(tool_bar, text="💾 Save to .txt File...", command=self._save_generated_file).pack(
            side=tk.LEFT, padx=2
        )

        self.gen_text_out = tk.Text(out_frame, wrap=tk.NONE, font=("Consolas", 10))
        self.gen_text_out.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        gen_scroll = ttk.Scrollbar(out_frame, orient=tk.VERTICAL, command=self.gen_text_out.yview)
        gen_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.gen_text_out.configure(yscrollcommand=gen_scroll.set)

    # -------------------------------------------------------------------------
    # TAB 1 HANDLERS & RECONSTRUCTION WORKER
    # -------------------------------------------------------------------------
    def _browse_src(self):
        d = filedialog.askdirectory(initialdir=self.src_entry.get().strip())
        if d:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, d)

    def _browse_dest(self):
        d = filedialog.askdirectory(initialdir=self.dest_entry.get().strip())
        if d:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, d)

    def _load_tree_file(self):
        fpath = filedialog.askopenfilename(
            title="Select ASCII Tree Text File",
            filetypes=[("Text Files", "*.txt"), ("Markdown Files", "*.md"), ("All Files", "*.*")],
        )
        if fpath:
            try:
                content = Path(fpath).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = Path(fpath).read_text(encoding="latin-1")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")
                return
            self.tree_text.delete("1.0", tk.END)
            self.tree_text.insert(tk.END, content)

    def _open_destination(self):
        dest_path = Path(self.dest_entry.get().strip())
        if dest_path.exists():
            os.startfile(str(dest_path))
        else:
            messagebox.showwarning("Not Found", f"Destination path does not exist:\n{dest_path}")

    def _update_progress(self, val: float, msg: str):
        self.prog_var.set(val)
        self.lbl_status.config(text=msg)

    def _start_reconstruction(self):
        self.reorg_btn.configure(state="disabled")
        self.open_dest_btn.configure(state="disabled")
        self.prog_var.set(0.0)
        self.lbl_status.config(text="Processing...")
        threading.Thread(target=self._run_reconstruction_worker, daemon=True).start()

    def _run_reconstruction_worker(self):
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(self.log_text)

        try:
            src_path = Path(self.src_entry.get().strip())
            dest_path = Path(self.dest_entry.get().strip())
            tree_text = self.tree_text.get("1.0", tk.END).strip()

            if not src_path.is_dir():
                messagebox.showerror("Error", f"Source path is not a valid directory:\n{src_path}")
                return
            if not tree_text:
                messagebox.showerror("Error", "ASCII tree specification cannot be empty.")
                return

            with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tf:
                tf.write(tree_text)
                tmp_tree = Path(tf.name)

            try:
                parser = AsciiTreeParser(tmp_tree, fallback_width=self.indent_var.get())
                nodes = parser.parse()
            finally:
                if tmp_tree.exists():
                    tmp_tree.unlink()

            if not nodes:
                print("[WARN] No valid nodes parsed from the tree.")
                return

            reorganizer = DirectoryReorganizer(
                source_dir=src_path,
                target_dir=dest_path,
                move_files=self.move_var.get(),
                overwrite=self.overwrite_var.get(),
                clean_relocated=self.clean_relocated_var.get(),
            )

            print("--- Pre-flight Audit ---")
            auditor = StructureAuditor(nodes, reorganizer.source_index)
            auditor.run_audit()
            print("------------------------\n")

            print("--- Starting File Placement & Sync ---")

            # 1. Clean relocated old files once across the whole desired tree
            if reorganizer.clean_relocated:
                reorganizer._cleanup_old_positions(nodes)

            # 2. Place each node incrementally and update progress bar
            total_nodes = len(nodes)
            for idx, node in enumerate(nodes, start=1):
                reorganizer._place_single_node(node)
                pct = (idx / total_nodes) * 100.0
                self.after(0, self._update_progress, pct, f"Processing {idx}/{total_nodes}: {node.name}")

            self.after(0, self._update_progress, 100.0, "Complete")
            print("\n[SUCCESS] Operation finished.")
            self.after(0, lambda: self.open_dest_btn.configure(state="normal"))
            messagebox.showinfo("Complete", f"Hierarchy synchronized successfully at:\n{dest_path}")

        except Exception as e:
            print(f"\n[ERROR] {e}")
            messagebox.showerror("Execution Failed", str(e))
        finally:
            sys.stdout = old_stdout
            self.after(0, lambda: self.reorg_btn.configure(state="normal"))

    # -------------------------------------------------------------------------
    # TAB 2 HANDLERS: TREE GENERATION
    # -------------------------------------------------------------------------
    def _browse_gen_folder(self):
        d = filedialog.askdirectory(initialdir=self.gen_folder_entry.get().strip())
        if d:
            self.gen_folder_entry.delete(0, tk.END)
            self.gen_folder_entry.insert(0, d)

    def _generate_ascii_tree(self):
        target_dir = Path(self.gen_folder_entry.get().strip())
        if not target_dir.is_dir():
            messagebox.showerror("Invalid Path", "Selected folder does not exist.")
            return

        depth_val = int(self.max_depth_spin.get())
        max_depth = None if depth_val <= 0 else depth_val

        options = GeneratorOptions(
            include_files=self.include_files_var.get(),
            max_depth=max_depth,
            indent_step=4,
        )

        generator = DirectoryTreeGenerator(target_dir, options=options)
        try:
            tree_output = generator.generate()
            self.gen_text_out.delete("1.0", tk.END)
            self.gen_text_out.insert(tk.END, tree_output)
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))

    def _copy_generated_to_clipboard(self):
        text = self.gen_text_out.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Clipboard", "No generated tree to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Clipboard", "ASCII tree copied to clipboard!")

    def _save_generated_file(self):
        text = self.gen_text_out.get("1.0", tk.END).strip()
        if not text:
            return
        f = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("Markdown file", "*.md")],
        )
        if f:
            Path(f).write_text(text, encoding="utf-8")
            messagebox.showinfo("Saved", f"Tree exported successfully to {f}")


# -------------------------------------------------------------------------
# ENTRYPOINT EXPORTS
# -------------------------------------------------------------------------
def launch_gui():
    """Primary entrypoint for the GUI application."""
    app = AsciiTreeReorgApp()
    app.mainloop()


# Backward-compatible alias for runners importing run_gui
run_gui = launch_gui


def main():
    launch_gui()


if __name__ == "__main__":
    launch_gui()