try:
    import pyodbc
except ImportError:
    pyodbc = None
import pandas as pd
try:
    from rapidfuzz import fuzz
except ImportError:
    from difflib import SequenceMatcher

    class _FuzzFallback:
        @staticmethod
        def partial_ratio(a, b):
            return int(100 * SequenceMatcher(None, str(a), str(b)).ratio())

    fuzz = _FuzzFallback()
import numpy as np
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    "_LedgerRowIndex",
    "_BankRowIndex",
    "_SourceRowIndex",
]


@dataclass(frozen=True)
class ReconciliationContext:
    """Context used when running reconciliation from a stored snapshot."""
    company: str
    bank: str
    year: str
    month: str
    financial_year: str
    statement_path: str = ""
    year_db: str = ""
    company_db: str = ""


def _derive_financial_year(month: str, year: str) -> str:
    month = (month or "").strip().lower()
    year_int = int(str(year).strip())
    if month in {"january", "february", "march"}:
        return f"{year_int - 1}-{year_int}"
    return f"{year_int}-{year_int + 1}"


def _build_context(
    company: str,
    bank: str,
    year: str,
    month: str,
    statement_path: Optional[str] = None
) -> ReconciliationContext:
    return ReconciliationContext(
        company=(company or "").strip().lower(),
        bank=(bank or "").strip().lower(),
        year=str(year).strip(),
        month=(month or "").strip().lower(),
        financial_year=_derive_financial_year(month, year),
        statement_path=(statement_path or "").strip(),
    )


