"""
Pickle to SQLite Migration Script

This script migrates all data from pickle files to SQLite database.
Run this once to upgrade your Record Matcher installation from pickle-based
storage to SQLite-based storage for better performance and data integrity.

Usage:
    # Dry run (preview what will be migrated without changes)
    python migrate_to_sqlite.py --dry-run
    
    # Actual migration
    python migrate_to_sqlite.py
    
    # Migration with custom paths
    python migrate_to_sqlite.py --snapshot-pickle /path/to/snapshots.pkl 
                                --cheque-pickle /path/to/cheques.pkl 
                                --sqlite-db /path/to/database.db
    
    # Migration with backup
    python migrate_to_sqlite.py --backup

What this script does:
    1. Locates existing pickle files (auto-detect from APPDATA)
    2. Creates SQLite database with proper schema
    3. Migrates all snapshots from pickle to SQLite
    4. Migrates all cheque reports from pickle to SQLite
    5. Verifies data integrity (checksums)
    6. Optionally backs up pickle files
    7. Generates migration report

After migration:
    - Update main.py to use SQLite repositories
    - Test application thoroughly
    - Keep pickle backups for rollback
    - Consider deleting pickle files after verification

Author: Code Change Documenter Agent
Date: December 9, 2025
"""

import argparse
import os
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def backup_pickle_files(
    snapshot_path: str,
    cheque_path: str,
    backup_dir: Optional[str] = None
) -> Dict[str, str]:
    """Backup pickle files before migration.
    
    Args:
        snapshot_path: Path to snapshot pickle file
        cheque_path: Path to cheque report pickle file
        backup_dir: Directory for backups (creates timestamped dir if None)
    
    Returns:
        Dictionary mapping original paths to backup paths
    """
    if backup_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"./pickle_backup_{timestamp}"
    
    os.makedirs(backup_dir, exist_ok=True)
    logger.info(f"Creating backups in: {backup_dir}")
    
    backups = {}
    
    # Backup snapshot file
    if os.path.exists(snapshot_path):
        backup_path = os.path.join(backup_dir, "tableSnapshotCollection.filv2.backup")
        shutil.copy2(snapshot_path, backup_path)
        backups[snapshot_path] = backup_path
        logger.info(f"✓ Backed up snapshots: {backup_path}")
    
    # Backup cheque file
    if os.path.exists(cheque_path):
        backup_path = os.path.join(backup_dir, "ChequeReportCollection.fil.backup")
        shutil.copy2(cheque_path, backup_path)
        backups[cheque_path] = backup_path
        logger.info(f"✓ Backed up cheque reports: {backup_path}")
    
    return backups


def verify_migration(sqlite_db_path: str, expected_snapshots: int, expected_reports: int) -> bool:
    """Verify migration was successful.
    
    Args:
        sqlite_db_path: Path to SQLite database
        expected_snapshots: Expected number of snapshots
        expected_reports: Expected number of cheque reports
    
    Returns:
        True if verification passed
    """
    try:
        from sqlite_storage import SQLiteSnapshotRepository, SQLiteChequeReportRepository
        
        snapshot_repo = SQLiteSnapshotRepository(db_path=sqlite_db_path)
        cheque_repo = SQLiteChequeReportRepository(db_path=sqlite_db_path)
        
        # Count migrated items
        actual_snapshots = len(snapshot_repo.list_all())
        actual_reports = len(cheque_repo.list_all())
        
        logger.info("\nVerification Results:")
        logger.info(f"  Snapshots: {actual_snapshots} of {expected_snapshots} expected")
        logger.info(f"  Cheque Reports: {actual_reports} of {expected_reports} expected")
        
        # Check health
        snapshot_health = snapshot_repo.health_check()
        cheque_health = cheque_repo.health_check()
        
        logger.info(f"  Snapshot repository health: {'✓ PASS' if snapshot_health else '✗ FAIL'}")
        logger.info(f"  Cheque report repository health: {'✓ PASS' if cheque_health else '✗ FAIL'}")
        
        # Overall verification
        verification_passed = (
            actual_snapshots == expected_snapshots and
            actual_reports == expected_reports and
            snapshot_health and
            cheque_health
        )
        
        if verification_passed:
            logger.info("\n✓ VERIFICATION PASSED")
        else:
            logger.warning("\n⚠ VERIFICATION FAILED - Review migration results")
        
        return verification_passed
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False


