from dataclasses import fields, asdict
import logging
from datetime import datetime
from pathlib import Path
from src.models import Session, Stint, Lap, PitStop
import pandas as pd

logger = logging.getLogger(__name__)


class ExcelExporter:
    def __init__(self):
        self.file_path = ""
        self.stint_headers = [field.name for field in fields(Stint)]
        self.lap_headers = [field.name for field in fields(Lap)]
        self.pitstop_headers = [field.name for field in fields(PitStop)]

        self.current_dir = Path(__file__).parent
        self.project_root = self.current_dir.parent.parent

    def create_workbook(self, session: Session):
        track_name = str(session.track).replace(" ", "_").replace("/", "-")
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"{track_name}_{date}.xlsx"

        races_dir = self.project_root / "races"
        races_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = races_dir / file_name

        session_df = pd.DataFrame([asdict(session)])
        stint_df = pd.DataFrame(columns=self.stint_headers)
        lap_df = pd.DataFrame(columns=self.lap_headers)
        pitstop_df = pd.DataFrame(columns=self.pitstop_headers)

        with pd.ExcelWriter(self.file_path, engine="openpyxl") as writer:
            session_df.to_excel(writer, sheet_name="Session", index=False)
            stint_df.to_excel(writer, sheet_name="Stint", index=False)
            lap_df.to_excel(writer, sheet_name="Lap", index=False)
            pitstop_df.to_excel(writer, sheet_name="PitStop", index=False)

        logger.info(f"Workbook created at {self.file_path}")

    def update_sheet(self, obj: Session | Lap | PitStop | Stint, append: bool = False):
        sheet_name = obj.__class__.__name__

        old_df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        if not append:
            old_df = old_df.iloc[:-1]

        df = pd.DataFrame([asdict(obj)])

        combined_df = pd.concat([old_df, df], ignore_index=True)

        with pd.ExcelWriter(
            self.file_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
        ) as writer:
            combined_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Updated sheet {sheet_name}")
