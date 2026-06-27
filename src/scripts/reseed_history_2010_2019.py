"""
reseed_history_2010_2019.py — Làm mới dữ liệu lịch sử 2010-2019 trong DB cho khớp
đúng tập training (features_*_v1.csv).

Lý do: một số DB được seed bằng load_db.py cũ (đã bỏ) với vintage cũ — raw_count
NULL, giá trị lệch, dengue phủ 2010-2019 thay vì 2015-2019. load_db_v2 dùng
ON CONFLICT DO NOTHING nên chạy lại không ghi đè được; phải xoá dòng 2010-2019 cũ
trước rồi nạp lại từ CSV.

KHÔNG đụng dữ liệu sync 2024+ (chỉ xoá đúng cửa sổ 2010-2019).
Chạy lại an toàn (idempotent): sau khi xoá + nạp, kết quả luôn bằng tập training.
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_db_v2 import connect, main as load_db_v2_main  # noqa: E402

YEAR_START = 2010
YEAR_END = 2019


def clear_stale_history():
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        # Xoá predictions trước (không có FK ràng buộc từ bảng khác trỏ tới),
        # rồi disease_cases. Chỉ trong cửa sổ 2010-2019.
        for table in ("predictions", "disease_cases"):
            cur.execute(
                f"DELETE FROM {table} WHERE iso_year BETWEEN %s AND %s",
                (YEAR_START, YEAR_END),
            )
            print(f"  Đã xoá {cur.rowcount:,} dòng cũ khỏi {table} (2010-2019)")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  reseed_history_2010_2019.py")
    print("=" * 60)
    print("\n[1] Xoá dữ liệu lịch sử stale 2010-2019...")
    clear_stale_history()
    print("\n[2] Nạp lại từ CSV training qua load_db_v2...")
    load_db_v2_main()
