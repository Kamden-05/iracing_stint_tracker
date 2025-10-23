import tkinter as tk
from tkinter import ttk


class StintTrackerGUI:
    def __init__(self, client, manager, stop_event, driver_name):
        """
        Args:
            client: APIClient instance (backend)
            manager: SessionManager instance (backend)
            stop_event: threading.Event used to signal shutdown
            driver_name: string, name of the driver to display
        """
        self.client = client
        self.manager = manager
        self.stop_event = stop_event
        self.driver_name = driver_name

        # Tkinter root
        self.root = tk.Tk()
        self.root.title(f"PDR Stint Logger - {self.driver_name}")
        self.root.geometry("400x175")
        self.root.resizable(False, False)
        self.root.configure(bg="#2b2b2b")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Build the dashboard UI
        self._build_dashboard()

        # Start polling connection status
        self.update_status()

    # ---------------- Dashboard GUI ----------------
    def _build_dashboard(self):
        """Builds the top bar and main status label"""
        self.top_bar = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=15)
        self.top_bar.pack(fill="x")

        # iRacing indicator
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

        # API indicator
        tk.Label(
            self.top_bar, text="API:", bg="#1e1e1e", fg="white", font=("Arial", 12)
        ).pack(side="left", padx=(0, 5))
        self.api_canvas = tk.Canvas(
            self.top_bar, width=20, height=20, bg="#1e1e1e", highlightthickness=0
        )
        self.api_circle = self.api_canvas.create_oval(2, 2, 18, 18, fill="orange")
        self.api_canvas.pack(side="left", padx=(0, 15))

        # Driver label
        tk.Label(
            self.top_bar,
            text=f"Driver: {self.driver_name}",
            bg="#1e1e1e",
            fg="white",
            font=("Arial", 12),
        ).pack(side="right", padx=10)

        # Main status label
        self.status_label = tk.Label(
            self.root,
            text="Waiting for connections...",
            font=("Arial", 14),
            fg="white",
            bg="#2b2b2b",
        )
        self.status_label.pack(expand=True)

    # ---------------- GUI update loop ----------------
    def update_status(self):
        """Poll backend threads for connection state and update indicators"""
        api_connected = getattr(self.client, "is_connected", False)
        iracing_connected = getattr(self.manager, "is_connected", False)

        # Update circle colors
        self.api_canvas.itemconfig(
            self.api_circle, fill="green" if api_connected else "orange"
        )
        self.iracing_canvas.itemconfig(
            self.iracing_circle, fill="green" if iracing_connected else "orange"
        )

        # Update main status label
        if api_connected and iracing_connected:
            self.status_label.config(text="Connected to iRacing")
        elif api_connected:
            self.status_label.config(text="Waiting for iRacing...")
        elif iracing_connected:
            self.status_label.config(text="Connecting to API...")
        else:
            self.status_label.config(text="Waiting for connections...")

        

        # Schedule next update
        if not self.stop_event.is_set():
            self.root.after(500, self.update_status)

    # ---------------- Shutdown ----------------
    def on_close(self):
        """Called when user closes the window"""
        self.stop_event.set()  # signal threads to stop
        self.root.destroy()

    # ---------------- Run GUI ----------------
    def run(self):
        self.root.mainloop()
