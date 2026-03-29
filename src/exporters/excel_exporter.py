from dataclasses import fields, asdict
import logging
from datetime import datetime
import os
from src.models import Session, Stint, Lap, PitStop
import pandas as pd

logger = logging.getLogger(__name__)


class ExcelExporter:
    def __init__(self):
        self.file_path = ""
        self.stint_headers = [field.name for field in fields(Stint)]
        self.lap_headers = [field.name for field in fields(Lap)]
        self.pitstop_headers = [field.name for field in fields(PitStop)]

        self.current_dir = os.path.dirname(__file__)
        self.project_root = os.path.abspath(
            os.path.join(self.current_dir, os.pardir, os.pardir)
        )

    def create_workbook(self, session: Session):
        file_name = (
            str(session.track)
            + "_"
            + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            + ".xlsx"
        )

        races_dir = os.path.join(self.project_root, "races")
        os.makedirs(races_dir, exist_ok=True)

        self.file_path = os.path.join(races_dir, file_name)

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
