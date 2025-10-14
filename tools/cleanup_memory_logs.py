#!/usr/bin/env python3
"""
Memory log cleanup utility for JK-Agents Framework.

This tool provides safe cleanup and maintenance of memory transaction log files
created by the memory logging system. It can remove old files, manage disk space,
and provide insights into log file usage.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def cleanup_old_logs(
    log_directory: str = "memory_logs", 
    days_to_keep: int = 7,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Remove memory log files older than specified days.
    
    Args:
        log_directory: Directory containing log files
        days_to_keep: Number of days to keep (files older than this will be removed)
        dry_run: If True, only show what would be deleted without actually deleting
        
    Returns:
        Dictionary with cleanup results
    """
    log_dir = Path(log_directory)
    
    if not log_dir.exists():
        return {
            'success': False,
            'error': f"Log directory does not exist: {log_directory}",
            'files_removed': 0,
            'space_freed': 0
        }
    
    # Find all memory log files
    all_files = list(log_dir.glob("memory_*.log"))
    
    if not all_files:
        return {
            'success': True,
            'message': f"No memory log files found in: {log_directory}",
            'files_removed': 0,
            'space_freed': 0
        }
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    files_to_remove = []
    total_size_to_remove = 0
    
    # Identify files to remove
    for log_file in all_files:
        try:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                file_size = log_file.stat().st_size
                files_to_remove.append({
                    'path': log_file,
                    'name': log_file.name,
                    'size': file_size,
                    'modified': file_mtime
                })
                total_size_to_remove += file_size
                
        except (OSError, PermissionError) as e:
            print(f"⚠️  Warning: Could not access {log_file.name}: {e}")
            continue
    
    if not files_to_remove:
        return {
            'success': True,
            'message': f"No files older than {days_to_keep} days found",
            'files_removed': 0,
            'space_freed': 0,
            'total_files': len(all_files)
        }
    
    # Sort by modification time (oldest first)
    files_to_remove.sort(key=lambda x: x['modified'])
    
    print(f"🗂️  Found {len(files_to_remove)} files to {'remove' if not dry_run else 'be removed'}")
    print(f"💾 Total space to free: {format_size(total_size_to_remove)}")
    print()
    
    removed_count = 0
    actual_size_removed = 0
    errors = []
    
    # Remove files (or show what would be removed in dry run)
    for file_info in files_to_remove:
        file_path = file_info['path']
        file_name = file_info['name']
        file_size = file_info['size']
        
        if dry_run:
            print(f"📄 Would remove: {file_name} ({format_size(file_size)})")
        else:
            try:
                file_path.unlink()
                print(f"🗑️  Removed: {file_name} ({format_size(file_size)})")
                removed_count += 1
                actual_size_removed += file_size
            except (OSError, PermissionError) as e:
                error_msg = f"Failed to remove {file_name}: {e}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
    
    # Show summary
    if dry_run:
        print(f"\n🔍 DRY RUN COMPLETE")
        print(f"   Would remove: {len(files_to_remove)} files")
        print(f"   Would free: {format_size(total_size_to_remove)}")
    else:
        print(f"\n✅ CLEANUP COMPLETE")
        print(f"   Files removed: {removed_count}")
        print(f"   Space freed: {format_size(actual_size_removed)}")
        
        if errors:
            print(f"   Errors: {len(errors)}")
    
    # Show current directory stats
    remaining_files = list(log_dir.glob("memory_*.log"))
    total_remaining_size = sum(f.stat().st_size for f in remaining_files if f.exists())
    
    print(f"\n📊 CURRENT STATUS")
    print(f"   Files remaining: {len(remaining_files)}")
    print(f"   Directory size: {format_size(total_remaining_size)}")
    
    return {
        'success': len(errors) == 0,
        'files_removed': removed_count,
        'space_freed': actual_size_removed,
        'errors': errors,
        'total_files_before': len(all_files),
        'files_remaining': len(remaining_files),
        'dry_run': dry_run
    }