def _normalize_snapshot_table(master_table: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(master_table or [])
    if df.empty:
        return df
    # Backward compatibility: old snapshots may have "Infi Date".
    if "Busy Date" not in df.columns and "Infi Date" in df.columns:
        df["Busy Date"] = df["Infi Date"]
    if "Infi Date" in df.columns:
        df = df.drop(columns=["Infi Date"])
    required_cols = [
        "Bank Date",
        "Bank Narration",
        "Chq No",
        "Party Name",
        "Busy Date",
        "Credit",
        "Debit",
        "Closing Balance",
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    df["Bank Date Parsed"] = pd.to_datetime(df["Bank Date"], dayfirst=True, errors="coerce")
    return df


def _to_numeric_amount(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    ).fillna(0.0)


def _build_bank_df_from_snapshot(table_df: pd.DataFrame, bank: str) -> pd.DataFrame:
    if table_df.empty:
        return table_df

    bank_df = pd.DataFrame()
    bank_df["SourceRowIndex"] = table_df.index
    bank_df["Date"] = pd.to_datetime(table_df["Bank Date"], dayfirst=True, errors="coerce")
    bank_df["Description"] = table_df["Bank Narration"].astype(str).fillna("").str.strip()
    bank_df["CHEQUE_NO"] = table_df["Chq No"].apply(normalize_reference)

    credit = _to_numeric_amount(table_df["Credit"])
    debit = _to_numeric_amount(table_df["Debit"])
    bank_df["Amount"] = (credit - debit).round(2)

    bank_lower = (bank or "").strip().lower()
    if bank_lower == "icici":
        bank_df["IS_CHEQUE_DEPOSIT"] = bank_df["Description"].str.upper().str.startswith("CLG/")
        bank_df["SKIP_MATCH"] = bank_df["Description"].str.upper().str.startswith("UPI")
        bank_df["BANK_TYPE"] = "ICICI"
    else:
        bank_df["IS_CHEQUE_DEPOSIT"] = bank_df["Description"].str.upper().str.startswith("CHQ DEP")
        bank_df["SKIP_MATCH"] = False
        bank_df["BANK_TYPE"] = "HDFC"

    bank_df = bank_df.dropna(subset=["Date"]).reset_index(drop=True)
    return bank_df


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _resolve_company_year_db(app_company: str, fy_start: int, options_df: pd.DataFrame) -> Dict[str, Any]:
    if options_df.empty:
        raise ValueError("No company/year options available from ERP SQL")

    year_candidates = options_df[options_df["FYStart"] == int(fy_start)].copy()
    if year_candidates.empty:
        raise ValueError(f"No ERP database found for financial year start: {fy_start}")

    alias_map = {
        "gokul": ["gokul", "gokulagencies"],
        "universal": ["universal", "universalenterprises"],
        "gawel1": ["gawel1", "gawel", "1249"],
        "gawel2": ["gawel2", "gawel", "1153", "impex"],
        "focus": ["focus", "gandh"],
    }
    keys = alias_map.get((app_company or "").strip().lower(), [app_company])
    keys_norm = [_normalize_text(k) for k in keys if str(k).strip()]

    def score_row(row: pd.Series) -> int:
        name_norm = _normalize_text(row.get("CompanyName", ""))
        db_norm = _normalize_text(row.get("CompanyDb", ""))
        score = 0
        for token in keys_norm:
            if token and token in name_norm:
                score += 2
            if token and token in db_norm:
                score += 1
        return score

    year_candidates["match_score"] = year_candidates.apply(score_row, axis=1)
    year_candidates = year_candidates.sort_values(by=["match_score", "CompanyName"], ascending=[False, True])
    top = year_candidates.iloc[0].to_dict()
    if int(top.get("match_score", 0)) <= 0:
        raise ValueError(
            f"Could not map app company '{app_company}' to ERP company DB for FY {fy_start}-{fy_start + 1}"
        )
    return top


def _derive_fy_start_from_context(context: ReconciliationContext) -> int:
    year_int = int(context.year)
    if context.month in {"january", "february", "march"}:
        return year_int - 1
    return year_int


def _fetch_busy_ledger_for_context(context: ReconciliationContext) -> pd.DataFrame:
    fy_start = _derive_fy_start_from_context(context)
    options_df = load_company_year_options(DB_SERVER)
    selected = _resolve_company_year_db(context.company, fy_start, options_df)

    year_db = str(selected["YearDb"])
    print(
        "[RECON DEBUG] ERP DB resolved:",
        f"company={selected.get('CompanyName')} ({selected.get('CompanyDb')}), year_db={year_db}"
    )

    banks = load_bank_accounts(DB_SERVER, year_db)
    if banks.empty:
        raise ValueError(f"No bank accounts found in ERP DB: {year_db}")

    target_bank = (context.bank or "").strip().lower()
    def _safe_bank_type(display_name: str) -> str:
        try:
            return detect_bank_type(display_name).lower()
        except Exception:
            return ""

    bank_matches = banks[
        banks["DisplayName"].apply(lambda x: _safe_bank_type(x) == target_bank)
    ]
    if bank_matches.empty:
        raise ValueError(f"No ERP bank account matched app bank '{target_bank}' in DB {year_db}")

    from_date, to_date = get_financial_year_dates(fy_start)
    print("[RECON DEBUG] Loading Busy ledger:", f"from={from_date}, to={to_date}")

    # If multiple bank masters match (common for ICICI), select by best reconciliation score.
    if len(bank_matches) == 1:
        selected_bank = bank_matches.iloc[0]
        bank_code = int(selected_bank["Code"])
        bank_display_name = str(selected_bank["DisplayName"])
        print("[RECON DEBUG] ERP bank account selected:", f"{bank_display_name} (Code={bank_code})")
        ledger_df = load_bank_ledger(DB_SERVER, year_db, bank_code, from_date, to_date)
        print(f"[RECON DEBUG] Busy ledger rows loaded from ERP: {len(ledger_df)}")
        return ledger_df

    print(f"[RECON DEBUG] Multiple ERP bank accounts matched for {target_bank}: {len(bank_matches)}")
    raise ValueError("Internal error: ambiguous ERP bank selection requires bank_df scoring")


def _fetch_busy_ledger_for_context_with_mapping(
    context: ReconciliationContext,
    bank_mapping: Optional[Dict[str, Dict[str, str]]] = None
) -> pd.DataFrame:
    """Fetch Busy ledger using explicit company+bank -> ERP bank code mapping from settings."""
    fy_start = _derive_fy_start_from_context(context)
    options_df = load_company_year_options(DB_SERVER)
    selected = _resolve_company_year_db(context.company, fy_start, options_df)

    year_db = str(selected["YearDb"])
    banks = load_bank_accounts(DB_SERVER, year_db)
    target_bank = (context.bank or "").strip().lower()

    def _safe_bank_type(display_name: str) -> str:
        try:
            return detect_bank_type(display_name).lower()
        except Exception:
            return ""

    bank_matches = banks[banks["DisplayName"].apply(lambda x: _safe_bank_type(x) == target_bank)]
    if bank_matches.empty:
        raise ValueError(f"No ERP bank account matched app bank '{target_bank}' in DB {year_db}")

    from_date, to_date = get_financial_year_dates(fy_start)
    company_mapping = (bank_mapping or {}).get(context.company, {})
    bank_key = f"{target_bank}_code"
    configured_code = str(company_mapping.get(bank_key, "")).strip()
    if not configured_code:
        raise ValueError(
            f"No ERP mapping configured for {context.company}/{target_bank}. "
            "Open Settings and set ERP bank code."
        )
    if not configured_code.isdigit():
        raise ValueError(
            f"Invalid ERP bank code '{configured_code}' for {context.company}/{target_bank}. "
            "Use numeric Code from ERP bank master."
        )

    configured_code_int = int(configured_code)
    candidate_codes = set(bank_matches["Code"].astype(int).tolist())
    if configured_code_int not in candidate_codes:
        candidates_text = ", ".join(str(x) for x in sorted(candidate_codes))
        raise ValueError(
            f"Configured ERP bank code {configured_code_int} not found for {context.company}/{target_bank}. "
            f"Available ERP codes: {candidates_text}"
        )

    selected_bank = bank_matches[bank_matches["Code"].astype(int) == configured_code_int].iloc[0]
    selected_name = str(selected_bank["DisplayName"])
    print(
        "[RECON DEBUG] Using explicit ERP bank mapping:",
        f"company={context.company}, bank={target_bank}, code={configured_code_int}, name={selected_name}"
    )

    ledger_df = load_bank_ledger(DB_SERVER, year_db, configured_code_int, from_date, to_date)
    print(f"[RECON DEBUG] Busy ledger rows loaded from ERP: {len(ledger_df)}")
    return ledger_df


def run_reconciliation_from_snapshot(
    snapshot_data: Dict[str, Any],
    output_dir: str = "output",
    bank_mapping: Optional[Dict[str, Dict[str, str]]] = None,
    write_output: bool = True
) -> Dict[str, Any]:
    """Run reconciliation output generation using already stored snapshot data.

    This entrypoint is used by the GUI flow. It does not query BUSY SQL; instead,
    it uses the statement snapshot already persisted by the application, which
    includes Party Name and Busy Date columns (legacy snapshots may still carry Infi Date).
    """
    if not snapshot_data:
        raise ValueError("Snapshot data is empty")
    print("[RECON DEBUG] run_reconciliation_from_snapshot() invoked")

    company = snapshot_data.get("company", "")
    bank = snapshot_data.get("bank", "")
    year = snapshot_data.get("year", "")
    month = snapshot_data.get("month", "")
    statement_path = snapshot_data.get("source_statement_path", "")
    context = _build_context(company, bank, year, month, statement_path)
    print(
        "[RECON DEBUG] Context:",
        f"company={context.company}, bank={context.bank}, year={context.year}, "
        f"month={context.month}, financial_year={context.financial_year}"
    )

    master_table = snapshot_data.get("master_table", [])
    print(f"[RECON DEBUG] Snapshot master_table rows: {len(master_table)}")
    table_df = _normalize_snapshot_table(master_table)
    if table_df.empty:
        raise ValueError("Snapshot has no statement rows")

    print("[RECON DEBUG] Preparing bank statement dataframe from snapshot...")
    bank_df = _build_bank_df_from_snapshot(table_df, context.bank)
    print(f"[RECON DEBUG] Prepared bank rows for matching: {len(bank_df)}")
    if bank_df.empty:
        raise ValueError("No valid bank statement rows found in snapshot")

    ledger_df = _fetch_busy_ledger_for_context_with_mapping(context, bank_mapping=bank_mapping)
    if ledger_df.empty:
        raise ValueError("ERP Busy ledger returned 0 rows for selected company/FY/bank")

    print("[RECON DEBUG] Running reconcile(bank_df, ledger_df)...")
    matched_df, unmatched_bank, unmatched_ledger, ignored_bank = reconcile(bank_df, ledger_df)
    print(
        "[RECON DEBUG] Reconcile output:",
        f"matched={len(matched_df)}, unmatched_bank={len(unmatched_bank)}, "
        f"unmatched_ledger={len(unmatched_ledger)}, ignored={len(ignored_bank)}"
    )

    matched_df = matched_df.sort_values(by="BankDate", na_position="last")
    unmatched_bank = unmatched_bank.sort_values(by="Date", na_position="last")
    unmatched_ledger = unmatched_ledger.sort_values(by="DATE1", na_position="last")

    # Build final statement view with Busy Date + Ledger Name populated only for matched rows.
    # IMPORTANT: This is authoritative on every reconcile run:
    # - clear both fields for all rows first
    # - populate only matched rows
    reconciled_statement_df = table_df.copy()
    if "Busy Date" not in reconciled_statement_df.columns:
        reconciled_statement_df["Busy Date"] = ""
    if "Ledger Name" not in reconciled_statement_df.columns:
        reconciled_statement_df["Ledger Name"] = ""
    reconciled_statement_df["Busy Date"] = ""
    reconciled_statement_df["Ledger Name"] = ""

    if not matched_df.empty:
        updates = matched_df[["_SourceRowIndex", "Party", "LedgerDate"]].copy()
        updates["_SourceRowIndex"] = pd.to_numeric(
            updates["_SourceRowIndex"], errors="coerce"
        ).fillna(-1).astype(int)
        updates = updates[updates["_SourceRowIndex"] >= 0]
        updates = updates[updates["_SourceRowIndex"].isin(reconciled_statement_df.index)]

        if not updates.empty:
            updates["Ledger Name"] = updates["Party"].astype(str).str.strip()

            parsed_busy_dates = pd.to_datetime(updates["LedgerDate"], errors="coerce")
            busy_date_text = parsed_busy_dates.dt.strftime("%d/%m/%Y").fillna("")
            fallback_mask = busy_date_text.eq("") & updates["LedgerDate"].notna()
            if fallback_mask.any():
                busy_date_text.loc[fallback_mask] = updates.loc[fallback_mask, "LedgerDate"].astype(str)
            updates["Busy Date Text"] = busy_date_text

            # Keep the latest mapping for a source row (defensive; should typically be unique).
            updates = updates.drop_duplicates(subset=["_SourceRowIndex"], keep="last").set_index("_SourceRowIndex")
            target_idx = updates.index

            reconciled_statement_df.loc[target_idx, "Ledger Name"] = updates["Ledger Name"]
            # Keep legacy visible columns in sync for existing UI.
            reconciled_statement_df.loc[target_idx, "Party Name"] = updates["Ledger Name"]

            has_busy_date = updates["Busy Date Text"].str.len() > 0
            if has_busy_date.any():
                busy_idx = updates.index[has_busy_date]
                reconciled_statement_df.loc[busy_idx, "Busy Date"] = updates.loc[busy_idx, "Busy Date Text"]
                # Keep legacy date column in sync for existing UI.
                reconciled_statement_df.loc[busy_idx, "Infi Date"] = updates.loc[busy_idx, "Busy Date Text"]

    # Persist updated values back into snapshot payload (saved by caller).
    snapshot_data["master_table"] = reconciled_statement_df.drop(
        columns=["Bank Date Parsed"], errors="ignore"
    ).to_dict(orient="records")

    # Matched export with requested naming.
    matched_export_df = matched_df.rename(
        columns={
            "LedgerDate": "Busy Date",
            "Party": "Ledger Name",
        }
    ).drop(columns=["_LedgerRowIndex", "_BankRowIndex", "_SourceRowIndex"], errors="ignore")

    summary_df = pd.DataFrame({
        "Metric": [
            "Company",
            "Bank",
            "Year",
            "Month",
            "Financial Year",
            "Statement Source Path",
            "Total Bank Rows (from snapshot)",
            "Total Busy Ledger Rows (from ERP SQL)",
            "Matched Rows",
            "Unmatched Bank Rows",
            "Unmatched Ledger Rows",
            "Ignored Bank Rows",
        ],
        "Value": [
            context.company,
            context.bank,
            context.year,
            context.month,
            context.financial_year,
            context.statement_path,
            len(bank_df),
            len(ledger_df),
            len(matched_df),
            len(unmatched_bank),
            len(unmatched_ledger),
            len(ignored_bank),
        ]
    })

    output_file = ""
    if write_output:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / (
            f"Reconciliation_{context.company}_{context.bank}_{context.month}_{context.year}_{timestamp}.xlsx"
        )
        print(f"[RECON DEBUG] Writing reconciliation workbook: {output_file}")

        with pd.ExcelWriter(output_file) as writer:
            matched_export_df.to_excel(
                writer, sheet_name="Matched", index=False
            )
            reconciled_statement_df.drop(columns=["Bank Date Parsed"], errors="ignore").to_excel(
                writer, sheet_name="Reconciled_Statement", index=False
            )
            unmatched_bank.drop(columns=["matched"], errors="ignore").to_excel(
                writer, sheet_name="Unmatched_Bank", index=False
            )
            unmatched_ledger.drop(columns=["matched"], errors="ignore").to_excel(
                writer, sheet_name="Unmatched_Ledger", index=False
            )
            bank_df.drop(columns=["matched"], errors="ignore").to_excel(
                writer, sheet_name="Bank_Statement_Debug", index=False
            )
            ledger_df.drop(columns=["matched"], errors="ignore").to_excel(
                writer, sheet_name="Busy_Ledger", index=False
            )
            ignored_bank.drop(columns=["matched"], errors="ignore").to_excel(
                writer, sheet_name="Ignored_Bank", index=False
            )
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

    return {
        "output_file": str(output_file) if output_file else "",
        "total_rows": len(bank_df),
        "matched_rows": len(matched_df),
        "unmatched_rows": len(unmatched_bank),
        "context": context,
        "updated_snapshot_data": snapshot_data,
    }

# ==============================
# DATABASE CONNECTION
# ==============================

def connect_to_sql(server, database):
    if pyodbc is None:
        raise ImportError("pyodbc is required for SQL-based reconciliation flows.")
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
    )

def get_financial_year_dates(fy_start_year):
    start_year = int(fy_start_year)
    from_date = f"{start_year}-04-01"
    to_date = f"{start_year + 1}-03-31"
    return from_date, to_date

def load_company_year_options(server):
    conn = connect_to_sql(server, "master")
    query = """
    SELECT name
    FROM sys.databases
    WHERE name LIKE 'BusyComp____[_]db1____'
    ORDER BY name
    """
    dbs = pd.read_sql(query, conn)
    conn.close()

    rows = []
    for db_name in dbs["name"].astype(str):
        match = re.match(r"^(BusyComp\d{4})_db1(\d{4})$", db_name)
        if not match:
            continue
        company_db = match.group(1)
        fy_start = int(match.group(2))
        rows.append({
            "YearDb": db_name,
            "CompanyDb": company_db,
            "FYStart": fy_start,
        })

    if not rows:
        return pd.DataFrame(columns=["YearDb", "CompanyDb", "CompanyName", "FYStart", "FYLabel"])

    options_df = pd.DataFrame(rows)

    company_name_map = {}
    company_year_db_map = (
        options_df.sort_values(by="FYStart")
        .groupby("CompanyDb")["YearDb"]
        .last()
        .to_dict()
    )
    for company_db in sorted(options_df["CompanyDb"].unique()):
        company_name = ""
        company_name_db = f"{company_db}_db"

        # Primary lookup: BusyCompXXXX_db
        try:
            c_conn = connect_to_sql(server, company_name_db)
            c_df = pd.read_sql(
                """
                SELECT TOP 1 LTRIM(RTRIM([Name])) AS CompanyName
                FROM dbo.Company
                WHERE NULLIF(LTRIM(RTRIM([Name])), '') IS NOT NULL
                ORDER BY [Name]
                """,
                c_conn
            )
            c_conn.close()
            company_name = str(c_df.iloc[0]["CompanyName"]).strip() if not c_df.empty else ""
        except Exception:
            company_name = ""

        # Fallback 1: BusyCompXXXX
        if not company_name:
            try:
                c_conn = connect_to_sql(server, company_db)
                c_df = pd.read_sql(
                    """
                    SELECT TOP 1 LTRIM(RTRIM([Name])) AS CompanyName
                    FROM dbo.Company
                    WHERE NULLIF(LTRIM(RTRIM([Name])), '') IS NOT NULL
                    ORDER BY [Name]
                    """,
                    c_conn
                )
                c_conn.close()
                company_name = str(c_df.iloc[0]["CompanyName"]).strip() if not c_df.empty else ""
            except Exception:
                company_name = ""

        # Fallback 2: latest known FY DB for this company.
        if not company_name:
            try:
                year_db = company_year_db_map.get(company_db, "")
                if year_db:
                    y_conn = connect_to_sql(server, year_db)
                    y_df = pd.read_sql(
                        """
                        SELECT TOP 1 LTRIM(RTRIM([Name])) AS CompanyName
                        FROM dbo.Company
                        WHERE NULLIF(LTRIM(RTRIM([Name])), '') IS NOT NULL
                        ORDER BY [Name]
                        """,
                        y_conn
                    )
                    y_conn.close()
                    company_name = str(y_df.iloc[0]["CompanyName"]).strip() if not y_df.empty else ""
            except Exception:
                company_name = ""

        if not company_name:
            company_name = company_db
        company_name_map[company_db] = company_name

    options_df["CompanyName"] = options_df["CompanyDb"].map(company_name_map)
    options_df["FYLabel"] = options_df["FYStart"].apply(
        lambda y: f"{y}-{y + 1}"
    )

    return options_df.sort_values(by=["CompanyName", "FYStart"]).reset_index(drop=True)

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

    # Precompute helper fields once for faster candidate filtering.
    bank_df['_amount_cents'] = np.rint(
        pd.to_numeric(bank_df['Amount'], errors='coerce').fillna(0.0) * 100.0
    ).astype(np.int64)
    bank_df['_date_norm'] = pd.to_datetime(bank_df['Date'], errors='coerce').dt.normalize()
    bank_df['_desc_lower'] = bank_df['Description'].astype(str).fillna("").str.lower()
    bank_df['_desc_words'] = bank_df['_desc_lower'].str.findall(r"[A-Za-z0-9]+").apply(set)
    bank_df['_cheque_no_str'] = bank_df['CHEQUE_NO'].astype(str)
    bank_df['_has_cheque_ref'] = bank_df['_cheque_no_str'].str.len() > 0

    # Build amount index for non-skipped bank rows to avoid scanning the full table each loop.
    tolerance_cents = int(round(float(AMOUNT_TOLERANCE) * 100))
    eligible_bank_mask = bank_df['SKIP_MATCH'] == False
    amount_index = defaultdict(list)
    for idx, amount_cents in bank_df.loc[eligible_bank_mask, '_amount_cents'].items():
        amount_index[int(amount_cents)].append(idx)

    # Track unmatched candidates without repeatedly filtering entire DataFrame.
    unmatched_bank_indices = set(bank_df.index[eligible_bank_mask].tolist())
    clr_date_norm = pd.to_datetime(ledger_df.get('CLRDATE'), errors='coerce').dt.normalize()
    date1_norm = pd.to_datetime(ledger_df.get('DATE1'), errors='coerce').dt.normalize()

    matches = []

    for l_row in ledger_df.itertuples(index=True):
        l_idx = l_row.Index

        if ledger_df.at[l_idx, 'matched']:
            continue

        # 1) Amount must match first.
        ledger_amount = getattr(l_row, 'Amount', np.nan)
        if pd.isna(ledger_amount):
            continue
        ledger_amount_cents = int(round(float(ledger_amount) * 100))
        candidate_indices = []
        for cents in range(ledger_amount_cents - tolerance_cents, ledger_amount_cents + tolerance_cents + 1):
            candidate_indices.extend(amount_index.get(cents, []))

        if not candidate_indices:
            continue

        candidate_indices = [idx for idx in candidate_indices if idx in unmatched_bank_indices]
        if not candidate_indices:
            continue

        candidates = bank_df.loc[candidate_indices].copy()

        if candidates.empty:
            continue

        reason_parts = [f"Amount matched within tolerance ({AMOUNT_TOLERANCE})"]
        match_type = "Amount"

        # 2) If instrument/cheque exists in BUSY, it must match bank ref.
        ledger_refs = [getattr(l_row, 'INSTRUMENT_NO', ''), getattr(l_row, 'CHEQUE_NO', '')]
        ledger_refs = [normalize_reference(ref) for ref in ledger_refs]
        ledger_refs = [ref for ref in dict.fromkeys(ledger_refs) if ref]
        if ledger_refs:
            candidates_with_ref = candidates[
                (candidates['_has_cheque_ref']) |
                (candidates['IS_CHEQUE_DEPOSIT'] == True)
            ]
            if not candidates_with_ref.empty:
                candidates = candidates_with_ref[candidates_with_ref['_cheque_no_str'].isin(ledger_refs)]
                if candidates.empty:
                    continue
                reason_parts.append(f"Instrument/Cheque matched ({', '.join(ledger_refs)})")
                match_type = "Instrument"

        # 3) If clearing date exists in BUSY, it must match bank statement date.
        clr_date = clr_date_norm.at[l_idx]
        has_clearing_date = pd.notna(clr_date)
        if has_clearing_date:
            candidates = candidates[candidates['_date_norm'] == clr_date]
            if candidates.empty:
                continue
            reason_parts.append("Clearing date matched bank date")
            match_type = "ClearingDate"

        # 4) Narration match must be based on ledger name (PARTY) vs bank narration.
        ledger_name = str(getattr(l_row, 'PARTY', '')).strip()
        if not ledger_name:
            continue
        ledger_words = set(re.findall(r"[A-Za-z0-9]+", ledger_name.lower()))
        if not ledger_words:
            continue
        candidates = candidates[
            candidates['_desc_words'].apply(
                lambda words: len(words.intersection(ledger_words)) > 0
            )
        ]
        if candidates.empty:
            continue
        reason_parts.append("At least one ledger-name word matched in bank narration")

        # 5) Narration score is only a tie-breaker.
        ledger_name_lower = ledger_name.lower()
        candidates['text_score'] = candidates['_desc_lower'].apply(
            lambda x: fuzz.partial_ratio(
                x,
                ledger_name_lower
            )
        )
        tie_base_date = clr_date if has_clearing_date else date1_norm.at[l_idx]
        if pd.notna(tie_base_date):
            candidates['date_diff'] = (
                candidates['_date_norm'] - tie_base_date
            ).abs().dt.days
        else:
            candidates['date_diff'] = np.iinfo(np.int32).max

        candidates = candidates.sort_values(
            by=['text_score', 'date_diff'],
            ascending=[False, True]
        )

        best_match = candidates.iloc[0]

        ledger_df.at[l_idx, 'matched'] = True
        bank_df.at[best_match.name, 'matched'] = True
        unmatched_bank_indices.discard(best_match.name)

        reason_parts.append(f"Narration tie-breaker score {best_match['text_score']:.0f}")

        matches.append({
            "LedgerDate": getattr(l_row, 'DATE1', ''),
            "BankDate": best_match['Date'],
            "Amount": ledger_amount,
            "Party": getattr(l_row, 'PARTY', ''),
            "LedgerNarration": getattr(l_row, 'SHORTNAR', ''),
            "BankNarration": best_match['Description'],
            "MatchType": match_type,
            "Reason": "; ".join(reason_parts),
            "DateDiff": best_match['date_diff'],
            "TextScore": best_match['text_score'],
            "_LedgerRowIndex": int(l_idx),
            "_BankRowIndex": int(best_match.name),
            "_SourceRowIndex": int(best_match.get("SourceRowIndex", -1)),
        })

    helper_columns = [
        '_amount_cents',
        '_date_norm',
        '_desc_lower',
        '_desc_words',
        '_cheque_no_str',
        '_has_cheque_ref',
    ]
    bank_df = bank_df.drop(columns=helper_columns, errors='ignore')

    matched_df = pd.DataFrame(matches, columns=MATCHED_COLUMNS)
    unmatched_bank = bank_df[(bank_df['matched'] == False) & (bank_df['SKIP_MATCH'] == False)]
    unmatched_ledger = ledger_df[ledger_df['matched'] == False]

    return matched_df, unmatched_bank, unmatched_ledger, ignored_bank

# ==============================
# MAIN PROGRAM
# ==============================

def main():

    print("\nLoading company and financial year options...\n")
    company_year_options = load_company_year_options(DB_SERVER)
    if company_year_options.empty:
        raise Exception("No company financial-year databases found (pattern BusyCompXXXX_db1YYYY).")

    company_choices = (
        company_year_options[["CompanyDb", "CompanyName"]]
        .drop_duplicates()
        .sort_values(by=["CompanyName", "CompanyDb"])
        .reset_index(drop=True)
    )

    for idx, row in company_choices.iterrows():
        print(f"{idx}: {row['CompanyName']} ({row['CompanyDb']})")

    company_choice = int(input("\nSelect company index: "))
    selected_company = company_choices.iloc[company_choice]
    selected_company_db = selected_company["CompanyDb"]
    selected_company_name = selected_company["CompanyName"]

    fy_choices = (
        company_year_options[company_year_options["CompanyDb"] == selected_company_db]
        .sort_values(by="FYStart")
        .reset_index(drop=True)
    )

    print(f"\nAvailable financial years for {selected_company_name}:")
    for idx, row in fy_choices.iterrows():
        print(f"{idx}: {row['FYLabel']}  [{row['YearDb']}]")

    fy_choice = int(input("\nSelect financial year index: "))
    selected_fy = fy_choices.iloc[fy_choice]
    selected_db_name = selected_fy["YearDb"]
    from_date, to_date = get_financial_year_dates(selected_fy["FYStart"])

    print(f"\nUsing database: {selected_db_name}")
    print(f"Financial year date range: {from_date} to {to_date}")

    print("\nLoading bank accounts...\n")
    banks = load_bank_accounts(DB_SERVER, selected_db_name)

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
        selected_db_name,
        bank_code,
        from_date,
        to_date
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