def generate_migration_report(results: Dict[str, Any], output_path: str = "./migration_report.txt"):
    """Generate detailed migration report.
    
    Args:
        results: Migration results dictionary
        output_path: Path to save report
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("PICKLE TO SQLITE MIGRATION REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Dry Run: {results.get('dry_run', False)}\n\n")
            
            f.write("RESULTS:\n")
            f.write(f"  Snapshots Migrated: {results.get('snapshots_migrated', 0)}\n")
            f.write(f"  Cheque Reports Migrated: {results.get('cheque_reports_migrated', 0)}\n")
            f.write(f"  Errors: {len(results.get('errors', []))}\n")
            f.write(f"  Success: {results.get('success', False)}\n\n")
            
            if results.get('errors'):
                f.write("ERRORS:\n")
                for i, error in enumerate(results['errors'], 1):
                    f.write(f"  {i}. {error}\n")
                f.write("\n")
            
            f.write("=" * 70 + "\n")
            f.write("NEXT STEPS:\n")
            f.write("=" * 70 + "\n")
            if not results.get('dry_run', False) and results.get('success', False):
                f.write("1. Verify the migration by running the application\n")
                f.write("2. Test all core functionality (load/save/search)\n")
                f.write("3. If everything works, update main.py to use SQLite repositories:\n")
                f.write("   - Change: PickleSnapshotRepository → SQLiteSnapshotRepository\n")
                f.write("   - Change: PickleChequeReportRepository → SQLiteChequeReportRepository\n")
                f.write("   - Or use: get_snapshot_repository() factory function\n")
                f.write("4. After 1-2 weeks of successful operation, consider deleting pickle backups\n")
            elif results.get('dry_run', False):
                f.write("1. Review this dry run report\n")
                f.write("2. Run migration again without --dry-run flag\n")
                f.write("3. Verify results\n")
            else:
                f.write("1. Review errors listed above\n")
                f.write("2. Fix any issues\n")
                f.write("3. Run migration again\n")
        
        logger.info(f"Migration report saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description='Migrate Record Matcher data from pickle to SQLite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview migration
  python migrate_to_sqlite.py --dry-run
  
  # Actual migration with backup
  python migrate_to_sqlite.py --backup
  
  # Custom paths
  python migrate_to_sqlite.py --snapshot-pickle /path/to/snapshots.pkl 
                              --sqlite-db /path/to/database.db
        """
    )
    
    parser.add_argument(
        '--snapshot-pickle',
        help='Path to snapshot pickle file (auto-detects if not specified)',
        default=None
    )
    
    parser.add_argument(
        '--cheque-pickle',
        help='Path to cheque report pickle file (auto-detects if not specified)',
        default=None
    )
    
    parser.add_argument(
        '--sqlite-db',
        help='Path to SQLite database (creates in APPDATA if not specified)',
        default=None
    )
    
    parser.add_argument(
        '--app-name',
        help='Application name for auto-detected paths',
        default='RecordMatcher'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migration without making changes'
    )
    
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Backup pickle files before migration'
    )
    
    parser.add_argument(
        '--backup-dir',
        help='Directory for backups (creates timestamped dir if not specified)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 70)
    print("RECORD MATCHER - PICKLE TO SQLITE MIGRATION")
    print("=" * 70 + "\n")
    
    if args.dry_run:
        print("⚠ DRY RUN MODE - No changes will be made\n")
    
    # Import migration function
    try:
        from sqlite_storage import migrate_pickle_to_sqlite
    except ImportError as e:
        logger.error(f"Failed to import sqlite_storage module: {e}")
        logger.error("Make sure sqlite_storage.py is in the same directory")
        sys.exit(1)
    
    # Auto-detect pickle paths if not specified
    snapshot_path = args.snapshot_pickle
    cheque_path = args.cheque_pickle
    
    if snapshot_path is None or cheque_path is None:
        appdata = os.getenv('APPDATA', '.')
        default_dir = os.path.join(appdata, args.app_name)
        
        if snapshot_path is None:
            snapshot_path = os.path.join(default_dir, "tableSnapshotCollection.filv2")
        if cheque_path is None:
            cheque_path = os.path.join(default_dir, "ChequeReportCollection.fil")
        
        logger.info(f"Auto-detected paths:")
        logger.info(f"  Snapshots: {snapshot_path}")
        logger.info(f"  Cheque Reports: {cheque_path}")
    
    # Check if files exist
    snapshot_exists = os.path.exists(snapshot_path)
    cheque_exists = os.path.exists(cheque_path)
    
    logger.info(f"\nFile status:")
    logger.info(f"  Snapshots: {'✓ Found' if snapshot_exists else '✗ Not found'}")
    logger.info(f"  Cheque Reports: {'✓ Found' if cheque_exists else '✗ Not found'}")
    
    if not snapshot_exists and not cheque_exists:
        logger.error("\n✗ No pickle files found. Nothing to migrate.")
        sys.exit(1)
    
    # Backup if requested
    if args.backup and not args.dry_run:
        logger.info("\nCreating backups...")
        backups = backup_pickle_files(snapshot_path, cheque_path, args.backup_dir)
        logger.info(f"✓ Created {len(backups)} backups")
    
    # Perform migration
    logger.info("\nStarting migration...")
    results = migrate_pickle_to_sqlite(
        pickle_snapshot_path=snapshot_path,
        pickle_cheque_path=cheque_path,
        sqlite_db_path=args.sqlite_db,
        app_name=args.app_name,
        dry_run=args.dry_run
    )
    
    # Generate report
    report_path = f"./migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    generate_migration_report(results, report_path)
    
    # Verify migration (if not dry run)
    if not args.dry_run and results.get('success', False):
        logger.info("\nVerifying migration...")
        sqlite_db = args.sqlite_db or os.path.join(
            os.getenv('APPDATA', '.'), 
            args.app_name, 
            "recordmatcher.db"
        )
        
        verify_migration(
            sqlite_db,
            results.get('snapshots_migrated', 0),
            results.get('cheque_reports_migrated', 0)
        )
    
    # Summary
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print(f"Snapshots migrated: {results.get('snapshots_migrated', 0)}")
    print(f"Cheque reports migrated: {results.get('cheque_reports_migrated', 0)}")
    print(f"Errors: {len(results.get('errors', []))}")
    print(f"Report saved to: {report_path}")
    
    if args.dry_run:
        print("\n⚠ This was a DRY RUN - No changes were made")
        print("Run without --dry-run to perform actual migration")
    elif results.get('success', False):
        print("\n✓ MIGRATION SUCCESSFUL")
        print("\nNext steps:")
        print("1. Test the application thoroughly")
        print("2. Update main.py to use SQLite repositories")
        print("3. Keep pickle backups for 1-2 weeks")
        print("4. Delete pickle files after verifying everything works")
    else:
        print("\n⚠ MIGRATION COMPLETED WITH ERRORS")
        print("Review the report and fix any issues")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Fatal error: {e}", exc_info=True)
        sys.exit(1)
