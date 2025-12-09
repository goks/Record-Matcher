# Configuration Management Guide

## Overview

Record Matcher uses a comprehensive configuration management system that provides:
- **TOML-based configuration** - Human-readable, industry-standard format
- **Environment-specific settings** - Separate configs for dev/staging/prod
- **Schema validation** - Pydantic models ensure configuration correctness
- **Type safety** - Full type hints and IDE support
- **Hot-reload** - Optional automatic reload on file changes
- **Backward compatibility** - Existing code continues to work

## Quick Start

### Basic Usage

```python
from config import get_config

# Get configuration instance
config = get_config()

# Access configuration values
ledger_name = config.tally.hdfc_ledger_name
max_length = config.validation.max_cheque_number_length
is_debug = config.application.debug_mode
```

### Environment Setup

Set the environment using an environment variable:

```powershell
# Development
$env:RECORD_MATCHER_ENV = "development"

# Production (default)
$env:RECORD_MATCHER_ENV = "production"

# Staging
$env:RECORD_MATCHER_ENV = "staging"
```

## Configuration Files

### File Hierarchy

Configuration files are loaded in this order (later files override earlier ones):

1. **config.default.toml** - Default values (committed to git)
2. **config.{environment}.toml** - Environment-specific overrides (committed to git)
3. **config.local.toml** - Local developer overrides (gitignored)

### File Locations

All configuration files are in the application root directory:
```
Record-Matcher v2/
├── config.default.toml          # Default configuration
├── config.development.toml      # Development overrides
├── config.production.toml       # Production overrides
├── config.local.toml.template   # Template for local config
└── config.local.toml            # Your local overrides (create from template)
```

## Configuration Sections

### Application Settings

Controls application-level behavior:

```toml
[application]
app_name = "Record Matcher"
environment = "production"        # development/staging/production
debug_mode = false               # Enable debug features
log_level = "INFO"               # DEBUG/INFO/WARNING/ERROR/CRITICAL
```

**Access:**
```python
config.application.app_name       # "Record Matcher"
config.application.environment    # "production"
config.application.debug_mode     # False
config.application.log_level      # "INFO"
```

### Tally Ledger Configuration

Bank and intermediary ledger names:

```toml
[tally]
hdfc_ledger_name = "HDFC Bank A/c No.50200008623602"
icici_ledger_name_gok = "ICICI Bank A/c No.099005000974"
icici_ledger_name_uni = "ICICI 1027"
payment_intermediary_ledger = "OTHER CREDITORS"
receipt_intermediary_ledger = "OTHER DEBTORS"
```

**Access:**
```python
config.tally.hdfc_ledger_name                 # HDFC account name
config.tally.icici_ledger_name_gok            # ICICI GOK account
config.tally.icici_ledger_name_uni            # ICICI UNI account
config.tally.payment_intermediary_ledger      # Payment intermediary
config.tally.receipt_intermediary_ledger      # Receipt intermediary
```

### Validation Rules

Cheque number and data validation settings:

```toml
[validation]
max_cheque_number_length = 15
cheque_number_padding_length = 16
```

**Access:**
```python
config.validation.max_cheque_number_length    # 15
config.validation.cheque_number_padding_length # 16
```

**Validation:**
- `max_cheque_number_length`: Must be between 1-50
- `cheque_number_padding_length`: Must be between 1-50 and > max_length

### File Paths

Directory paths for application files:

```toml
[paths]
temp_directory = "./temp"
output_directory = "./output"
fonts_directory = "./fonts"
images_directory = "./images"
service_account_directory = "./service-account"
```

**Access:**
```python
config.paths.temp_directory           # "./temp"
config.paths.output_directory         # "./output"
config.paths.fonts_directory          # "./fonts"
config.paths.images_directory         # "./images"
config.paths.service_account_directory # "./service-account"
```

### Firebase Configuration

Firebase connection and operation settings:

```toml
[firebase]
credentials_file = "service-account/recordmatcher-firebase-adminsdk-mfcn7-d0ee2c6bad.json"
database_url = ""                # Leave empty to use default from credentials
batch_size = 500                 # Number of records per batch
timeout_seconds = 30             # Timeout for operations
```

**Access:**
```python
config.firebase.credentials_file  # Path to credentials
config.firebase.database_url      # Optional database URL
config.firebase.batch_size        # 500
config.firebase.timeout_seconds   # 30
```

**Validation:**
- `batch_size`: Must be between 1-10000
- `timeout_seconds`: Must be between 5-300

## Environment-Specific Configuration

### Development Environment

**config.development.toml:**
```toml
[application]
environment = "development"
debug_mode = true
log_level = "DEBUG"

[firebase]
timeout_seconds = 60    # Longer timeout for debugging
batch_size = 100        # Smaller batches for easier debugging
```

**Features:**
- Debug mode enabled
- Verbose logging
- Extended timeouts for debugging
- Smaller batch sizes for better error visibility

