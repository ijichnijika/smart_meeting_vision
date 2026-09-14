"""
考勤与出勤分析报表导出服务。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import pandas as pd

from app.config import REPORTS_DIR
from app.src.common.logger import get_logger
from app.src.model import Attendee

logger = get_logger("export_service")


class AttendanceReportService:
    """负责将参会出勤数据格式化并持久化导出为 Excel 报表。"""

    @staticmethod
    def export_to_excel(attendees: List[Attendee], export_path: Optional[Path] = None) -> Path:
        """导出参会人员出勤记录至 .xlsx 报表文件。"""
        if export_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"考勤出勤分析报表_{ts}.xlsx"
            export_path = REPORTS_DIR / file_name

        export_path.parent.mkdir(parents=True, exist_ok=True)

        records = [
            {
                "工号": a.id,
                "姓名": a.name,
                "所属部门": a.department,
                "职位": a.role,
                "当前状态": "在席" if a.status == "present" else "离席",
                "关联追踪编号": a.track_id or "未关联",
                "分心次数": a.distraction_count,
                "出勤核定": "准时参会" if a.status == "present" else "缺席",
            }
            for a in attendees
        ]

        df = pd.DataFrame(records)
        df.to_excel(str(export_path), index=False, engine="openpyxl")
        logger.info(f"考勤出勤分析报表已导出: {export_path}")
        return export_path
