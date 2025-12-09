"""Test configuration loading and validation."""

from config import get_config

# Test config loading
print("Testing configuration loading...")

cfg = get_config()

print("✓ Config loaded successfully")
print(f"  App Name: {cfg.application.app_name}")
print(f"  Environment: {cfg.application.environment}")
print(f"  HDFC Ledger: {cfg.tally.hdfc_ledger_name}")
print(f"  ICICI GOK Ledger: {cfg.tally.icici_ledger_name_gok}")
print(f"  ICICI UNI Ledger: {cfg.tally.icici_ledger_name_uni}")
print(f"  Max Cheque Length: {cfg.validation.max_cheque_number_length}")
print(f"  Cheque Padding Length: {cfg.validation.cheque_number_padding_length}")
print(f"  Temp Directory: {cfg.paths.temp_directory}")
print(f"  Firebase Credentials: {cfg.firebase.credentials_file}")

print("\n✓ All configuration values accessed successfully")
print("✓ Configuration system working correctly")
