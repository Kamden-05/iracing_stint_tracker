from dataclasses import fields, asdict
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path
from src.models import Session, Stint, Lap, PitStop
import pandas as pd
import time

logger = logging.getLogger(__name__)


class ExcelExporter:
    def __init__(self):
        self.file_path: Optional[Path] = None
        self.stint_headers = [field.name for field in fields(Stint)]
        self.lap_headers = [field.name for field in fields(Lap)]
        self.pitstop_headers = [field.name for field in fields(PitStop)]

        self.current_dir: Path = Path(__file__).parent
        self.project_root: Path = self.current_dir.parent.parent
        self.MAX_AGE_DAYS = 30

    def delete_old_files(self):
        if not self.project_root.is_dir():
            logger.info("Root folder does not exist")
            return

        races_dir = self.project_root / "races"
        if not races_dir.is_dir():
            logger.info("Race directory not found")
            return

        files = races_dir.rglob("*.xlsx")
        max_age_seconds = self.MAX_AGE_DAYS * 86400
        now = time.time()

        for f in files:
            if f.stat().st_birthtime < now - max_age_seconds:
                try:
                    f.unlink()
                    logger.info("File deleted: %s", f.name)
                except FileNotFoundError as e:
                    logger.warning("File not found: %s", e)
                    continue

    def create_workbook(self, session: Session):
        track_name = str(session.track).replace(" ", "_").replace("/", "-")
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"{track_name}_{date}_{session.id}.xlsx"

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

        logger.info("Workbook created at %s", self.file_path)

    def update_sheet(self, obj: Session | Lap | PitStop | Stint, append: bool = False):
        if self.file_path is None:
            raise RuntimeError("Workbook not created yet. Call create_workbook first.")

        sheet_name = obj.__class__.__name__

        try:
            old_df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        except (FileNotFoundError, ValueError):
            logger.warning(
                "Sheet %s not found in %s",
                sheet_name,
                self.file_path,
            )
            old_df = pd.DataFrame()

        if not append and not old_df.empty:
            old_df = old_df.iloc[:-1]

        df = pd.DataFrame([asdict(obj)])

        combined_df = pd.concat([old_df, df], ignore_index=True)

        with pd.ExcelWriter(
            self.file_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
        ) as writer:
            combined_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info("Updated sheet %s now has %s rows", sheet_name, len(combined_df))
