# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "xlrd"]
# ///
"""把 114-1 在學人數統計表 (.xls) 轉成整齊的 CSV：系所 x 學制 x 性別。"""
import glob
import re
from pathlib import Path

import pandas as pd
import xlrd

ROOT = Path(__file__).resolve().parent.parent
SRC = glob.glob(str(ROOT / "東華大學統計資料" / "在學人數統計表" / "114-1*.xls"))[0]
OUT = ROOT / "work" / "enrollment_114-1.csv"

# 學制區塊標題（第 0 欄「xxx 合計N」）-> 標準學制名稱
PROGRAMS = {"博士班": "博士班", "碩士班": "碩士班", "碩專班": "碩士在職專班", "學士班": "學士班"}
COL_COLLEGE, COL_DEPT, COL_COUNT_F, COL_COUNT_M = 1, 2, 5, 6


def clean(v):
    return None if pd.isna(v) else str(v).strip()


df = pd.read_excel(SRC, sheet_name=0, header=None)

# 系所欄（第 2 欄）實際被合併儲存格涵蓋的列；r2 為不含的結尾
merged_rows = set()
for r1, r2, c1, c2 in xlrd.open_workbook(SRC, formatting_info=True).sheet_by_index(0).merged_cells:
    if c1 <= COL_DEPT < c2:
        merged_rows.update(range(r1, r2))

rows = []
program = college = dept = None
for i, r in df.iloc[3:].iterrows():
    head = clean(r[0])
    if head and head.startswith("備註"):
        break
    if head and "合計" in head:  # 學制區塊標題列（含人數合計），只用來切換學制
        program = PROGRAMS[head.split()[0]]
        college = dept = None
        continue
    # 合併儲存格：只有範圍第一格有值，其餘為空 -> 往下沿用
    if clean(r[COL_COLLEGE]):
        college = re.sub(r"[（(].*?[)）]", "", clean(r[COL_COLLEGE])).strip()
    if clean(r[COL_DEPT]):
        dept = clean(r[COL_DEPT])
    elif i not in merged_rows and not pd.isna(r[COL_COUNT_F]):
        # 系所欄空白、又不在任何合併範圍內（例如 114-1 物理學系博士班第一列，
        # 名稱被寫在下一列）：該列屬於下一個出現的系所，不能沿用上一個系所
        dept = next(clean(v) for v in df.loc[i + 1:, COL_DEPT] if clean(v))
    if pd.isna(r[COL_COUNT_F]) and pd.isna(r[COL_COUNT_M]):
        continue
    for gender, col in (("女", COL_COUNT_F), ("男", COL_COUNT_M)):
        rows.append((college, dept, program, gender, int(r[col])))

out = (
    pd.DataFrame(rows, columns=["college", "dept_raw", "program_raw", "gender", "count"])
    .groupby(["college", "dept_raw", "program_raw", "gender"], sort=False, as_index=False)["count"]
    .sum()  # 同系所同學制的多個分組加總
)
out.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"寫出 {len(out)} 列，人數合計 {out['count'].sum()} -> {OUT}")
