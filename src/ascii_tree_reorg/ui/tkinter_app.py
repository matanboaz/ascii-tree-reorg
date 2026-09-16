import os
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..core.parser import AsciiTreeParser
from ..engine.reorganizer import DirectoryReorganizer


class TextRedirector:
    """Redirects stdout/stderr writes directly into a Tkinter Text widget."""

    def __init__(self, widget: tk.Text):
        self.widget = widget

    def write(self, text: str) -> None:
        def _append():
            self.widget.insert(tk.END, text)
            self.widget.see(tk.END)

        self.widget.after(0, _append)

    def flush(self) -> None:
        pass


class AsciiTreeReorgApp(tk.Tk):
    """Main desktop GUI for ASCII Tree Reorganization."""

    def __init__(self):
        super().__init__()
        self.title("ASCII Tree Directory Reorganizer")
        self.geometry("960x780")
        self.minsize(820, 640)

        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent

        self._init_variables()
        self._build_ui()

    def _init_variables(self) -> None:
        default_source = self.repo_root / "data" / "inputs" / "raw_archive"
        default_dest = self.repo_root / "data" / "outputs"

        self.src_var = tk.StringVar(value=str(default_source) if default_source.exists() else "")
        self.dst_var = tk.StringVar(value=str(default_dest) if default_dest.exists() else "")
        self.move_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=True)
        self.clean_relocated_var = tk.BooleanVar(value=True)
        self.indent_var = tk.IntVar(value=4)
        self.status_var = tk.StringVar(value="Ready")

    def _build_ui(self) -> None:
        # Paths Frame
        frm_paths = ttk.LabelFrame(self, text="Path Configurations", padding=10)
        frm_paths.pack(fill=tk.X, padx=12, pady=6)

        # Source Dir
        ttk.Label(frm_paths, text="Source Folder:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frm_paths, textvariable=self.src_var, width=70).grid(row=0, column=1, sticky=tk.EW, padx=6)
        ttk.Button(frm_paths, text="Browse...", command=self._browse_source).grid(row=0, column=2, padx=2)

        # Dest Dir
        ttk.Label(frm_paths, text="Destination:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frm_paths, textvariable=self.dst_var, width=70).grid(row=1, column=1, sticky=tk.EW, padx=6)
        ttk.Button(frm_paths, text="Browse...", command=self._browse_dest).grid(row=1, column=2, padx=2)

        frm_paths.columnconfigure(1, weight=1)

        # Options Frame
        frm_opts = ttk.LabelFrame(self, text="Execution Options", padding=10)
        frm_opts.pack(fill=tk.X, padx=12, pady=4)

        ttk.Checkbutton(frm_opts, text="Move files (cut instead of copy)", variable=self.move_var).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Checkbutton(frm_opts, text="Overwrite existing files", variable=self.overwrite_var).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Checkbutton(
            frm_opts,
            text="Clean relocated / orphan files",
            variable=self.clean_relocated_var,
        ).pack(side=tk.LEFT, padx=6)

        ttk.Label(frm_opts, text="Indent Width:").pack(side=tk.LEFT, padx=(16, 4))
        ttk.Spinbox(frm_opts, from_=2, to=8, textvariable=self.indent_var, width=4).pack(side=tk.LEFT)

        # Tree Editor Frame
        frm_tree = ttk.LabelFrame(self, text="ASCII Directory Structure", padding=10)
        frm_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        frm_tree_toolbar = ttk.Frame(frm_tree)
        frm_tree_toolbar.pack(fill=tk.X, pady=(0, 4))

        ttk.Button(frm_tree_toolbar, text="📂 Load Tree File...", command=self._load_tree_file).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(frm_tree_toolbar, text="🧹 Clear Text", command=self._clear_tree_text).pack(
            side=tk.LEFT, padx=2
        )

        self.txt_tree = tk.Text(frm_tree, wrap=tk.NONE, font=("Consolas", 10), height=12)
        sb_tree_y = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL, command=self.txt_tree.yview)
        sb_tree_x = ttk.Scrollbar(frm_tree, orient=tk.HORIZONTAL, command=self.txt_tree.xview)
        self.txt_tree.configure(xscrollcommand=sb_tree_x.set, yscrollcommand=sb_tree_y.set)

        sb_tree_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_tree_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._load_initial_tree_template()

        # Action Button & Progress
        frm_action = ttk.Frame(self, padding=6)
        frm_action.pack(fill=tk.X, padx=12, pady=4)

        self.btn_run = ttk.Button(
            frm_action,
            text="🚀 Reconstruct Directory Structure",
            command=self._start_processing,
        )
        self.btn_run.pack(side=tk.LEFT, padx=4)

        self.btn_open_dest = ttk.Button(
            frm_action,
            text="📁 Open Destination Folder",
            state=tk.DISABLED,
            command=self._open_destination,
        )
        self.btn_open_dest.pack(side=tk.LEFT, padx=4)

        self.progress_bar = ttk.Progressbar(frm_action, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        self.lbl_status = ttk.Label(frm_action, textvariable=self.status_var, font=("Segoe UI", 9, "italic"))
        self.lbl_status.pack(side=tk.RIGHT, padx=4)

        # Log Terminal Frame
        frm_log = ttk.LabelFrame(self, text="Console Output & Audit Log", padding=10)
        frm_log.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))

        self.txt_log = tk.Text(frm_log, wrap=tk.WORD, font=("Consolas", 9), background="#1e1e1e", foreground="#d4d4d4")
        sb_log = ttk.Scrollbar(frm_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb_log.set)

        sb_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _browse_source(self) -> None:
        path = filedialog.askdirectory(title="Select Unorganized Source Folder")
        if path:
            self.src_var.set(path)

    def _browse_dest(self) -> None:
        path = filedialog.askdirectory(title="Select Target Destination Folder")
        if path:
            self.dst_var.set(path)

    def _load_tree_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open ASCII Tree File",
            filetypes=[("Text & Log Files", "*.txt *.log *.md"), ("All Files", "*.*")],
        )
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8")
                self.txt_tree.delete("1.0", tk.END)
                self.txt_tree.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file:\n{e}")

    def _clear_tree_text(self) -> None:
        self.txt_tree.delete("1.0", tk.END)

    def _load_initial_tree_template(self) -> None:
        default_tree_file = self.repo_root / "data" / "inputs" / "structure.txt"
        if default_tree_file.exists():
            try:
                content = default_tree_file.read_text(encoding="utf-8")
                self.txt_tree.insert(tk.END, content)
                return
            except Exception:
                pass

        sample = (
            "project_root/\n"
            "├── configs/\n"
            "│   └── config.yaml\n"
            "├── data/\n"
            "│   └── raw/\n"
            "└── src/\n"
            "    └── main.py\n"
        )
        self.txt_tree.insert(tk.END, sample)

    def _open_destination(self) -> None:
        path = Path(self.dst_var.get().strip()).resolve()
        if path.exists():
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])

    def _update_progress(self, value: float, status_text: str) -> None:
        self.progress_bar["value"] = value
        self.status_var.set(status_text)

    def _start_processing(self) -> None:
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()
        tree = self.txt_tree.get("1.0", tk.END).strip()

        if not src or not dst:
            messagebox.showwarning("Missing Fields", "Please specify both source and destination folders.")
            return

        if not tree:
            messagebox.showwarning("Missing Tree", "Please paste or load an ASCII directory tree.")
            return

        self.btn_run.configure(state=tk.DISABLED)
        self.btn_open_dest.configure(state=tk.DISABLED)
        self.txt_log.delete("1.0", tk.END)
        self.progress_bar["value"] = 0
        self.status_var.set("Processing...")

        threading.Thread(target=self._run_process, daemon=True).start()

    def _run_process(self) -> None:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = TextRedirector(self.txt_log)
        sys.stdout = redirector
        sys.stderr = redirector

        tmp_tree = None
        try:
            src_path = Path(self.src_var.get().strip()).resolve()
            dest_path = Path(self.dst_var.get().strip()).resolve()
            tree_text = self.txt_tree.get("1.0", tk.END).strip()

            print("================= DIAGNOSTIC RUN =================")
            print(f"[DEBUG] Source Directory      : {src_path}")
            print(f"[DEBUG] Destination Directory : {dest_path}")
            print(f"[DEBUG] Same Directory?       : {src_path == dest_path}")
            print(f"[DEBUG] Overwrite?            : {self.overwrite_var.get()}")
            print(f"[DEBUG] Clean Relocated?      : {self.clean_relocated_var.get()}")
            print(f"[DEBUG] Move Files?           : {self.move_var.get()}")

            if not src_path.is_dir():
                print(f"[ERROR] Source does not exist: {src_path}")
                messagebox.showerror("Error", f"Source directory not found:\n{src_path}")
                return

            with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tf:
                tf.write(tree_text)
                tmp_tree = Path(tf.name)

            parser = AsciiTreeParser(tmp_tree, fallback_width=self.indent_var.get())
            nodes = parser.parse(target_root_name=dest_path.name)

            print(f"\n[DEBUG] Total Parsed Nodes: {len(nodes)}")
            for n in nodes[:8]:
                print(f"   -> {'[DIR] ' if n.is_directory else '[FILE]'} {n.name:<25} | Target: {dest_path / n.relative_path}")
            if len(nodes) > 8:
                print(f"   ... and {len(nodes) - 8} more entries.")

            reorganizer = DirectoryReorganizer(
                source_dir=src_path,
                target_dir=dest_path,
                move_files=self.move_var.get(),
                overwrite=self.overwrite_var.get(),
                clean_relocated=self.clean_relocated_var.get(),
            )

            print(f"\n[DEBUG] Indexed Source Files: {len(reorganizer.source_index)} unique filenames found in source.")
            existing_in_dest = list(dest_path.rglob("*")) if dest_path.exists() else []
            print(f"[DEBUG] Existing Items in Dest: {len(existing_in_dest)} items found on disk.")

            print("\n---------------- EXECUTION LOG ----------------")

            # Execute cleanups (parent orphans + old positions)
            if reorganizer.clean_relocated:
                reorganizer._purge_parent_orphans(nodes)
                reorganizer._cleanup_old_positions(nodes)

            total = len(nodes)
            for idx, node in enumerate(nodes, start=1):
                reorganizer._place_single_node(node)
                pct = (idx / total) * 100.0
                self.after(0, self._update_progress, pct, f"{idx}/{total}: {node.name}")

            self.after(0, self._update_progress, 100.0, "Complete")
            print("=================================================")
            print("[DONE] Execution finished successfully.")
            self.after(0, lambda: self.btn_open_dest.configure(state="normal"))

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"\n[CRASH] {e}")
            messagebox.showerror("Execution Error", str(e))
        finally:
            if tmp_tree and tmp_tree.exists():
                try:
                    tmp_tree.unlink()
                except OSError:
                    pass
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.after(0, lambda: self.btn_run.configure(state="normal"))


def launch_gui() -> None:
    app = AsciiTreeReorgApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()