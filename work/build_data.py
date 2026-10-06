# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
# ///
"""把 data/ 的三個 CSV 整理成網頁可直接載入的 docs/data.js（window.BI_DATA）。"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
read = lambda name: pd.read_csv(ROOT / "data" / name, encoding="utf-8-sig", keep_default_na=False)

enr = read("enrollment.csv")
leave = read("leave.csv")
mapping = read("dept_mapping.csv")

# 只保留網頁用到的欄位並先加總（college 以 114-1 組織為準，dept 為標準名稱）
KEY = ["semester", "college", "dept", "degree", "gender"]
enr = enr.groupby(KEY, as_index=False)["count"].sum()
leave = leave.groupby(KEY + ["reason"], as_index=False)[["new_leave", "on_leave_end"]].sum()

def table(df):
    return {"columns": list(df.columns), "rows": df.values.tolist()}

depts = [
    {"dept": r.dept, "college": r.college, "aliases": [a for a in r.aliases.split(";") if a]}
    for r in mapping.itertuples()
]

data = {
    "semesters": sorted(enr["semester"].unique().tolist()),
    "enrollment": table(enr),  # count = 在學人數
    "leave": table(leave),     # new_leave = 學期間休學；on_leave_end = 學期底休學狀態
    "depts": depts,            # 系所標準名稱、學院、舊名稱
}

out = ROOT / "docs" / "data.js"
out.write_text("window.BI_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

# 核對
print("enrollment 114-1 合計：", int(enr[enr.semester == "114-1"]["count"].sum()))
print("enrollment 列數：", len(enr), "；leave 列數：", len(leave), "；系所數：", len(depts))
print("休學 new_leave 總計：", int(leave.new_leave.sum()), "；on_leave_end 總計：", int(leave.on_leave_end.sum()))
print("data.js 大小：", out.stat().st_size, "bytes")
