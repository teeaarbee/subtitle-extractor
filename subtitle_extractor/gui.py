import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List

from .ffutils import ffprobe_subtitle_streams, extract_subtitles, SubtitleStream


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Subtitle Extractor (SRT from MKV)")
        self.geometry("700x450")

        self.mkv_var = tk.StringVar()
        self.out_var = tk.StringVar()

        # File chooser
        frm_top = tk.Frame(self)
        frm_top.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(frm_top, text="MKV file:").pack(side=tk.LEFT)
        entry = tk.Entry(frm_top, textvariable=self.mkv_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        tk.Button(frm_top, text="Browse", command=self.choose_mkv).pack(side=tk.LEFT)

        # Output chooser
        frm_out = tk.Frame(self)
        frm_out.pack(fill=tk.X, padx=10, pady=0)
        tk.Label(frm_out, text="Output folder:").pack(side=tk.LEFT)
        entry2 = tk.Entry(frm_out, textvariable=self.out_var)
        entry2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        tk.Button(frm_out, text="Choose", command=self.choose_out).pack(side=tk.LEFT)

        # Probe button
        frm_actions = tk.Frame(self)
        frm_actions.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(frm_actions, text="Detect Subtitles", command=self.detect).pack(side=tk.LEFT)

        # Listbox of streams with multi-select
        self.listbox = tk.Listbox(self, selectmode=tk.EXTENDED)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        # Extract button
        frm_extract = tk.Frame(self)
        frm_extract.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(frm_extract, text="Extract Selected SRT", command=self.extract_selected).pack(side=tk.RIGHT)

        self.detected_streams: List[SubtitleStream] = []

    def choose_mkv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("MKV files", "*.mkv")])
        if path:
            self.mkv_var.set(path)
            # Default output to the MKV's folder if none chosen yet
            if not self.out_var.get():
                self.out_var.set(str(Path(path).parent))

    def choose_out(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.out_var.set(path)

    def detect(self) -> None:
        mkv = Path(self.mkv_var.get())
        if not mkv.is_file():
            messagebox.showerror("Error", "Please choose a valid MKV file")
            return
        try:
            streams = ffprobe_subtitle_streams(mkv)
        except Exception as e:
            messagebox.showerror("ffprobe error", str(e))
            return

        self.detected_streams = [s for s in streams if s.is_subrip]
        self.listbox.delete(0, tk.END)
        if not self.detected_streams:
            self.listbox.insert(tk.END, "No SubRip (SRT) subtitles found.")
            return
        for s in self.detected_streams:
            self.listbox.insert(tk.END, s.display_label())

    def extract_selected(self) -> None:
        mkv = Path(self.mkv_var.get())
        outdir = Path(self.out_var.get() or mkv.parent)
        if not mkv.is_file():
            messagebox.showerror("Error", "Please choose a valid MKV file")
            return
        if not outdir.exists():
            try:
                outdir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output: {e}")
                return

        if not self.detected_streams:
            self.detect()
            if not self.detected_streams:
                return

        sel = [self.detected_streams[i] for i in self.listbox.curselection()] or self.detected_streams
        try:
            outputs = extract_subtitles(mkv, sel, outdir)
        except Exception as e:
            messagebox.showerror("ffmpeg error", str(e))
            return
        messagebox.showinfo("Done", f"Extracted {len(outputs)} file(s) to:\n{outdir}")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()


