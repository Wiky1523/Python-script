"""
data_cleaner.py
----------------
批量 CSV 数据清洗工具：自动完成去重、空值处理、列名标准化、类型推断。
依赖：pip install pandas openpyxl

用法示例：
    # 清洗单个文件
    python data_cleaner.py --input dirty.csv

    # 批量清洗一个目录下所有 CSV
    python data_cleaner.py --input ./raw_data/ --out-dir ./clean_data/

    # 自定义：只保留指定列，空值用 0 填充
    python data_cleaner.py --input data.csv --keep "姓名,年龄,城市" --fill-num 0
"""

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("❌ 缺少依赖，请先执行：pip install pandas openpyxl")


# ── 核心清洗函数 ──────────────────────────────────────────────────────────

def clean_df(df: pd.DataFrame,
             keep_cols: list[str] | None,
             fill_str: str,
             fill_num: float | None) -> tuple[pd.DataFrame, dict]:
    """
    对 DataFrame 执行一套标准清洗流程，返回清洗后的 df 及统计报告。
    """
    report = {}
    original_rows = len(df)
    original_cols = list(df.columns)

    # 1. 列名标准化：去首尾空格、统一小写（可按需注释掉小写部分）
    df.columns = [str(c).strip() for c in df.columns]
    report["列名标准化"] = "✔ 已去除列名首尾空格"

    # 2. 只保留指定列
    if keep_cols:
        missing = [c for c in keep_cols if c not in df.columns]
        if missing:
            print(f"  ⚠️  以下列不存在，已跳过：{missing}")
        df = df[[c for c in keep_cols if c in df.columns]]
        report["列筛选"] = f"保留 {list(df.columns)}"

    # 3. 删除完全重复行
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    report["去重"] = f"删除重复行 {removed} 行"

    # 4. 删除全为空的行与列
    df = df.dropna(how="all")                   # 全空行
    df = df.dropna(axis=1, how="all")           # 全空列
    report["删全空行/列"] = "✔"

    # 5. 空值填充
    num_cols = df.select_dtypes(include="number").columns.tolist()
    str_cols = df.select_dtypes(exclude="number").columns.tolist()

    if fill_num is not None:
        df[num_cols] = df[num_cols].fillna(fill_num)
        report["数值空值填充"] = f"用 {fill_num} 填充"
    else:
        df[num_cols] = df[num_cols].fillna(df[num_cols].median())
        report["数值空值填充"] = "用各列中位数填充"

    df[str_cols] = df[str_cols].fillna(fill_str)
    report["字符串空值填充"] = f'用 "{fill_str}" 填充'

    # 6. 去除字符串列的首尾空格
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
    report["字符串去空格"] = "✔"

    # 7. 自动推断更精确的类型（如把 "123" 转为 int）
    df = df.infer_objects()
    report["类型推断"] = "✔"

    report["行数变化"] = f"{original_rows} → {len(df)}"
    report["列数变化"] = f"{len(original_cols)} → {len(df.columns)}"
    return df, report


def print_report(filename: str, report: dict) -> None:
    print(f"\n  📊 清洗报告 [{filename}]")
    for k, v in report.items():
        print(f"     {k}: {v}")


# ── 文件级处理 ────────────────────────────────────────────────────────────

def process_file(in_path: Path,
                 out_path: Path,
                 keep_cols: list[str] | None,
                 fill_str: str,
                 fill_num: float | None) -> None:
    # 自动检测编码读取 CSV
    df = None
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb2312"):
        try:
            df = pd.read_csv(in_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        print(f"  ❌ 无法读取：{in_path.name}")
        return

    df_clean, report = clean_df(df, keep_cols, fill_str, fill_num)
    print_report(in_path.name, report)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  💾 已保存 → {out_path}")


# ── 入口 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="批量 CSV 数据清洗工具")
    parser.add_argument("--input",   required=True,  help="输入文件或目录")
    parser.add_argument("--out-dir", default=None,   help="输出目录（默认在原文件旁生成 _clean 后缀）")
    parser.add_argument("--keep",    default=None,   help="只保留的列名，英文逗号分隔，如 '姓名,年龄'")
    parser.add_argument("--fill-str",default="未知",  help="字符串列空值填充内容（默认：未知）")
    parser.add_argument("--fill-num",default=None,   type=float,
                        help="数值列空值填充值（默认用各列中位数）")
    args = parser.parse_args()

    in_path  = Path(args.input).expanduser().resolve()
    keep_cols = [c.strip() for c in args.keep.split(",")] if args.keep else None

    # ── 单文件模式
    if in_path.is_file():
        if in_path.suffix.lower() != ".csv":
            print("❌ 目前仅支持 CSV 文件")
            return
        out_dir  = Path(args.out_dir).expanduser().resolve() if args.out_dir else in_path.parent
        out_path = out_dir / (in_path.stem + "_clean.csv")
        print(f"\n🚀 清洗文件：{in_path.name}")
        process_file(in_path, out_path, keep_cols, args.fill_str, args.fill_num)

    # ── 批量目录模式
    elif in_path.is_dir():
        csv_files = list(in_path.glob("*.csv"))
        if not csv_files:
            print(f"❌ 目录中没有找到 CSV 文件：{in_path}")
            return
        out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else in_path / "cleaned"
        print(f"\n🚀 批量清洗目录：{in_path}  共 {len(csv_files)} 个文件")
        for f in csv_files:
            out_path = out_dir / (f.stem + "_clean.csv")
            process_file(f, out_path, keep_cols, args.fill_str, args.fill_num)

    else:
        print(f"❌ 路径不存在：{in_path}")
        return

    print("\n✅ 全部清洗完成\n")


if __name__ == "__main__":
    main()
