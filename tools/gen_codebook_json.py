#!/usr/bin/env python3
"""Maak components/remeha_confida/codebook.json uit data/Remeha_parametercodeboek.xlsx.

De component gebruikt dit bestand alleen bij het compileren (niet op de ESP), om
een entiteit met alleen `code: HM001` automatisch in te vullen: index, subindex,
datatype, gain, eenheid, naam en (bij enums) de keuzeteksten.

Gebruik (vanuit de hoofdmap van de repo):  python3 tools/gen_codebook_json.py
"""
import json
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "Remeha_parametercodeboek.xlsx"
OUT = ROOT / "components" / "remeha_confida" / "codebook.json"


def parse_choices(txt):
    """'0=Uit | 1=Aan' -> [[0, 'Uit'], [1, 'Aan']]"""
    out = []
    if not txt:
        return out
    for part in str(txt).split(" | "):
        m = re.match(r"\s*(-?\d+)=(.*)$", part)
        if m:
            out.append([int(m.group(1)), m.group(2).strip()])
    return out


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True)
    ws = wb["Parameters"]
    hdr = next(ws.iter_rows(max_row=1, values_only=True))
    col = {h: i for i, h in enumerate(hdr)}

    enums = {}
    we = wb["Enums"]
    eh = next(we.iter_rows(max_row=1, values_only=True))
    ec = {h: i for i, h in enumerate(eh)}
    for r in we.iter_rows(min_row=2, values_only=True):
        name, val, txt = r[ec["Enum"]], r[ec["Waarde"]], r[ec["Omschrijving (NL)"]]
        if name is None or val is None:
            continue
        enums.setdefault(name, []).append([int(val), str(txt or val).strip()])

    codes = {}
    dupes = set()
    for r in ws.iter_rows(min_row=2, values_only=True):
        code = r[col["App-code"]]
        if not code:
            continue
        code = str(code).strip().upper()
        note = r[col["Wetenswaardigheden"]] or ""
        entry = {
            "i": int(r[col["CANopen index"]], 16),
            "s": int(r[col["Sub"]], 16),
            "a": 1 if str(note).startswith("ARRAY") else 0,  # array: waarde op sub >= 1
            "k": {"Parameter": "P", "Signal": "S", "Counter": "C"}.get(r[col["Soort"]], "S"),
            "t": r[col["Datatype"]],
            "g": float(r[col["Gain"]]) if r[col["Gain"]] not in (None, "") else 1.0,
            "u": r[col["Eenheid"]] or "",
            "n": (r[col["Naam (NL)"]] or code).strip(),
        }
        if entry["t"] == "Enum":
            ch = parse_choices(r[col["Toegestane waarden (NL)"]])
            if not ch and r[col["Enum"]] in enums:
                ch = enums[r[col["Enum"]]]
            entry["e"] = ch
        if code in codes:
            dupes.add(code)
            continue
        codes[code] = entry
    for d in dupes:  # ambigue codes: niet via code: te gebruiken
        codes[d] = {"dup": 1}
    OUT.write_text(json.dumps(codes, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(codes)} codes ({len(dupes)} dubbel), {OUT.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
