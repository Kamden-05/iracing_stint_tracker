import tkinter as tk
from tkinter import ttk


class StintLoggerGUI:
    def __init__(self, client, manager, stop_event, drivers):
        """
        Args:
            client: APIClient instance
            manager: SessionManager instance
            stop_event: threading.Event used to stop background threads
            drivers: list of driver names for the dropdown
        """
        self.client = client
        self.manager = manager
        self.stop_event = stop_event

        # Tkinter root
        self.root = tk.Tk()
        self.root.title("PDR Stint Logger")
        self.root.geometry("400x175")
        self.root.resizable(False, False)
        self.root.configure(bg="#2b2b2b")

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Build UI
        self._build_ui(drivers)

        # Start polling status
        self.update_status()

    def _build_ui(self, drivers):
        # --- Top bar ---
        self.top_bar = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=15)
        self.top_bar.pack(fill="x")

        # iRacing connection
        tk.Label(
            self.top_bar, text="iRacing:", bg="#1e1e1e", fg="white", font=("Arial", 12)
        ).pack(side="left", padx=(0, 5))
        self.iracing_canvas = tk.Canvas(
            self.top_bar, width=20, height=20, bg="#1e1e1e", highlightthickness=0
        )
        self.iracing_circle = self.iracing_canvas.create_oval(
            2, 2, 18, 18, fill="orange"
        )
        self.iracing_canvas.pack(side="left", padx=(0, 15))

        # API connection
        tk.Label(
            self.top_bar, text="API:", bg="#1e1e1e", fg="white", font=("Arial", 12)
        ).pack(side="left", padx=(0, 5))
        self.api_canvas = tk.Canvas(
            self.top_bar, width=20, height=20, bg="#1e1e1e", highlightthickness=0
        )
        self.api_circle = self.api_canvas.create_oval(2, 2, 18, 18, fill="orange")
        self.api_canvas.pack(side="left", padx=(0, 15))

        # Driver dropdown
        self.selected_driver = tk.StringVar(value=drivers[0])
        self.driver_dropdown = ttk.Combobox(
            self.top_bar,
            values=drivers,
            textvariable=self.selected_driver,
            state="readonly",
        )
        self.driver_dropdown.pack(side="right", padx=10)

        # Dark style for dropdown
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground="#2b2b2b",
            background="#1e1e1e",
            foreground="white",
            arrowcolor="white",
        )

        # Main status label
        self.status_label = tk.Label(
            self.root,
            text="Waiting for connections...",
            font=("Arial", 14),
            fg="white",
            bg="#2b2b2b",
        )
        self.status_label.pack(expand=True)

    def update_status(self):
        """Polls the client and manager for connection states and updates the GUI"""
        api_connected = getattr(self.client, "connected", False)
        iracing_connected = getattr(self.manager, "connected", False)

        # Update indicator colors
        self.api_canvas.itemconfig(
            self.api_circle, fill="green" if api_connected else "orange"
        )
        self.iracing_canvas.itemconfig(
            self.iracing_circle, fill="green" if iracing_connected else "orange"
        )

        # Update status label
        if iracing_connected and api_connected:
            self.status_label.config(text="Connected to iRacing and API!")
        elif iracing_connected:
            self.status_label.config(text="Connected to iRacing... Waiting for API")
        elif api_connected:
            self.status_label.config(text="Connected to API... Waiting for iRacing")
        else:
            self.status_label.config(text="Waiting for connections...")

        # Continue polling if GUI still running
        if not self.stop_event.is_set():
            self.root.after(500, self.update_status)

    def on_close(self):
        """Called when the user closes the window"""
        self.stop_event.set()  # signal background threads to stop
        self.root.destroy()  # close GUI

    def run(self):
        """Start the Tkinter main loop"""
        self.root.mainloop()