### Production Environment

**config.production.toml:**
```toml
[application]
environment = "production"
debug_mode = false
log_level = "INFO"

[firebase]
batch_size = 500        # Optimized for performance
timeout_seconds = 30    # Production timeout
```

**Features:**
- Debug mode disabled
- Standard logging
- Optimized batch sizes
- Production-level timeouts

## Local Configuration

### Creating Local Overrides

1. Copy the template:
   ```powershell
   Copy-Item config.local.toml.template config.local.toml
   ```

2. Edit `config.local.toml` with your custom settings:
   ```toml
   # Override Tally ledger names for testing
   [tally]
   hdfc_ledger_name = "HDFC Test Account"
   
   # Override paths for local development
   [paths]
   temp_directory = "C:/MyCustomPath/temp"
   
   # Use test Firebase credentials
   [firebase]
   credentials_file = "path/to/test-credentials.json"
   batch_size = 50
   ```

3. Your `config.local.toml` is gitignored - it won't be committed

### Local Override Examples

**Test with different database:**
```toml
[firebase]
credentials_file = "service-account/test-credentials.json"
database_url = "https://test-database.firebaseio.com"
```

**Custom paths:**
```toml
[paths]
temp_directory = "C:/Users/YourName/AppData/Local/RecordMatcher/temp"
output_directory = "D:/Documents/RecordMatcher/output"
```

**Different ledger names:**
```toml
[tally]
hdfc_ledger_name = "My Custom HDFC Account"
icici_ledger_name_gok = "My ICICI Account"
```

## Advanced Usage

### Manual Configuration Reload

```python
config = get_config()

# Modify external config file
# ...

# Reload configuration
config.reload()
```

### Hot-Reload (Auto-reload on file changes)

```python
from config import ConfigManager

# Enable auto-reload
config = ConfigManager(auto_reload=True)

# Configuration will automatically reload when files change
# (Useful for development, disable in production)
```

### Save Configuration

```python
config = get_config()

# Modify configuration
config.tally.hdfc_ledger_name = "New Account Name"

# Save to local config file
config.save_config()  # Saves to config.local.toml
```

### Custom Configuration Directory

```python
from config import ConfigManager

# Load config from custom directory
config = ConfigManager(config_dir="/path/to/configs")
```

### Explicit Environment

```python
from config import ConfigManager

# Override environment detection
config = ConfigManager(environment='development')
```

## Validation

### Schema Validation

All configuration is validated using Pydantic models when loaded:

```python
# This will raise a validation error:
# config.validation.max_cheque_number_length = "abc"  # Not an integer
# config.application.environment = "invalid"  # Not a valid environment
# config.firebase.batch_size = 20000  # Exceeds maximum (10000)
```

### Validation Rules

**Application:**
- `environment` must be: "development", "staging", or "production"
- `log_level` must be: "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL"

**Validation:**
- `max_cheque_number_length`: 1 ≤ value ≤ 50
- `cheque_number_padding_length`: 1 ≤ value ≤ 50
- Padding length should be greater than max length (warning if not)

**Firebase:**
- `batch_size`: 1 ≤ value ≤ 10000
- `timeout_seconds`: 5 ≤ value ≤ 300

## Migration from Hardcoded Values

### Before (Hardcoded)

```python
# core.py
HDFC_TALLY_LEDGERNAME = "HDFC Bank A/c No.50200008623602"
MAX_CHEQUE_NUMBER_LENGTH = 15

# Usage
if len(chqno) <= MAX_CHEQUE_NUMBER_LENGTH:
    formatted = format_chqNo(chqno)
```

### After (Configuration)

```python
# core.py (backward compatible)
from config import get_config

_config = get_config()
HDFC_TALLY_LEDGERNAME = _config.tally.hdfc_ledger_name
MAX_CHEQUE_NUMBER_LENGTH = _config.validation.max_cheque_number_length

# Usage (same as before)
if len(chqno) <= MAX_CHEQUE_NUMBER_LENGTH:
    formatted = format_chqNo(chqno)
```

### New Code (Direct Config Access)

```python
from config import get_config

config = get_config()

# Direct access
if len(chqno) <= config.validation.max_cheque_number_length:
    formatted = format_chqNo(chqno)
```

## Testing

### Test Configuration Loading

```bash
python test_config.py
```

**Expected Output:**
```
Testing configuration loading...
✓ Config loaded successfully
  App Name: Record Matcher
  Environment: production
  HDFC Ledger: HDFC Bank A/c No.50200008623602
  ICICI GOK Ledger: ICICI Bank A/c No.099005000974
  ...
✓ All configuration values accessed successfully
✓ Configuration system working correctly
```

### Test in Python

```python
from config import get_config

config = get_config()

# Test values
assert config.application.app_name == "Record Matcher"
assert config.tally.hdfc_ledger_name == "HDFC Bank A/c No.50200008623602"
assert config.validation.max_cheque_number_length == 15
```

