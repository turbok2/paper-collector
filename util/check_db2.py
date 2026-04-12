import sqlite3
from pathlib import Path

DB_PATH = Path("paper.db")
UPLOAD_DIR = Path("uploaded")
TABLE_NAME = "c_info"
COLUMN_NAME = "JSON_FILE_NAME"


def normalize_name(name: str) -> str:
    """Normalize file names for comparison (basename + lowercase + trim)."""
    return Path(name).name.strip().lower()


def get_db_pdf_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT {COLUMN_NAME} FROM {TABLE_NAME}")
        rows = cur.fetchall()
    finally:
        conn.close()

    names = set()
    for (value,) in rows:
        if value is None:
            continue
        value = str(value).strip()
        if value:
            names.add(normalize_name(value))
    return names


def get_uploaded_pdf_names(upload_dir: Path) -> set[str]:
    if not upload_dir.exists() or not upload_dir.is_dir():
        raise FileNotFoundError(f"업로드 폴더를 찾을 수 없습니다: {upload_dir}")

    return {
        normalize_name(path.name)
        for path in upload_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".json"
    }


def print_list(title: str, values: list[str]) -> None:
    print(f"\n[{title}] ({len(values)}개)")
    if not values:
        print("- 없음")
        return
    for item in values:
        print(f"- {item}")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다: {DB_PATH}")

    db_names = get_db_pdf_names(DB_PATH)
    uploaded_names = get_uploaded_pdf_names(UPLOAD_DIR)

    only_in_db = sorted(db_names - uploaded_names)
    only_in_uploaded = sorted(uploaded_names - db_names)

    print(f"DB 파일: {DB_PATH}")
    print(f"테이블/컬럼: {TABLE_NAME}.{COLUMN_NAME}")
    print(f"업로드 폴더: {UPLOAD_DIR}")
    print(f"DB JSON 이름 수: {len(db_names)}")
    print(f"폴더 JSON 파일 수: {len(uploaded_names)}")

    print_list("DB에는 있고 uploaded에는 없는 파일", only_in_db)
    print_list("uploaded에는 있고 DB에는 없는 파일", only_in_uploaded)


if __name__ == "__main__":
    main()
