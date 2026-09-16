"""
会议信息管理与 SQLite 持久化层单元测试。
"""

import os
import sqlite3
from pathlib import Path
import pytest

from app.src.model.models import MeetingInfo, Attendee
from app.resource.db import get_connection, init_database
from app.src.service.db_service import (
    get_active_meeting,
    save_meeting,
    get_attendees,
)

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_init_database_and_tables(tmp_path: Path):
    db_file = tmp_path / "test_vision.db"
    init_database(db_file)

    assert db_file.exists()
    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            "meetings",
            "attendees",
            "check_in_records",
            "distraction_events",
            "seat_zones",
        }
        assert expected_tables.issubset(tables)


def test_default_meeting_creation_and_retrieval(tmp_path: Path):
    db_file = tmp_path / "test_vision.db"
    init_database(db_file)

    meeting = get_active_meeting(db_file)
    assert meeting.id is not None
    assert "软件工程" in meeting.title
    assert meeting.host == "夏一帆"
    assert meeting.department == "研发中心"
    assert meeting.total_expected == 12


def test_save_and_update_meeting(tmp_path: Path):
    db_file = tmp_path / "test_vision.db"
    init_database(db_file)

    meeting = get_active_meeting(db_file)
    meeting.title = "2026年第三季度人工智能研讨会"
    meeting.host_name = "张工程师"
    meeting.department = "视觉算法部"
    meeting.status = "completed"

    saved = save_meeting(meeting, db_file)
    assert saved.title == "2026年第三季度人工智能研讨会"

    reloaded = get_active_meeting(db_file)
    assert reloaded.title == "2026年第三季度人工智能研讨会"
    assert reloaded.host == "张工程师"
    assert reloaded.department == "视觉算法部"
    assert reloaded.status == "completed"


def test_get_attendees_from_db(tmp_path: Path):
    db_file = tmp_path / "test_vision.db"
    init_database(db_file)

    meeting = get_active_meeting(db_file)
    attendees = get_attendees(meeting.id, db_file)

    assert len(attendees) == 12
    assert attendees[0].id == "EMP001"
    assert attendees[0].name == "夏一帆"
    assert attendees[0].status == "present"


def test_database_viewer_dialog(tmp_path: Path):
    from app.src.ui.components.db_dialog import DatabaseViewerDialog

    db_file = tmp_path / "test_vision.db"
    init_database(db_file)

    dlg = DatabaseViewerDialog(db_path=db_file)
    assert dlg.table_widget.rowCount() > 0
    assert dlg.table_widget.columnCount() > 0

    # 切换到参会人员表
    dlg.combo_tables.setCurrentIndex(1)
    assert dlg.table_widget.rowCount() == 12

    # 测试即时搜索过滤
    dlg.search_input.setText("夏一帆")
    assert not dlg.table_widget.isRowHidden(0)
    assert dlg.table_widget.isRowHidden(1)
    assert "匹配 1 / 12 条" in dlg.lbl_count.text()

    dlg.search_input.setText("")
    assert not dlg.table_widget.isRowHidden(1)
    assert "共 12 条记录" in dlg.lbl_count.text()
    dlg.close()


def test_meeting_edit_dialog(tmp_path: Path):
    from app.src.ui.components.meeting_dialog import MeetingEditDialog

    db_file = tmp_path / "test_vision.db"
    init_database(db_file)
    meeting = get_active_meeting(db_file)

    dlg = MeetingEditDialog(meeting)
    dlg.input_title.setText("智能感知算法答辩评审会")
    dlg.input_room.setText("第二学术报告厅")
    dlg._on_save()

    assert meeting.title == "智能感知算法答辩评审会"
    assert meeting.room == "第二学术报告厅"
    dlg.close()


