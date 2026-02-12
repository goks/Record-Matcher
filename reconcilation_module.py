import pyodbc
import pandas as pd
from rapidfuzz import fuzz
import numpy as np
import re

def normalize_reference(value):
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "nat", "-"}:
        return ""
    return text.lstrip("0")

def normalize_column_name(value):
    return re.sub(r"\s+", " ", str(value).replace("\n", " ").strip())

def detect_bank_type(bank_display_name):
    text = str(bank_display_name).lower()
    if "hdfc" in text:
        return "HDFC"
    if "icici" in text:
        return "ICICI"
    raise Exception(f"Unsupported bank for statement import: {bank_display_name}")

def find_header_row(raw_df, required_headers):
    required = {normalize_column_name(h).lower() for h in required_headers}
    for i, row in raw_df.iterrows():
        row_values = {
            normalize_column_name(cell).lower()
            for cell in row.tolist()
            if str(cell).strip().lower() not in {"", "nan", "none"}
        }
        if required.issubset(row_values):
            return i
    return None

def parse_busy_date(value):
    if pd.isna(value):
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return value.normalize()

    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "nat"}:
        return pd.NaT

    # Handle numeric BUSY date formats like 20251103 / 20251103.0
    if text.replace(".", "", 1).isdigit():
        num = text.split(".")[0]
        if len(num) == 8:
            dt = pd.to_datetime(num, format="%Y%m%d", errors="coerce")
            if pd.notna(dt):
                return dt.normalize()

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
        dt = pd.to_datetime(text, format=fmt, errors="coerce")
        if pd.notna(dt):
            return dt.normalize()

    return pd.to_datetime(text, errors="coerce", dayfirst=True).normalize() \
        if pd.notna(pd.to_datetime(text, errors="coerce", dayfirst=True)) else pd.NaT

def has_common_narration_word(ledger_text, bank_text):
    ledger_words = set(re.findall(r"[A-Za-z0-9]+", str(ledger_text).lower()))
    bank_words = set(re.findall(r"[A-Za-z0-9]+", str(bank_text).lower()))
    return len(ledger_words.intersection(bank_words)) > 0

# ==============================
# CONFIGURATION
# ==============================

DB_SERVER = r"GASERVER\BUSYSTDSQL"
DB_NAME = "BusyComp0004_db12025"

FROM_DATE = "2025-04-01"
TO_DATE = "2026-03-31"

AMOUNT_TOLERANCE = 0.50
MIN_NARRATION_SCORE = 50
MATCHED_COLUMNS = [
    "LedgerDate",
    "BankDate",
    "Amount",
    "Party",
    "LedgerNarration",
    "BankNarration",
    "MatchType",
    "Reason",
    "DateDiff",
    "TextScore",
]

# ==============================
# DATABASE CONNECTION
# ==============================

def connect_to_sql(server, database):
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
    )

# ==============================
# LOAD BANK LIST
# ==============================

