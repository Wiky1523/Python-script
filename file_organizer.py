"""
file_organizer.py
-----------------
批量文件整理工具：扫描指定目录，按文件类型或修改日期自动归类。

用法示例：
    python file_organizer.py --src ~/Downloads --mode type
    python file_organizer.py --src ~/Downloads --mode date --dry-run
"""

import argparse
import shutil
from pathlib import Path
from datetime import datetime

# ── 文件类型映射表（可自行扩展）────────────────────────────────────────
TYPE_MAP = {
    "图片":    [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".heic"],
    "文档":    [".pdf", ".docx", ".doc", ".txt", ".md", ".pptx", ".xlsx", ".csv"],
    "音频":    [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"],
    "视频":    [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
    "代码":    [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".sh"],
    "压缩包":  [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "字体":    [".ttf", ".otf", ".woff", ".woff2"],
}


def get_type_folder(suffix: str) -> str:
    """根据后缀返回分类文件夹名，未匹配到则归入「其他」"""
    suffix = suffix.lower()
    for folder, exts in TYPE_MAP.items():
        if suffix in exts:
            return folder
    return "其他"


def organize_by_type(src: Path, dst: Path, dry_run: bool) -> None:
    """按文件类型归类"""
    files = [f for f in src.rglob("*") if f.is_file()]
    print(f"\n📂 共扫描到 {len(files)} 个文件\n")

    moved = 0
    for file in files:
        folder_name = get_type_folder(file.suffix)
        target_dir = dst / folder_name
        target_path = target_dir / file.name

        # 同名文件自动加序号避免覆盖
        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{file.stem}_{counter}{file.suffix}"
            counter += 1

        print(f"  {'[预览]' if dry_run else '[移动]'} {file.name}  →  {folder_name}/")

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file), str(target_path))
            moved += 1

    summary = f"\n✅ 预览完成（共 {len(files)} 个文件）" if dry_run else f"\n✅ 整理完成，已移动 {moved} 个文件"
    print(summary)


def organize_by_date(src: Path, dst: Path, dry_run: bool) -> None:
    """按修改日期（YYYY-MM）归类"""
    files = [f for f in src.rglob("*") if f.is_file()]
    print(f"\n📂 共扫描到 {len(files)} 个文件\n")

    moved = 0
    for file in files:
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        folder_name = mtime.strftime("%Y-%m")          # e.g. 2025-03
        target_dir = dst / folder_name
        target_path = target_dir / file.name

        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{file.stem}_{counter}{file.suffix}"
            counter += 1

        print(f"  {'[预览]' if dry_run else '[移动]'} {file.name}  →  {folder_name}/")

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file), str(target_path))
            moved += 1

    summary = f"\n✅ 预览完成（共 {len(files)} 个文件）" if dry_run else f"\n✅ 整理完成，已移动 {moved} 个文件"
    print(summary)


def main():
    parser = argparse.ArgumentParser(description="批量文件整理工具")
    parser.add_argument("--src",     required=True,        help="源目录路径")
    parser.add_argument("--dst",     default=None,         help="目标目录路径（默认与源目录相同）")
    parser.add_argument("--mode",    choices=["type", "date"], default="type",
                        help="整理模式：type=按类型  date=按日期（默认 type）")
    parser.add_argument("--dry-run", action="store_true",  help="预览模式，不实际移动文件")
    args = parser.parse_args()

    src = Path(args.src).expanduser().resolve()
    dst = Path(args.dst).expanduser().resolve() if args.dst else src

    if not src.exists():
        print(f"❌ 源目录不存在：{src}")
        return

    print(f"源目录：{src}")
    print(f"目标目录：{dst}")
    print(f"整理模式：{'按文件类型' if args.mode == 'type' else '按修改日期'}")
    if args.dry_run:
        print("⚠️  预览模式 — 不会实际移动文件")

    if args.mode == "type":
        organize_by_type(src, dst, args.dry_run)
    else:
        organize_by_date(src, dst, args.dry_run)


if __name__ == "__main__":
    main()
