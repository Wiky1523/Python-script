"""
format_converter.py
--------------------
数据格式转换工具：支持 CSV / JSON / Excel(.xlsx) 三种格式互转。
依赖：pip install pandas openpyxl

用法示例：
    python format_converter.py --input data.csv   --to json
    python format_converter.py --input data.json  --to xlsx
    python format_converter.py --input data.xlsx  --to csv   --sheet Sheet1
    python format_converter.py --input data.csv   --to json  --output result.json
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("❌ 缺少依赖，请先执行：pip install pandas openpyxl")


# ── 读取函数 ────────────────────────────────────────────────────────────

def read_file(path: Path, sheet: str | None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        # 自动检测编码（优先 utf-8-sig 兼容带 BOM 的 Excel 导出文件）
        for enc in ("utf-8-sig", "utf-8", "gbk", "gb2312"):
            try:
                df = pd.read_csv(path, encoding=enc)
                print(f"  编码：{enc}")
                return df
            except UnicodeDecodeError:
                continue
        raise ValueError("无法识别文件编码，请手动指定编码后重试")

    elif suffix == ".json":
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        # 支持两种 JSON 结构：列表 或 {records: [...]}
        if isinstance(raw, list):
            return pd.DataFrame(raw)
        elif isinstance(raw, dict):
            # 取第一个值为列表的键
            for v in raw.values():
                if isinstance(v, list):
                    return pd.DataFrame(v)
        raise ValueError("JSON 结构不支持，需为数组或含数组字段的对象")

    elif suffix in (".xlsx", ".xls"):
        sheet_name = sheet or 0
        df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
        print(f"  Sheet：{sheet_name}")
        return df

    else:
        raise ValueError(f"不支持的输入格式：{suffix}")


# ── 写出函数 ────────────────────────────────────────────────────────────

def write_file(df: pd.DataFrame, out_path: Path) -> None:
    suffix = out_path.suffix.lower()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if suffix == ".csv":
        df.to_csv(out_path, index=False, encoding="utf-8-sig")  # utf-8-sig 让 Excel 正常打开

    elif suffix == ".json":
        records = df.to_dict(orient="records")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    elif suffix in (".xlsx", ".xls"):
        df.to_excel(out_path, index=False, engine="openpyxl")

    else:
        raise ValueError(f"不支持的输出格式：{suffix}")


# ── 主逻辑 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CSV / JSON / Excel 格式互转工具")
    parser.add_argument("--input",  required=True,                         help="输入文件路径")
    parser.add_argument("--to",     required=True, choices=["csv","json","xlsx"], help="目标格式")
    parser.add_argument("--output", default=None,                          help="输出文件路径（默认同名换后缀）")
    parser.add_argument("--sheet",  default=None,                          help="Excel Sheet 名称（仅读取 xlsx 时有效）")
    args = parser.parse_args()

    in_path  = Path(args.input).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else \
               in_path.with_suffix("." + args.to)

    if not in_path.exists():
        print(f"❌ 输入文件不存在：{in_path}")
        return

    print(f"\n📄 读取：{in_path.name}")
    df = read_file(in_path, args.sheet)
    print(f"  行数：{len(df)}  列数：{len(df.columns)}")
    print(f"  列名：{list(df.columns)}")

    print(f"\n💾 写出：{out_path.name}")
    write_file(df, out_path)

    print(f"\n✅ 转换完成 → {out_path}\n")


if __name__ == "__main__":
    main()