def test_import_attendees_csv(tmp_path: Path):
    from app.src.service.db_service import import_attendees_csv

    db_file = tmp_path / "test_vision.db"
    init_database(db_file)
    meeting = get_active_meeting(db_file)
    assert meeting.expected_count == 12

    # 创建测试 CSV 文件 (包含 1 个重复人员 EMP001 和 2 个新人员)
    csv_file = tmp_path / "test_roster.csv"
    csv_file.write_text(
        "工号,姓名,部门,职位\n"
        "EMP001,夏一帆,研发一部,项目负责人\n"
        "EMP020,周华健,研发三部,高级开发\n"
        "EMP021,王菲,音频算法部,科学家\n",
        encoding="utf-8",
    )

    added, dups, dup_list = import_attendees_csv(meeting.id, csv_file, db_file)
    assert added == 2
    assert dups == 1
    assert dup_list == ["EMP001"]

    # 验证人员名单数量与会议应到人数更新
    attendees = get_attendees(meeting.id, db_file)
    assert len(attendees) == 14
    updated_meeting = get_active_meeting(db_file)
    assert updated_meeting.expected_count == 14


def test_import_attendees_csv_gbk_and_validation(tmp_path: Path):
    from app.src.service.db_service import import_attendees_csv

    db_file = tmp_path / "test_vision.db"
    init_database(db_file)
    meeting = get_active_meeting(db_file)

    # 测试 GBK 编码解析兼容
    gbk_file = tmp_path / "gbk_roster.csv"
    gbk_file.write_bytes("工号,姓名,部门\nEMP099,李四,市场部\n".encode("gbk"))

    added, dups, _ = import_attendees_csv(meeting.id, gbk_file, db_file)
    assert added == 1
    assert dups == 0

    # 测试格式校验与缺失列拦截
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("姓名,性别,年龄\n张三,男,25\n", encoding="utf-8")
    with pytest.raises(ValueError, match="缺少必要的表头列"):
        import_attendees_csv(meeting.id, bad_csv, db_file)


def test_meeting_crud_backend(tmp_path: Path):
    from app.src.service.db_service import (
        delete_meeting,
        get_all_meetings,
        get_meeting_by_id,
        save_meeting,
    )

    db_file = tmp_path / "test_vision.db"
    init_database(db_file)

    # 1. 查询所有
    all_meetings = get_all_meetings(db_file)
    assert len(all_meetings) == 1

    # 2. 新增会议 (Create)
    new_m = MeetingInfo(
        id=0,
        title="测试自动化答辩会议",
        department="测试部",
        host_name="测试员",
        start_time="2026-09-10 14:00:00",
        end_time="2026-09-10 16:00:00",
        expected_count=8,
        status="scheduled",
    )
    created = save_meeting(new_m, db_file)
    assert created.id > 1
    assert len(get_all_meetings(db_file)) == 2

    # 3. 按 ID 查询 (Read)
    retrieved = get_meeting_by_id(created.id, db_file)
    assert retrieved is not None
    assert retrieved.title == "测试自动化答辩会议"

    # 4. 修改会议 (Update)
    retrieved.title = "已更名测试会议"
    retrieved.status = "completed"
    save_meeting(retrieved, db_file)
    updated = get_meeting_by_id(created.id, db_file)
    assert updated.title == "已更名测试会议"
    assert updated.status == "completed"

    # 5. 删除会议 (Delete)
    assert delete_meeting(created.id, db_file) is True
    assert get_meeting_by_id(created.id, db_file) is None
    assert len(get_all_meetings(db_file)) == 1


def test_meeting_manager_dialog(tmp_path: Path):
    from app.src.ui.components.meeting_dialog import MeetingManagerDialog

    db_file = tmp_path / "test_vision.db"
    init_database(db_file)
    meeting = get_active_meeting(db_file)

    dlg = MeetingManagerDialog(current_meeting_id=meeting.id, db_path=db_file)
    assert dlg.table.rowCount() == 1
    assert "★" in dlg.table.item(0, 1).text()  # 当前活动会议标记

    # 测试新建会议
    new_m = MeetingInfo(
        id=0,
        title="技术研讨交流会",
        department="软件中心",
        host_name="李四",
        start_time="2026-09-12 09:00:00",
        end_time="2026-09-12 11:00:00",
        expected_count=10,
        status="in_progress",
    )
    save_meeting(new_m, db_file)
    dlg.load_meetings()
    assert dlg.table.rowCount() == 2

    # 测试即时搜索
    dlg.search_input.setText("研讨")
    assert not dlg.table.isRowHidden(0)
    assert dlg.table.isRowHidden(1)
    dlg.search_input.setText("")

    dlg.close()



