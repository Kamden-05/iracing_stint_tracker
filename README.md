# iRacing Stint Tracker (Python)

A lightweight Python desktop app that connects to the **iRacing SDK** and sends live race telemetry to the **iRacing Stint Tracker Backend**.  
Built with **Python** and **Tkinter** for a minimal GUI.

---

## Overview

The **iRacing Stint Tracker GUI** provides a simple interface to monitor live telemetry from iRacing and forward it to the backend.
It connects to the **[iRacing SDK](https://sajax.github.io/irsdkdocs/)** to capture telemetry data and automatically sends it to the **[iRacing Stint Tracker Backend](https://github.com/Kamden-05/stint-tracker-server)** for storage and analysis.

**Key features:**
- Connects to the iRacing SDK to capture live telemetry (laps, stints, pit stops, incidents, etc.).
- Sends data in real-time to the **backend API** for storage and analysis.
- Simple GUI displays:
  - Connection status to the iRacing SDK
  - Connection status to the backend API
- Designed for personal use by a single iRacing team, with plans to extend to multiple teams in the future.

**Future Plans:**
- Offline data exporting
- User/team authentication

**Known Issues**
- stints end prematurely if client temporarily disconnects from iRacing session

This app **does not include dashboards or visualizations**; its purpose is reliable data capture and transmission.

---

## Tech Stack

| Component  | Technology |
|------------|------------|
| Language   | Python 3.14 |
| GUI        | Tkinter |
| Backend    | iRacing Stint Tracker Backend (FastAPI + PostgreSQL) |
| SDK        | iRacing Python SDK |

---

## How It Works

1. Connects to the **iRacing SDK** to capture live telemetry.  
2. Displays connection status for both the SDK and the backend.  
3. Sends telemetry data in real-time to the backend API endpoints:
   - `POST /sessions` → create/update session
   - `POST /stints` → send stint data
   - `POST /laps` → send lap data
   - `POST /pitstops` → send pit stop events

---

## License

This project is licensed under the [MIT License](LICENSE).

