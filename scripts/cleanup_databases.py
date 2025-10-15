#!/usr/bin/env python3
"""
Database Cleanup Script

This script consolidates all test data into a single centralized database
and archives/removes old database files.

Usage:
    python scripts/cleanup_databases.py [--dry-run] [--backup]

Options:
    --dry-run    Show what would be done without making changes
    --backup     Create backups before deleting old databases
"""

import sqlite3
import json
import gzip
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Database paths
DATA_DIR = Path("./data")
PRIMARY_DB = DATA_DIR / "large_data_storage.db"
OLD_DBS = [
    DATA_DIR / "large_tool_data.db",
    DATA_DIR / "test_large_data.db",
    DATA_DIR / "schema_test_data.db",
]
BACKUP_DIR = DATA_DIR / "backups"


def get_db_stats(db_path: Path) -> dict:
    """Get statistics about a database"""
    if not db_path.exists():
        return {"exists": False}
    
    stats = {
        "exists": True,
        "size_bytes": db_path.stat().st_size,
        "size_mb": round(db_path.stat().st_size / (1024 * 1024), 2),
        "record_count": 0,
        "oldest_record": None,
        "newest_record": None,
    }
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='large_tool_data'
        """)
        
        if cursor.fetchone():
            # Get record count
            cursor.execute("SELECT COUNT(*) FROM large_tool_data")
            stats["record_count"] = cursor.fetchone()[0]
            
            # Get oldest and newest records
            cursor.execute("""
                SELECT MIN(created_at), MAX(created_at) 
                FROM large_tool_data
            """)
            oldest, newest = cursor.fetchone()
            stats["oldest_record"] = oldest
            stats["newest_record"] = newest
        
        conn.close()
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


def migrate_data(source_db: Path, target_db: Path, dry_run: bool = False) -> int:
    """Migrate data from source database to target database"""
    if not source_db.exists():
        return 0
    
    try:
        source_conn = sqlite3.connect(str(source_db))
        source_cursor = source_conn.cursor()
        
        # Check if table exists
        source_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='large_tool_data'
        """)
        
        if not source_cursor.fetchone():
            source_conn.close()
            return 0
        
        # Get all records
        source_cursor.execute("""
            SELECT reference_id, tool_name, storage_type, storage_location,
                   data_blob, data_hash, size_bytes, size_category,
                   content_type, compressed, metadata, created_at,
                   expires_at, access_count, last_accessed
            FROM large_tool_data
        """)
        
        records = source_cursor.fetchall()
        source_conn.close()
        
        if not records:
            return 0
        
        if dry_run:
            print(f"   Would migrate {len(records)} records from {source_db.name}")
            return len(records)
        
        # Insert into target database
        target_conn = sqlite3.connect(str(target_db))
        target_cursor = target_conn.cursor()
        
        migrated = 0
        for record in records:
            try:
                # Check if reference_id already exists
                target_cursor.execute(
                    "SELECT reference_id FROM large_tool_data WHERE reference_id = ?",
                    (record[0],)
                )
                
                if target_cursor.fetchone():
                    print(f"   Skipping duplicate: {record[0]}")
                    continue
                
                # Insert record
                target_cursor.execute("""
                    INSERT INTO large_tool_data (
                        reference_id, tool_name, storage_type, storage_location,
                        data_blob, data_hash, size_bytes, size_category,
                        content_type, compressed, metadata, created_at,
                        expires_at, access_count, last_accessed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, record)
                
                migrated += 1
            except Exception as e:
                print(f"   Error migrating record {record[0]}: {e}")
        
        target_conn.commit()
        target_conn.close()
        
        print(f"   Migrated {migrated} records from {source_db.name}")
        return migrated
        
    except Exception as e:
        print(f"   Error migrating from {source_db.name}: {e}")
        return 0


def backup_database(db_path: Path, backup_dir: Path) -> Path:
    """Create a backup of a database"""
    if not db_path.exists():
        return None
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}_{timestamp}.db"
    
    shutil.copy2(db_path, backup_path)
    return backup_path


def main():
    parser = argparse.ArgumentParser(description="Cleanup and consolidate databases")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--backup", action="store_true", help="Create backups before deleting")
    args = parser.parse_args()
    
    print("=" * 80)
    print("DATABASE CLEANUP AND CONSOLIDATION")
    print("=" * 80)
    print()
    
    # Step 1: Show current state
    print("[Step 1] Current Database State")
    print("-" * 80)
    
    print(f"\nPrimary Database: {PRIMARY_DB}")
    primary_stats = get_db_stats(PRIMARY_DB)
    if primary_stats["exists"]:
        print(f"  Size: {primary_stats['size_mb']} MB")
        print(f"  Records: {primary_stats['record_count']}")
        if primary_stats.get("oldest_record"):
            print(f"  Oldest: {primary_stats['oldest_record']}")
            print(f"  Newest: {primary_stats['newest_record']}")
    else:
        print("  ❌ Does not exist")
    
    print(f"\nOld Databases:")
    old_db_stats = {}
    total_old_records = 0
    for db_path in OLD_DBS:
        stats = get_db_stats(db_path)
        old_db_stats[db_path] = stats
        
        print(f"\n  {db_path.name}:")
        if stats["exists"]:
            print(f"    Size: {stats['size_mb']} MB")
            print(f"    Records: {stats['record_count']}")
            total_old_records += stats['record_count']
            if stats.get("oldest_record"):
                print(f"    Oldest: {stats['oldest_record']}")
                print(f"    Newest: {stats['newest_record']}")
        else:
            print("    ❌ Does not exist")
    
    print()
    print(f"Total records in old databases: {total_old_records}")
    
    # Step 2: Migrate data
    if total_old_records > 0:
        print()
        print("[Step 2] Migrating Data to Primary Database")
        print("-" * 80)
        
        total_migrated = 0
        for db_path in OLD_DBS:
            if old_db_stats[db_path]["exists"] and old_db_stats[db_path]["record_count"] > 0:
                migrated = migrate_data(db_path, PRIMARY_DB, dry_run=args.dry_run)
                total_migrated += migrated
        
        print()
        if args.dry_run:
            print(f"Would migrate {total_migrated} records total")
        else:
            print(f"✅ Migrated {total_migrated} records total")
    else:
        print()
        print("[Step 2] No data to migrate")
    
    # Step 3: Backup old databases
    if args.backup and not args.dry_run:
        print()
        print("[Step 3] Creating Backups")
        print("-" * 80)
        
        for db_path in OLD_DBS:
            if old_db_stats[db_path]["exists"]:
                backup_path = backup_database(db_path, BACKUP_DIR)
                if backup_path:
                    print(f"  ✅ Backed up {db_path.name} to {backup_path}")
    
    # Step 4: Remove old databases
    print()
    print("[Step 4] Removing Old Databases")
    print("-" * 80)
    
    for db_path in OLD_DBS:
        if old_db_stats[db_path]["exists"]:
            if args.dry_run:
                print(f"  Would remove: {db_path}")
            else:
                try:
                    db_path.unlink()
                    print(f"  ✅ Removed: {db_path}")
                except Exception as e:
                    print(f"  ❌ Error removing {db_path}: {e}")
        else:
            print(f"  ⏭️  Skipped (doesn't exist): {db_path}")
    
    # Step 5: Final state
    print()
    print("[Step 5] Final State")
    print("-" * 80)
    
    final_stats = get_db_stats(PRIMARY_DB)
    print(f"\nPrimary Database: {PRIMARY_DB}")
    if final_stats["exists"]:
        print(f"  Size: {final_stats['size_mb']} MB")
        print(f"  Records: {final_stats['record_count']}")
        if final_stats.get("oldest_record"):
            print(f"  Oldest: {final_stats['oldest_record']}")
            print(f"  Newest: {final_stats['newest_record']}")
    
    print()
    print("=" * 80)
    if args.dry_run:
        print("DRY RUN COMPLETE - No changes made")
    else:
        print("✅ CLEANUP COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

