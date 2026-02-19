from dataclasses import fields, asdict
from datetime import datetime
import os
from src.models import Session, Stint, Lap, PitStop
import pandas as pd


class ExcelExporter:
    def __init__(
        self,
        output_path: str = r"C:\Users\kmdnw\Projects\iRacing\iracing_stint_tracker\races",
    ):
        self.file_name = ""
        self.stint_headers = [field.name for field in fields(Stint)]
        self.lap_headers = [field.name for field in fields(Lap)]
        self.pitstop_headers = [field.name for field in fields(PitStop)]

        self.output_dir = output_path

    def create_workbook(self, session: Session):
        self.file_name = (
            str(session.id)
            + "_"
            + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            + ".xlsx"
        )

        self.file_path = os.path.join(self.output_dir, self.file_name)

        session_df = pd.DataFrame([asdict(session)])
        stint_df = pd.DataFrame(columns=self.stint_headers)
        lap_df = pd.DataFrame(columns=self.lap_headers)
        pitstop_df = pd.DataFrame(columns=self.pitstop_headers)

        with pd.ExcelWriter(self.file_path, engine="openpyxl") as writer:
            session_df.to_excel(writer, sheet_name="Session", index=False)
            stint_df.to_excel(writer, sheet_name="Stint", index=False)
            lap_df.to_excel(writer, sheet_name="Lap", index=False)
            pitstop_df.to_excel(writer, sheet_name="PitStop", index=False)

    def update_sheet(self, obj: Session | Lap | PitStop | Stint):
        sheet_name = obj.__class__.__name__
        old_df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        df = pd.DataFrame([asdict(obj)])
        combined_df = pd.concat([old_df, df], ignore_index=True)

        with pd.ExcelWriter(
            self.file_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
        ) as writer:
            combined_df.to_excel(writer, sheet_name=sheet_name, index=False)