def analyze_disk_usage(log_directory: str = "memory_logs") -> None:
    """
    Analyze disk usage of memory log files.
    
    Args:
        log_directory: Directory containing log files
    """
    log_dir = Path(log_directory)
    
    if not log_dir.exists():
        print(f"❌ Log directory does not exist: {log_directory}")
        return
    
    all_files = list(log_dir.glob("memory_*.log"))
    
    if not all_files:
        print(f"❌ No memory log files found in: {log_directory}")
        return
    
    print(f"📁 Directory: {log_dir.absolute()}")
    print(f"📄 Total files: {len(all_files)}")
    print()
    
    # Calculate total size and age distribution
    total_size = 0
    age_buckets = {
        'Last hour': {'files': 0, 'size': 0},
        'Last day': {'files': 0, 'size': 0},
        'Last week': {'files': 0, 'size': 0},
        'Last month': {'files': 0, 'size': 0},
        'Older': {'files': 0, 'size': 0}
    }
    
    now = datetime.now()
    
    for log_file in all_files:
        try:
            file_size = log_file.stat().st_size
            total_size += file_size
            
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            age_hours = (now - mtime).total_seconds() / 3600
            
            if age_hours < 1:
                age_buckets['Last hour']['files'] += 1
                age_buckets['Last hour']['size'] += file_size
            elif age_hours < 24:
                age_buckets['Last day']['files'] += 1
                age_buckets['Last day']['size'] += file_size
            elif age_hours < 168:  # 7 days
                age_buckets['Last week']['files'] += 1
                age_buckets['Last week']['size'] += file_size
            elif age_hours < 720:  # 30 days
                age_buckets['Last month']['files'] += 1
                age_buckets['Last month']['size'] += file_size
            else:
                age_buckets['Older']['files'] += 1
                age_buckets['Older']['size'] += file_size
                
        except (OSError, PermissionError) as e:
            print(f"⚠️  Warning: Could not access {log_file.name}: {e}")
            continue
    
    print(f"💾 Total size: {format_size(total_size)}")
    print()
    
    print("📅 File age distribution:")
    print("-" * 50)
    for period, stats in age_buckets.items():
        if stats['files'] > 0:
            print(f"{period:<12} {stats['files']:>6} files  {format_size(stats['size']):>10}")
    
    # Show largest files
    print("\n📊 Largest files:")
    print("-" * 50)
    
    file_sizes = [(f, f.stat().st_size) for f in all_files]
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    
    for i, (file_path, size) in enumerate(file_sizes[:10]):  # Top 10
        print(f"{i+1:>2}. {file_path.name:<40} {format_size(size):>10}")
    
    # Provide cleanup recommendations
    print(f"\n💡 CLEANUP RECOMMENDATIONS")
    print("-" * 50)
    
    old_files_count = age_buckets['Last month']['files'] + age_buckets['Older']['files']
    old_files_size = age_buckets['Last month']['size'] + age_buckets['Older']['size']
    
    if old_files_count > 0:
        print(f"📦 {old_files_count} files older than 1 week ({format_size(old_files_size)})")
        print("   Consider running: python tools/cleanup_memory_logs.py --days 7")
    
    very_old_files_count = age_buckets['Older']['files']
    very_old_files_size = age_buckets['Older']['size']
    
    if very_old_files_count > 0:
        print(f"🗑️  {very_old_files_count} files older than 1 month ({format_size(very_old_files_size)})")
        print("   Consider running: python tools/cleanup_memory_logs.py --days 30")
    
    if total_size > 100 * 1024 * 1024:  # > 100MB
        print(f"⚠️  Directory size is large ({format_size(total_size)})")
        print("   Consider regular cleanup or reducing retention period")


def list_files_by_thread(log_directory: str = "memory_logs", show_sizes: bool = False) -> None:
    """
    List log files grouped by thread ID.
    
    Args:
        log_directory: Directory containing log files
        show_sizes: Whether to show file sizes
    """
    log_dir = Path(log_directory)
    
    if not log_dir.exists():
        print(f"❌ Log directory does not exist: {log_directory}")
        return
    
    all_files = list(log_dir.glob("memory_*.log"))
    
    if not all_files:
        print(f"❌ No memory log files found in: {log_directory}")
        return
    
    # Group files by thread ID
    thread_groups = {}
    
    for log_file in all_files:
        parts = log_file.stem.split('_')
        if len(parts) >= 3:
            thread_id = '_'.join(parts[1:-1])  # Extract thread ID
            if thread_id not in thread_groups:
                thread_groups[thread_id] = []
            
            file_info = {
                'path': log_file,
                'name': log_file.name,
                'mtime': datetime.fromtimestamp(log_file.stat().st_mtime)
            }
            
            if show_sizes:
                file_info['size'] = log_file.stat().st_size
            
            thread_groups[thread_id].append(file_info)
    
    print(f"📁 Directory: {log_dir.absolute()}")
    print(f"🔗 Found {len(thread_groups)} thread(s) with {len(all_files)} total files")
    print()
    
    # Sort threads by number of files (descending)
    sorted_threads = sorted(thread_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    for thread_id, files in sorted_threads:
        files.sort(key=lambda x: x['mtime'])  # Sort by modification time
        
        total_size = sum(f['size'] for f in files) if show_sizes else 0
        latest_file = max(files, key=lambda x: x['mtime'])
        oldest_file = min(files, key=lambda x: x['mtime'])
        
        print(f"🔗 Thread: {thread_id}")
        print(f"   Files: {len(files)}")
        
        if show_sizes:
            print(f"   Total size: {format_size(total_size)}")
        
        print(f"   Oldest: {oldest_file['name']} ({oldest_file['mtime'].strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"   Latest: {latest_file['name']} ({latest_file['mtime'].strftime('%Y-%m-%d %H:%M:%S')})")
        print()


def main():
    """Main entry point for the memory log cleanup utility."""
    parser = argparse.ArgumentParser(
        description='Clean up and manage memory transaction log files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --days 7                     # Remove files older than 7 days
  %(prog)s --days 7 --dry-run          # Show what would be removed (dry run)
  %(prog)s --analyze                    # Analyze disk usage
  %(prog)s --list-threads               # List files by thread ID
  %(prog)s --list-threads --show-sizes  # List files with sizes
        """
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=7,
        help='Days to keep (files older than this will be removed, default: 7)'
    )
    parser.add_argument(
        '--log-dir', 
        default='memory_logs',
        help='Log directory path (default: memory_logs)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--analyze', 
        action='store_true',
        help='Analyze disk usage and provide recommendations'
    )
    parser.add_argument(
        '--list-threads', 
        action='store_true',
        help='List files grouped by thread ID'
    )
    parser.add_argument(
        '--show-sizes', 
        action='store_true',
        help='Show file sizes (use with --list-threads or --analyze)'
    )
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_disk_usage(args.log_dir)
    elif args.list_threads:
        list_files_by_thread(args.log_dir, args.show_sizes)
    else:
        # Default action is cleanup
        result = cleanup_old_logs(args.log_dir, args.days, args.dry_run)
        
        if not result['success']:
            print(f"❌ Cleanup failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()