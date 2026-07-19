"""Native desktop viewer for Mermaid .mmd files."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from interactive_graph import FlowchartParser, InteractiveGraph, build_relation_color_map


class MermaidViewer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Mermaid Diagram Viewer")
        self.geometry("1160x780")
        self.minsize(720, 480)

        self.source_path: Path | None = None
        self.original_image: tk.PhotoImage | None = None
        self.display_image: tk.PhotoImage | None = None
        self.zoom = 1.0
        self.render_generation = 0
        self.zoom_render_job: str | None = None
        self.graph: InteractiveGraph | None = None
        self.drag_node_id: str | None = None
        self.drag_last = (0, 0)
        self.selecting_edge = False
        self.relation_colors: dict[str, str] = {}
        self.detail_title = tk.StringVar(value="Nothing selected")
        self.detail_kind = tk.StringVar(value="Select an entity or relationship")
        self.detail_meaning = tk.StringVar(value="Click a graph item to see what it means.")
        self.status = tk.StringVar(value="Ready - open a Mermaid diagram to begin")
        self.file_name = tk.StringVar(value="No diagram open")

        self._configure_styles()
        self.logo_image = self._load_logo()
        if self.logo_image:
            self.iconphoto(True, self.logo_image)
        self._build_ui()
        self.bind("<Control-o>", lambda _event: self.open_file())
        self.bind("<Control-r>", lambda _event: self.reload_file())
        self.bind("<Control-plus>", lambda _event: self.change_zoom(1.2))
        self.bind("<Control-minus>", lambda _event: self.change_zoom(1 / 1.2))

    def _configure_styles(self) -> None:
        self.configure(background="#eef2f7")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#eef2f7")
        style.configure("Header.TFrame", background="#111827")
        style.configure("Title.TLabel", background="#111827", foreground="#f9fafb", font=("Segoe UI Semibold", 17))
        style.configure("Subtitle.TLabel", background="#111827", foreground="#94a3b8", font=("Segoe UI", 9))
        style.configure("Primary.TButton", background="#6366f1", foreground="white", borderwidth=0, padding=(16, 9), font=("Segoe UI Semibold", 9))
        style.map("Primary.TButton", background=[("active", "#4f46e5"), ("pressed", "#4338ca")])
        style.configure("Toolbar.TButton", background="#1f2937", foreground="#e5e7eb", borderwidth=0, padding=(12, 9), font=("Segoe UI", 9))
        style.map("Toolbar.TButton", background=[("active", "#374151"), ("pressed", "#4b5563")])
        style.configure("Zoom.TButton", background="#1f2937", foreground="#f9fafb", borderwidth=0, padding=(8, 8), font=("Segoe UI Semibold", 11))
        style.map("Zoom.TButton", background=[("active", "#374151"), ("pressed", "#4b5563")])
        style.configure("Zoom.TLabel", background="#111827", foreground="#c7d2fe", font=("Segoe UI Semibold", 10), padding=(6, 0))
        style.configure("Status.TLabel", background="#f8fafc", foreground="#64748b", font=("Segoe UI", 9), padding=(14, 8))

    def _load_logo(self) -> tk.PhotoImage | None:
        logo_path = Path(__file__).parent / "assets" / "app-logo.png"
        try:
            source = tk.PhotoImage(file=str(logo_path))
        except tk.TclError:
            return None
        target_size = 54
        factor = max(1, (max(source.width(), source.height()) + target_size - 1) // target_size)
        return source.subsample(factor, factor) if factor > 1 else source

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(22, 14))
        header.pack(fill=tk.X)

        brand = ttk.Frame(header, style="Header.TFrame")
        brand.pack(side=tk.LEFT)
        if self.logo_image:
            tk.Label(brand, image=self.logo_image, background="white", borderwidth=0, padx=4, pady=4).pack(side=tk.LEFT, padx=(0, 12))
        brand_text = ttk.Frame(brand, style="Header.TFrame")
        brand_text.pack(side=tk.LEFT)
        ttk.Label(brand_text, text="Mermaid Viewer", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(brand_text, textvariable=self.file_name, style="Subtitle.TLabel").pack(anchor=tk.W, pady=(2, 0))

        controls = ttk.Frame(header, style="Header.TFrame")
        controls.pack(side=tk.RIGHT)
        ttk.Button(controls, text="Open diagram", style="Primary.TButton", command=self.open_file).pack(side=tk.LEFT)
        ttk.Button(controls, text="Reload", style="Toolbar.TButton", command=self.reload_file).pack(side=tk.LEFT, padx=(8, 20))
        ttk.Button(controls, text="-", width=3, style="Zoom.TButton", command=lambda: self.change_zoom(1 / 1.2)).pack(side=tk.LEFT)
        self.zoom_label = ttk.Label(controls, text="100%", width=7, anchor=tk.CENTER, style="Zoom.TLabel")
        self.zoom_label.pack(side=tk.LEFT)
        ttk.Button(controls, text="+", width=3, style="Zoom.TButton", command=lambda: self.change_zoom(1.2)).pack(side=tk.LEFT)
        ttk.Button(controls, text="Fit", style="Toolbar.TButton", command=self.fit_to_window).pack(side=tk.LEFT, padx=(8, 0))

        shell = ttk.Frame(self, style="App.TFrame", padding=(18, 18, 18, 12))
        shell.pack(fill=tk.BOTH, expand=True)
        self.legend = tk.Frame(shell, background="#f8fafc", highlightbackground="#dbe3ee", highlightthickness=1, padx=14, pady=14)
        self.legend.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        tk.Label(self.legend, text="RELATIONSHIPS", background="#f8fafc", foreground="#64748b", font=("Segoe UI Semibold", 9)).pack(anchor=tk.W, pady=(0, 10))
        self.legend_items = tk.Frame(self.legend, background="#f8fafc")
        self.legend_items.pack(fill=tk.X)
        tk.Label(self.legend_items, text="Open a flowchart", background="#f8fafc", foreground="#94a3b8", font=("Segoe UI", 9)).pack(anchor=tk.W)
        tk.Frame(self.legend, background="#dbe3ee", height=1).pack(fill=tk.X, pady=(18, 14))
        tk.Label(self.legend, text="SELECTED ITEM", background="#f8fafc", foreground="#64748b", font=("Segoe UI Semibold", 9)).pack(anchor=tk.W)
        tk.Label(self.legend, textvariable=self.detail_title, background="#f8fafc", foreground="#0f172a", font=("Segoe UI Semibold", 11), wraplength=210, justify=tk.LEFT).pack(anchor=tk.W, pady=(9, 2))
        tk.Label(self.legend, textvariable=self.detail_kind, background="#f8fafc", foreground="#6366f1", font=("Segoe UI Semibold", 8), wraplength=210, justify=tk.LEFT).pack(anchor=tk.W)
        tk.Label(self.legend, textvariable=self.detail_meaning, background="#f8fafc", foreground="#475569", font=("Segoe UI", 9), wraplength=210, justify=tk.LEFT).pack(anchor=tk.W, pady=(9, 0))
        frame = tk.Frame(shell, background="#ffffff", highlightbackground="#dbe3ee", highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(frame, background="#ffffff", highlightthickness=0, cursor="hand2")
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.canvas.create_text(0, 0, text="Open a Mermaid file to preview your diagram", fill="#94a3b8", font=("Segoe UI", 13), tags="empty-state")

        self.canvas.bind("<MouseWheel>", self._mouse_wheel)
        self.canvas.bind("<Button-4>", lambda event: self.change_zoom(1.1))
        self.canvas.bind("<Button-5>", lambda event: self.change_zoom(1 / 1.1))
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._drag_pan)
        self.canvas.bind("<ButtonRelease-1>", self._end_pan)
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._drag_pan)
        self.canvas.bind("<ButtonRelease-2>", self._end_pan)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.fit_to_window())
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        status_bar = ttk.Frame(self, style="App.TFrame")
        status_bar.pack(fill=tk.X)
        ttk.Label(status_bar, textvariable=self.status, style="Status.TLabel", anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(status_bar, text="Drag entity: move  |  Drag canvas: pan  |  Wheel: zoom  |  Double-click: fit", style="Status.TLabel", anchor=tk.E).pack(side=tk.RIGHT)

    def _on_canvas_resize(self, _event: tk.Event | None = None) -> None:
        self._center_image()
        if not self.display_image:
            self.canvas.coords("empty-state", self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2)

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(title="Open Mermaid diagram", filetypes=(("Mermaid files", "*.mmd"), ("All files", "*.*")))
        if filename:
            self.source_path = Path(filename)
            self.file_name.set(self.source_path.name)
            self.zoom = 1.0
            self._load_diagram()

    def reload_file(self) -> None:
        if self.source_path:
            self._load_diagram()

    def _load_diagram(self) -> None:
        assert self.source_path is not None
        try:
            source = self.source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            messagebox.showerror("Could not open diagram", str(exc))
            return
        graph = FlowchartParser().parse(source)
        if graph:
            self._show_interactive_graph(graph)
        else:
            self.graph = None
            self._clear_details()
            self.canvas.delete("graph")
            self._update_legend()
            self.render_file()

    def _show_interactive_graph(self, graph: InteractiveGraph) -> None:
        self.graph = graph
        self.relation_colors = build_relation_color_map([edge.label for edge in graph.edges])
        self.graph_offset = (20.0, 20.0)
        self.original_image = None
        self.display_image = None
        self._clear_details()
        self.canvas.delete("all")
        self._draw_graph()
        self._update_legend()
        if self.source_path:
            self.title(f"{self.source_path.name} - Mermaid Diagram Viewer")
        self.status.set(f"Interactive flowchart  |  {len(graph.nodes)} entities  |  {len(graph.edges)} relationships")
        self.after_idle(self.fit_to_window)

    def _update_legend(self) -> None:
        for child in self.legend_items.winfo_children():
            child.destroy()
        if not self.graph:
            tk.Label(self.legend_items, text="Static diagram", background="#f8fafc", foreground="#94a3b8", font=("Segoe UI", 9)).pack(anchor=tk.W)
            return
        labels = list(dict.fromkeys(edge.label for edge in self.graph.edges))
        for label in labels:
            row = tk.Frame(self.legend_items, background="#f8fafc")
            row.pack(fill=tk.X, pady=4)
            swatch = tk.Label(row, text="  ", width=2, background=self.relation_colors[label], cursor="hand2")
            swatch.pack(side=tk.LEFT, padx=(0, 8))
            name = tk.Label(row, text=label, background="#f8fafc", foreground="#334155", font=("Segoe UI Semibold", 9), cursor="hand2")
            name.pack(side=tk.LEFT)
            for widget in (row, swatch, name):
                widget.bind("<Button-1>", lambda _event, relation=label: self._show_relation_details(relation))

    def _clear_details(self) -> None:
        self.detail_title.set("Nothing selected")
        self.detail_kind.set("Select an entity or relationship")
        self.detail_meaning.set("Click a graph item to see what it means.")

    def _show_node_details(self, node_id: str) -> None:
        if not self.graph:
            return
        node = self.graph.nodes[node_id]
        self.detail_title.set(node.label)
        self.detail_kind.set(f"ENTITY  |  {node.shape.upper()}")
        self.detail_meaning.set(node.meaning)

    def _show_edge_details(self, edge_index: int) -> None:
        if not self.graph or edge_index >= len(self.graph.edges):
            return
        edge = self.graph.edges[edge_index]
        source = self.graph.nodes[edge.source].label
        target = self.graph.nodes[edge.target].label
        self.detail_title.set(edge.label)
        self.detail_kind.set(f"RELATIONSHIP  |  {source} -> {target}")
        self.detail_meaning.set(edge.meaning)

    def _show_relation_details(self, label: str) -> None:
        if not self.graph:
            return
        matching = [edge for edge in self.graph.edges if edge.label == label]
        self.detail_title.set(label)
        self.detail_kind.set(f"RELATIONSHIP TYPE  |  {len(matching)} connection(s)")
        meanings = list(dict.fromkeys(edge.meaning for edge in matching))
        self.detail_meaning.set("\n\n".join(meanings))

    def render_file(self) -> None:
        assert self.source_path is not None
        local_renderer = Path(__file__).parent / "node_modules" / ".bin" / "mmdc.cmd"
        renderer = (str(local_renderer) if local_renderer.exists() else None) or shutil.which("mmdc") or shutil.which("mmdc.cmd")
        if not renderer:
            messagebox.showerror("Mermaid CLI not found", "The Mermaid renderer is not installed.\n\nRun setup.bat once, or run npm install in the project folder.")
            self.status.set("Renderer missing - install @mermaid-js/mermaid-cli")
            return

        self.render_generation += 1
        generation = self.render_generation
        requested_zoom = self.zoom
        self.status.set(f"Rendering {self.source_path.name}...")
        self.config(cursor="watch")
        threading.Thread(target=self._render_worker, args=(renderer, self.source_path, generation, requested_zoom), daemon=True).start()

    def _render_worker(self, renderer: str, source: Path, generation: int, requested_zoom: float) -> None:
        output = Path(tempfile.gettempdir()) / f"mermaid-viewer-{generation}.png"
        try:
            result = subprocess.run(
                [renderer, "-i", str(source), "-o", str(output), "-b", "transparent", "-s", f"{2 * requested_zoom:.4g}"],
                capture_output=True, text=True, timeout=60, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout or "Unknown rendering error").strip())
            self.after(0, lambda: self._show_render(output, source, generation))
        except Exception as exc:
            self.after(0, lambda: self._show_error(str(exc), generation))

    def _show_render(self, output: Path, source: Path, generation: int) -> None:
        if generation != self.render_generation:
            return
        self.config(cursor="")
        try:
            self.original_image = tk.PhotoImage(file=str(output))
        except tk.TclError as exc:
            self._show_error(f"Could not load rendered image: {exc}", generation)
            return
        self.canvas.delete("empty-state")
        self._update_legend()
        self._update_image()
        self.title(f"{source.name} - Mermaid Diagram Viewer")
        self.status.set(f"{source}  |  {self.original_image.width()} x {self.original_image.height()} px")

    def _show_error(self, error: str, generation: int) -> None:
        if generation != self.render_generation:
            return
        self.config(cursor="")
        self.status.set("Rendering failed")
        messagebox.showerror("Could not render diagram", error)

    def change_zoom(self, factor: float) -> None:
        if (not self.original_image and not self.graph) or not self.source_path:
            return
        self.zoom = min(4.0, max(0.1, self.zoom * factor))
        self.zoom_label.configure(text=f"{self.zoom:.0%}")
        if self.graph:
            self._draw_graph()
        else:
            self._schedule_zoom_render()

    def fit_to_window(self) -> None:
        if self.graph:
            xs = [position[0] for position in self.graph.positions.values()]
            ys = [position[1] for position in self.graph.positions.values()]
            if not xs or not ys:
                return
            graph_w = max(xs) - min(xs) + 220
            graph_h = max(ys) - min(ys) + 140
            available_w = max(1, self.canvas.winfo_width() - 40)
            available_h = max(1, self.canvas.winfo_height() - 40)
            self.zoom = min(1.5, available_w / graph_w, available_h / graph_h)
            self._draw_graph(center=True)
            return
        if not self.original_image:
            return
        available_w = max(1, self.canvas.winfo_width() - 40)
        available_h = max(1, self.canvas.winfo_height() - 40)
        self.zoom = min(1.0, self.zoom * available_w / self.original_image.width(), self.zoom * available_h / self.original_image.height())
        self.zoom_label.configure(text=f"{self.zoom:.0%}")
        self._schedule_zoom_render(delay_ms=0)

    def _schedule_zoom_render(self, delay_ms: int = 140) -> None:
        if self.zoom_render_job is not None:
            self.after_cancel(self.zoom_render_job)
        self.zoom_render_job = self.after(delay_ms, self._render_zoom)

    def _render_zoom(self) -> None:
        self.zoom_render_job = None
        self.render_file()

    def _update_image(self) -> None:
        assert self.original_image is not None
        self.display_image = self.original_image
        self.canvas.delete("diagram")
        self.canvas.create_image(0, 0, image=self.display_image, anchor=tk.NW, tags="diagram")
        self.canvas.configure(scrollregion=(0, 0, self.display_image.width(), self.display_image.height()))
        self.zoom_label.configure(text=f"{self.zoom:.0%}")
        self._center_image()

    def _draw_graph(self, center: bool = False) -> None:
        if not self.graph:
            return
        self.canvas.delete("graph")
        scale = self.zoom
        offset_x, offset_y = getattr(self, "graph_offset", (20.0, 20.0))
        if center:
            xs = [position[0] for position in self.graph.positions.values()]
            ys = [position[1] for position in self.graph.positions.values()]
            scaled_w = (max(xs) - min(xs) + 180) * scale
            scaled_h = (max(ys) - min(ys) + 100) * scale
            offset_x = max(20.0, (self.canvas.winfo_width() - scaled_w) / 2 - min(xs) * scale + 90 * scale)
            offset_y = max(20.0, (self.canvas.winfo_height() - scaled_h) / 2 - min(ys) * scale + 50 * scale)
        self.graph_offset = (offset_x, offset_y)

        for index, edge in enumerate(self.graph.edges):
            source = self._screen_position(edge.source)
            target = self._screen_position(edge.target)
            start, end = self._edge_endpoints(source, target)
            color = self.relation_colors[edge.label]
            dash = (7, 5) if edge.style == "dashed" else ()
            self.canvas.create_line(*start, *end, fill=color, width=max(2, round(2.4 * scale)), arrow=tk.LAST, arrowshape=(10, 12, 5), dash=dash, tags=("graph", f"edge:{index}"))
            mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
            text_id = self.canvas.create_text(mid_x, mid_y - 10, text=edge.label, fill=color, font=("Segoe UI Semibold", max(8, round(9 * scale))), tags=("graph", f"edge:{index}"))
            bbox = self.canvas.bbox(text_id)
            if bbox:
                background = self.canvas.create_rectangle(bbox[0] - 5, bbox[1] - 2, bbox[2] + 5, bbox[3] + 2, fill="white", outline=color, width=1, tags=("graph", f"edge:{index}"))
                self.canvas.tag_lower(background, text_id)

        for node_id, node in self.graph.nodes.items():
            x, y = self._screen_position(node_id)
            half_w, half_h = 82 * scale, 36 * scale
            tags = ("graph", f"node:{node_id}")
            if node.shape == "diamond":
                self.canvas.create_polygon(x, y - half_h - 8 * scale, x + half_w, y, x, y + half_h + 8 * scale, x - half_w, y, fill="#f8fafc", outline="#334155", width=2, tags=tags)
            elif node.shape == "circle":
                radius = 45 * scale
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#f8fafc", outline="#334155", width=2, tags=tags)
            elif node.shape == "rounded":
                radius = 14 * scale
                points = (
                    x - half_w + radius, y - half_h, x + half_w - radius, y - half_h,
                    x + half_w, y - half_h + radius, x + half_w, y + half_h - radius,
                    x + half_w - radius, y + half_h, x - half_w + radius, y + half_h,
                    x - half_w, y + half_h - radius, x - half_w, y - half_h + radius,
                )
                self.canvas.create_polygon(*points, smooth=True, splinesteps=12, fill="#f8fafc", outline="#334155", width=2, tags=tags)
            else:
                self.canvas.create_rectangle(x - half_w, y - half_h, x + half_w, y + half_h, fill="#f8fafc", outline="#334155", width=2, tags=tags)
            self.canvas.create_text(x, y, text=node.label, fill="#0f172a", width=max(60, round(140 * scale)), font=("Segoe UI Semibold", max(8, round(10 * scale))), tags=tags)

        bbox = self.canvas.bbox("graph")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0] - 30, bbox[1] - 30, bbox[2] + 30, bbox[3] + 30))
        self.zoom_label.configure(text=f"{self.zoom:.0%}")

    def _screen_position(self, node_id: str) -> tuple[float, float]:
        assert self.graph is not None
        x, y = self.graph.positions[node_id]
        offset_x, offset_y = getattr(self, "graph_offset", (20.0, 20.0))
        return x * self.zoom + offset_x, y * self.zoom + offset_y

    def _edge_endpoints(self, source: tuple[float, float], target: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
        dx, dy = target[0] - source[0], target[1] - source[1]
        if not dx and not dy:
            return source, target
        half_w, half_h = 88 * self.zoom, 43 * self.zoom
        factor = min(0.45, half_w / max(abs(dx), 0.001), half_h / max(abs(dy), 0.001))
        return (source[0] + dx * factor, source[1] + dy * factor), (target[0] - dx * factor, target[1] - dy * factor)

    def _center_image(self) -> None:
        if not self.display_image:
            return
        x = max(0, (self.canvas.winfo_width() - self.display_image.width()) // 2)
        y = max(0, (self.canvas.winfo_height() - self.display_image.height()) // 2)
        self.canvas.coords("diagram", x, y)
        self.canvas.configure(scrollregion=(0, 0, max(self.canvas.winfo_width(), x + self.display_image.width()), max(self.canvas.winfo_height(), y + self.display_image.height())))

    def _start_pan(self, event: tk.Event) -> None:
        self.selecting_edge = False
        current = self.canvas.find_withtag("current")
        if self.graph and current:
            tags = self.canvas.gettags(current[0])
            for tag in tags:
                if tag.startswith("node:"):
                    self.drag_node_id = tag.split(":", 1)[1]
                    self._show_node_details(self.drag_node_id)
                    self.drag_last = (event.x, event.y)
                    self.canvas.configure(cursor="fleur")
                    return
            for tag in tags:
                if tag.startswith("edge:"):
                    self._show_edge_details(int(tag.split(":", 1)[1]))
                    self.selecting_edge = True
                    return
        if not self.display_image and not self.graph:
            return
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def _drag_pan(self, event: tk.Event) -> None:
        if self.selecting_edge:
            return
        if self.graph and self.drag_node_id:
            old_x, old_y = self.graph.positions[self.drag_node_id]
            delta_x = (event.x - self.drag_last[0]) / self.zoom
            delta_y = (event.y - self.drag_last[1]) / self.zoom
            self.graph.positions[self.drag_node_id] = (old_x + delta_x, old_y + delta_y)
            self.drag_last = (event.x, event.y)
            self._draw_graph()
        elif self.display_image or self.graph:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _end_pan(self, _event: tk.Event) -> None:
        self.drag_node_id = None
        self.selecting_edge = False
        self.canvas.configure(cursor="hand2")

    def _mouse_wheel(self, event: tk.Event) -> None:
        if event.state & 0x0001:  # Shift + wheel scrolls horizontally.
            self.canvas.xview_scroll(-1 if event.delta > 0 else 1, "units")
        else:
            self.change_zoom(1.1 if event.delta > 0 else 1 / 1.1)


if __name__ == "__main__":
    MermaidViewer().mainloop()