## Troubleshooting

### Configuration File Not Found

**Problem:** Warning message: "Default config not found"

**Solution:** Ensure `config.default.toml` exists in the application directory

### Validation Errors

**Problem:** `ValidationError` when loading config

**Solution:** Check the error message for invalid values:
```
1 validation error for AppConfig
application -> environment
  value is not a valid enumeration member; permitted: 'development', 'staging', 'production'
```

Fix the invalid value in your config file.

### Module Not Found: pydantic

**Problem:** `ModuleNotFoundError: No module named 'pydantic'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
# or
pip install toml pydantic
```

### Changes Not Taking Effect

**Problem:** Configuration changes not reflected in application

**Solutions:**
1. Restart the application (config loaded once at startup)
2. Enable hot-reload: `ConfigManager(auto_reload=True)`
3. Manually reload: `config.reload()`

### Environment Variable Not Working

**Problem:** Environment-specific config not loading

**Solution:** Ensure environment variable is set before running application:
```powershell
# Set environment
$env:RECORD_MATCHER_ENV = "development"

# Verify
echo $env:RECORD_MATCHER_ENV

# Run application
python main.py
```

## Best Practices

### Development Workflow

1. **Use config.local.toml for personal settings**
   - Never commit config.local.toml
   - Use for local database URLs, test credentials, custom paths

2. **Keep default values in config.default.toml**
   - Commit this file
   - Should work out-of-the-box for new developers

3. **Use environment-specific files for team settings**
   - Commit these files
   - Share development/staging/production settings with team

### Security

1. **Never commit sensitive values**
   - Use config.local.toml for secrets
   - Use environment variables for production secrets
   - Rotate credentials regularly

2. **Use environment-specific credentials**
   - Development: Use test/sandbox credentials
   - Production: Use separate production credentials

3. **Validate configuration**
   - Schema validation catches typos
   - Range validation prevents misconfigurations
   - Test configuration after changes

### Performance

1. **Use singleton pattern**
   - Call `get_config()` instead of creating new instances
   - Config loaded once and cached

2. **Disable hot-reload in production**
   - Default is disabled for performance
   - Only enable during development if needed

3. **Keep config files small**
   - Only include values that differ from defaults
   - Use comments to document non-obvious values

## API Reference

### ConfigManager Class

**Constructor:**
```python
ConfigManager(
    config_dir: Optional[str] = None,
    environment: Optional[str] = None,
    auto_reload: bool = False
)
```

**Properties:**
- `application: ApplicationConfig` - Application settings
- `tally: TallyLedgerConfig` - Tally ledger names
- `validation: ValidationConfig` - Validation rules
- `paths: PathConfig` - File paths
- `firebase: FirebaseConfig` - Firebase settings

**Methods:**
- `reload() -> None` - Reload configuration from files
- `get_config_dict() -> Dict[str, Any]` - Get config as dictionary
- `save_config(file_path: Optional[str] = None) -> None` - Save config to file

### Global Functions

**get_config():**
```python
def get_config() -> ConfigManager
```
Get or create the global ConfigManager instance.

**reset_config():**
```python
def reset_config() -> None
```
Reset the global ConfigManager instance (useful for testing).

## Examples

### Example 1: Basic Access

```python
from config import get_config

config = get_config()

print(f"Application: {config.application.app_name}")
print(f"HDFC Ledger: {config.tally.hdfc_ledger_name}")
print(f"Max Cheque Length: {config.validation.max_cheque_number_length}")
```

### Example 2: Conditional Behavior

```python
from config import get_config

config = get_config()

if config.application.debug_mode:
    # Enable verbose logging
    logging.basicConfig(level=logging.DEBUG)
    print("Debug mode enabled")
else:
    # Standard logging
    logging.basicConfig(level=logging.INFO)
```

### Example 3: Environment-Specific Logic

```python
from config import get_config

config = get_config()

if config.application.environment == 'development':
    # Use test database
    firebase_creds = config.firebase.credentials_file
else:
    # Use production database
    firebase_creds = config.firebase.credentials_file

print(f"Using credentials: {firebase_creds}")
```

### Example 4: Dynamic Configuration

```python
from config import get_config

config = get_config()

# Build file path from config
import os
temp_file = os.path.join(config.paths.temp_directory, "data.xlsx")
output_file = os.path.join(config.paths.output_directory, "report.xlsx")

print(f"Temp file: {temp_file}")
print(f"Output file: {output_file}")
```

## Support

For issues or questions about configuration:

1. Check this guide for common scenarios
2. Review troubleshooting section
3. Check CHANGELOG.md for recent changes
4. Test with `test_config.py`
5. Review Pydantic validation errors for details

## Version History

- **v1.0** (December 9, 2025) - Initial release
  - TOML-based configuration
  - Pydantic schema validation
  - Environment-specific configs
  - Hot-reload support
  - Backward compatibility with hardcoded constants
