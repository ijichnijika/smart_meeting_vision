"""
参会人员 CSV 名单解析与入库导入器。
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import List, Tuple, Union

from app.config import DB_PATH
from app.resource.db import get_connection
from app.src.common.logger import get_logger

logger = get_logger("csv_importer")


class CsvAttendeeImporter:
    """负责参会人员花名册文件的编码探测、表头映射与批量导入。"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def import_csv(
        self,
        meeting_id: int,
        file_path: Union[str, Path],
    ) -> Tuple[int, int, List[str]]:
        """批量解析参会人员 CSV 名单并导入数据库。

        返回: (成功导入人数, 拦截重复人数, 重复工号列表)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {file_path}")

        content = None
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError("无法解析 CSV 文件编码，请确保文件为 UTF-8 或 GBK 格式。")

        reader = csv.reader(io.StringIO(content.strip()))
        rows = list(reader)
        if not rows:
            return 0, 0, []

        headers = [h.strip() for h in rows[0]]

        def find_col(*aliases):
            for idx, h in enumerate(headers):
                if h.lower() in aliases:
                    return idx
            return -1

        id_idx = find_col("工号", "employee_id", "学号", "id")
        name_idx = find_col("姓名", "name", "参会人")
        dept_idx = find_col("部门", "department", "所属部门", "班级")
        role_idx = find_col("职位", "role", "position", "职务")

        if id_idx == -1 or name_idx == -1 or dept_idx == -1:
            raise ValueError("CSV 格式不规范，缺少必要的表头列：工号、姓名、部门。")

        added_count = 0
        duplicate_ids: List[str] = []

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            for row in rows[1:]:
                if not row or len(row) <= max(id_idx, name_idx, dept_idx):
                    continue
                emp_id = row[id_idx].strip()
                name = row[name_idx].strip()
                dept = row[dept_idx].strip()
                role = row[role_idx].strip() if role_idx != -1 and len(row) > role_idx else "参会成员"

                if not emp_id or not name:
                    continue

                cursor.execute("SELECT id FROM attendees WHERE employee_id = ?", (emp_id,))
                existing = cursor.fetchone()

                if existing:
                    att_db_id = existing[0]
                    cursor.execute(
                        "SELECT id FROM check_in_records WHERE meeting_id = ? AND attendee_id = ?",
                        (meeting_id, att_db_id),
                    )
                    if cursor.fetchone():
                        duplicate_ids.append(emp_id)
                        continue
                    else:
                        cursor.execute(
                            "INSERT INTO check_in_records (meeting_id, attendee_id, status) VALUES (?, ?, 'absent')",
                            (meeting_id, att_db_id),
                        )
                        added_count += 1
                else:
                    cursor.execute(
                        "INSERT INTO attendees (employee_id, name, department, position) VALUES (?, ?, ?, ?)",
                        (emp_id, name, dept, role),
                    )
                    att_db_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO check_in_records (meeting_id, attendee_id, status) VALUES (?, ?, 'absent')",
                        (meeting_id, att_db_id),
                    )
                    added_count += 1

                cursor.execute(
                    """
                    UPDATE meetings
                    SET expected_count = (SELECT COUNT(*) FROM check_in_records WHERE meeting_id = ?)
                    WHERE id = ?
                    """,
                    (meeting_id, meeting_id),
                )

            logger.info(f"CSV 名单导入完成: 新增 {added_count} 人, 拦截重复 {len(duplicate_ids)} 人 ({duplicate_ids})")
            return added_count, len(duplicate_ids), duplicate_ids
