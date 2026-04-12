import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("paper.db")
TABLE_NAME = "c_info"
OUTPUT_CSV = Path("cdata.csv")


def export_table_to_csv(db_path: Path, table_name: str, output_csv: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
    finally:
        conn.close()

    with output_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"저장 완료: {output_csv}")
    print(f"행 수: {len(rows)}")


def main() -> None:
    export_table_to_csv(DB_PATH, TABLE_NAME, OUTPUT_CSV)


if __name__ == "__main__":
    main()