def load_bank_accounts(server, database):
    conn = connect_to_sql(server, database)

    query = """
    SELECT 
        Code,
        Name +
        CASE 
            WHEN Alias IS NOT NULL AND Alias <> '' 
            THEN ' (' + Alias + ')'
            ELSE ''
        END AS DisplayName
    FROM Master1 WITH (NOLOCK)
    WHERE MasterType = 2
      AND ParentGrp = 112
      AND DeactiveMaster = 0
      AND BlockedMaster = 0
    ORDER BY Name
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ==============================
# LOAD LEDGER FROM SQL
# ==============================

def load_bank_ledger(server, database, bank_master_code, from_date, to_date):
    conn = connect_to_sql(server, database)

    query = """
    SELECT
        B.ENTRYDATE AS DATE1,
        (
            SELECT TOP 1 H1.NameAlias
            FROM Help1 H1
            WHERE H1.NameOrAlias = 1
              AND H1.Code = B.MasterCode2
        ) AS PARTY,
        B.SHORTNAR,
        B.C1 AS CHEQUE_NO,
        COALESCE(
            NULLIF(LTRIM(RTRIM(B.I1)), ''),
            NULLIF(LTRIM(RTRIM(B.C1)), '')
        ) AS INSTRUMENT_NO,
        B.OPAMT AS AMT,
        B.CLRDATE,
        B.VCHNO,
        CAST(0 AS BIGINT) AS VCHCODE
    FROM BRSOPBAL B WITH (NOLOCK)
    WHERE B.MASTERCODE1 = ?
      AND B.ENTRYDATE BETWEEN ? AND ?

    UNION ALL

    SELECT
        T.DATE AS DATE1,
        (
            SELECT TOP 1 H1.NameAlias
            FROM Help1 H1
            WHERE H1.NameOrAlias = 1
              AND H1.Code = T.MasterCode1
        ) AS PARTY,
        T.SHORTNAR,
        T.C1 AS CHEQUE_NO,
        COALESCE(
            NULLIF(LTRIM(RTRIM(T.C2)), ''),
            NULLIF(LTRIM(RTRIM(T.C1)), ''),
            NULLIF(LTRIM(RTRIM(RP.REF_C2)), ''),
            NULLIF(LTRIM(RTRIM(RP.REF_C1)), '')
        ) AS INSTRUMENT_NO,
        T.VALUE1 AS AMT,
        T.CLRDATE,
        T.VCHNO,
        T.VCHCODE
    FROM TRAN2 T WITH (NOLOCK)
    OUTER APPLY (
        SELECT TOP 1
            X.C2 AS REF_C2,
            X.C1 AS REF_C1
        FROM TRAN2 X WITH (NOLOCK)
        WHERE X.VCHCODE = T.VCHCODE
          AND X.RECTYPE = 1
          AND (
              NULLIF(LTRIM(RTRIM(X.C2)), '') IS NOT NULL OR
              NULLIF(LTRIM(RTRIM(X.C1)), '') IS NOT NULL
          )
        ORDER BY
          CASE WHEN X.MASTERCODE1 <> T.MASTERCODE1 THEN 0 ELSE 1 END,
          X.DATE
    ) RP
    WHERE T.RECTYPE = 1
      AND T.VCHCODE IN (
          SELECT DISTINCT T2.VCHCODE
          FROM TRAN2 T2 WITH (NOLOCK)
          WHERE T2.RECTYPE = 1
            AND T2.MASTERCODE1 = ?
            AND T2.MASTERCODE2 = 0
            AND T2.DATE BETWEEN ? AND ?
      )
      AND T.MASTERCODE1 <> ?
    """

    df = pd.read_sql(query, conn, params=[
        int(bank_master_code),
        str(from_date),
        str(to_date),
        int(bank_master_code),
        str(from_date),
        str(to_date),
        int(bank_master_code),
    ])

    conn.close()

    df['DATE1'] = pd.to_datetime(df['DATE1'], errors='coerce')
    df['CLRDATE'] = df['CLRDATE'].apply(parse_busy_date)
    df.loc[df['CLRDATE'].dt.year < 2020, 'CLRDATE'] = pd.NaT
    # Use BUSY AMT column only (as per query semantics).
    df['Amount'] = pd.to_numeric(df['AMT'], errors='coerce').fillna(0).round(2)

    df['CHEQUE_NO'] = df['CHEQUE_NO'].apply(normalize_reference)
    df['INSTRUMENT_NO'] = df['INSTRUMENT_NO'].apply(normalize_reference)

    return df

# ==============================
# HDFC STATEMENT LOADER
# ==============================

def load_hdfc_statement(excel_path):

    raw_df = pd.read_excel(excel_path, header=None, engine="openpyxl")

    header_row = find_header_row(
        raw_df,
        ["Date", "Narration", "Chq./Ref.No.", "Withdrawal Amt.", "Deposit Amt."]
    )

    if header_row is None:
        raise Exception("Could not detect transaction table header.")

    df = pd.read_excel(
        excel_path,
        skiprows=header_row,
        engine="openpyxl"
    )
    df.columns = [normalize_column_name(c) for c in df.columns]

    df = df[df["Date"] != "********"]

    df = df.rename(columns={
        "Narration": "Description",
        "Withdrawal Amt.": "Debit",
        "Deposit Amt.": "Credit",
        "Chq./Ref.No.": "CHEQUE_NO"
    })

    df["Debit"] = df["Debit"].astype(str).str.replace(",", "", regex=False)
    df["Credit"] = df["Credit"].astype(str).str.replace(",", "", regex=False)

    df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce").fillna(0)
    df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce").fillna(0)

    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df = df.dropna(subset=["Date"])

    # Reverse sign convention for bank amount calculation.
    df["Amount"] = (df["Credit"] - df["Debit"]).round(2)

    df["CHEQUE_NO"] = df["CHEQUE_NO"].apply(normalize_reference)
    df["IS_CHEQUE_DEPOSIT"] = (
        df["Description"].astype(str).str.strip().str.upper().str.startswith("CHQ DEP")
    )
    df["SKIP_MATCH"] = False
    df["BANK_TYPE"] = "HDFC"

    return df

def _pick_column(df, candidates, required=True):
    lookup = {str(c).lower(): c for c in df.columns}
    for name in candidates:
        col = lookup.get(str(name).lower())
        if col is not None:
            return col
    if required:
        raise Exception(f"Required column not found. Tried: {candidates}")
    return None

def load_icici_statement(excel_path):
    raw_df = pd.read_excel(excel_path, header=None, engine="openpyxl")

    header_row = find_header_row(
        raw_df,
        ["Value Date", "Description", "Cr/Dr", "Transaction Amount(INR)"]
    )
    if header_row is None:
        raise Exception("Could not detect ICICI transaction table header.")

    df = pd.read_excel(
        excel_path,
        skiprows=header_row,
        engine="openpyxl"
    )
    df.columns = [normalize_column_name(c) for c in df.columns]

    date_col = _pick_column(df, ["Value Date"])
    desc_col = _pick_column(df, ["Description"])
    crdr_col = _pick_column(df, ["Cr/Dr"])
    amt_col = _pick_column(df, ["Transaction Amount(INR)", "Transaction Amount (INR)"])

    df["Date"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    df["Description"] = (
        df[desc_col]
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    amount_series = (
        df[amt_col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["TxnAmount"] = pd.to_numeric(amount_series, errors="coerce").fillna(0)
    df["CrDr"] = df[crdr_col].astype(str).str.strip().str.upper()
    df["Amount"] = np.where(df["CrDr"] == "CR", df["TxnAmount"], -df["TxnAmount"]).round(2)

    df["IS_CHEQUE_DEPOSIT"] = df["Description"].str.upper().str.startswith("CLG/")
    df["SKIP_MATCH"] = df["Description"].str.upper().str.startswith("UPI")

    # ICICI cheque number is embedded in CLG narration: CLG/<...>/<cheque_no>/<...>
    df["CHEQUE_NO"] = (
        df["Description"]
        .str.extract(r"(?i)^CLG/[^/]+/([0-9]+)(?:/|$)", expand=False)
        .fillna("")
        .apply(normalize_reference)
    )
    df["BANK_TYPE"] = "ICICI"

    df = df.dropna(subset=["Date"])

    return df

def load_bank_statement(excel_path, bank_type):
    if bank_type == "HDFC":
        return load_hdfc_statement(excel_path)
    if bank_type == "ICICI":
        return load_icici_statement(excel_path)
    raise Exception(f"No loader configured for bank type: {bank_type}")

# ==============================
# RECONCILIATION ENGINE
# ==============================

def reconcile(bank_df, ledger_df):

    bank_df = bank_df.copy()
    ledger_df = ledger_df.copy()

    bank_df['matched'] = False
    ledger_df['matched'] = False
    if 'SKIP_MATCH' not in bank_df.columns:
        bank_df['SKIP_MATCH'] = False
    else:
        bank_df['SKIP_MATCH'] = bank_df['SKIP_MATCH'].fillna(False)
    if 'IS_CHEQUE_DEPOSIT' not in bank_df.columns:
        bank_df['IS_CHEQUE_DEPOSIT'] = False
    else:
        bank_df['IS_CHEQUE_DEPOSIT'] = bank_df['IS_CHEQUE_DEPOSIT'].fillna(False)

    ignored_bank = bank_df[bank_df['SKIP_MATCH'] == True].copy()

    matches = []

    for l_idx, l_row in ledger_df.iterrows():

        if ledger_df.at[l_idx, 'matched']:
            continue

        # 1) Amount must match first.
        candidates = bank_df[
            (bank_df['SKIP_MATCH'] == False) &
            (bank_df['matched'] == False) &
            (np.abs(bank_df['Amount'] - l_row['Amount']) <= AMOUNT_TOLERANCE)
        ].copy()

        if candidates.empty:
            continue

        reason_parts = [f"Amount matched within tolerance ({AMOUNT_TOLERANCE})"]
        match_type = "Amount"

        # 2) If instrument/cheque exists in BUSY, it must match bank ref.
        ledger_refs = [l_row.get('INSTRUMENT_NO', ''), l_row.get('CHEQUE_NO', '')]
        ledger_refs = [ref for ref in dict.fromkeys(ledger_refs) if ref]
        if ledger_refs:
            candidates_with_ref = candidates[
                (candidates['CHEQUE_NO'].astype(str).str.len() > 0) |
                (candidates['IS_CHEQUE_DEPOSIT'] == True)
            ]
            if not candidates_with_ref.empty:
                candidates = candidates_with_ref[candidates_with_ref['CHEQUE_NO'].isin(ledger_refs)]
                if candidates.empty:
                    continue
                reason_parts.append(f"Instrument/Cheque matched ({', '.join(ledger_refs)})")
                match_type = "Instrument"

        # 3) If clearing date exists in BUSY, it must match bank statement date.
        clr_date = l_row.get('CLRDATE')
        has_clearing_date = pd.notna(clr_date)
        if has_clearing_date:
            clr_date = pd.Timestamp(clr_date).normalize()
            candidates = candidates[candidates['Date'].dt.normalize() == clr_date]
            if candidates.empty:
                continue
            reason_parts.append("Clearing date matched bank date")
            match_type = "ClearingDate"

        # 4) Narration match must be based on ledger name (PARTY) vs bank narration.
        ledger_name = str(l_row.get('PARTY', '')).strip()
        if not ledger_name:
            continue
        candidates = candidates[
            candidates['Description'].apply(
                lambda x: has_common_narration_word(ledger_name, x)
            )
        ]
        if candidates.empty:
            continue
        reason_parts.append("At least one ledger-name word matched in bank narration")

        # 5) Narration score is only a tie-breaker.
        candidates['text_score'] = candidates['Description'].apply(
            lambda x: fuzz.partial_ratio(
                str(x).lower(),
                ledger_name.lower()
            )
        )
        tie_base_date = clr_date if has_clearing_date else l_row['DATE1']
        candidates['date_diff'] = (
            candidates['Date'].dt.normalize() - pd.Timestamp(tie_base_date).normalize()
        ).abs().dt.days

        candidates = candidates.sort_values(
            by=['text_score', 'date_diff'],
            ascending=[False, True]
        )

        best_match = candidates.iloc[0]

        ledger_df.at[l_idx, 'matched'] = True
        bank_df.at[best_match.name, 'matched'] = True

        reason_parts.append(f"Narration tie-breaker score {best_match['text_score']:.0f}")

        matches.append({
            "LedgerDate": l_row['DATE1'],
            "BankDate": best_match['Date'],
            "Amount": l_row['Amount'],
            "Party": l_row['PARTY'],
            "LedgerNarration": l_row['SHORTNAR'],
            "BankNarration": best_match['Description'],
            "MatchType": match_type,
            "Reason": "; ".join(reason_parts),
            "DateDiff": best_match['date_diff'],
            "TextScore": best_match['text_score']
        })

    matched_df = pd.DataFrame(matches, columns=MATCHED_COLUMNS)
    unmatched_bank = bank_df[(bank_df['matched'] == False) & (bank_df['SKIP_MATCH'] == False)]
    unmatched_ledger = ledger_df[ledger_df['matched'] == False]

    return matched_df, unmatched_bank, unmatched_ledger, ignored_bank

# ==============================
# MAIN PROGRAM
# ==============================

def main():

    print("\nLoading bank accounts...\n")
    banks = load_bank_accounts(DB_SERVER, DB_NAME)

    for idx, row in banks.iterrows():
        print(f"{idx}: {row['DisplayName']}")

    choice = int(input("\nSelect bank index: "))
    selected_bank = banks.iloc[choice]

    bank_code = int(selected_bank['Code'])
    bank_name = selected_bank['DisplayName']
    bank_type = detect_bank_type(bank_name)

    print(f"\nSelected Bank: {bank_name} ({bank_type})")

    print("\nLoading ledger...")
    ledger_df = load_bank_ledger(
        DB_SERVER,
        DB_NAME,
        bank_code,
        FROM_DATE,
        TO_DATE
    )

    print("Ledger loaded:", len(ledger_df), "rows")

    excel_path = input("\nEnter bank statement (.xlsx) path: ")

    if not excel_path.lower().endswith(".xlsx"):
        raise Exception("Please provide converted .xlsx file.")

    bank_df = load_bank_statement(excel_path, bank_type)

    print("Bank rows loaded:", len(bank_df))

    print("\nReconciling... Please wait...\n")

    matched, unmatched_bank, unmatched_ledger, ignored_bank = reconcile(bank_df, ledger_df)

    matched = matched.sort_values(by="BankDate")
    unmatched_bank = unmatched_bank.sort_values(by="Date")
    unmatched_ledger = unmatched_ledger.sort_values(by="DATE1")

    output_file = f"Reconciliation_{bank_name.replace(' ', '_')}.xlsx"
    
    

    with pd.ExcelWriter(output_file) as writer:

        # 1️⃣ Matched Results
        matched.to_excel(writer, sheet_name="Matched", index=False)

        # 2️⃣ Unmatched Bank Entries
        unmatched_bank.to_excel(writer, sheet_name="Unmatched_Bank", index=False)

        # 3️⃣ Unmatched Ledger Entries
        unmatched_ledger.to_excel(writer, sheet_name="Unmatched_Ledger", index=False)

        # 4️⃣ Full Bank Statement (Debug)
        bank_df.drop(columns=["matched"], errors="ignore") \
            .to_excel(writer, sheet_name="Bank_Statement_Debug", index=False)

        # 5️⃣ Full BUSY Ledger (Debug)
        ledger_df.drop(columns=["matched"], errors="ignore") \
                .to_excel(writer, sheet_name="Busy_Ledger_Debug", index=False)

        # 6️⃣ Ignored Bank Entries (e.g., ICICI UPI)
        ignored_bank.drop(columns=["matched"], errors="ignore") \
            .to_excel(writer, sheet_name="Ignored_Bank", index=False)

        summary = pd.DataFrame({
            "Metric": [
                "Total Bank Entries",
                "Total Ledger Entries",
                "Matched Count",
                "Unmatched Bank",
                "Unmatched Ledger",
                "Ignored Bank Entries"
            ],
            "Value": [
                len(bank_df),
                len(ledger_df),
                len(matched),
                len(unmatched_bank),
                len(unmatched_ledger),
                len(ignored_bank)
            ]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)

        print("\nReconciliation Completed ✅")
        print("Output saved as:", output_file)



if __name__ == "__main__":
    main()
