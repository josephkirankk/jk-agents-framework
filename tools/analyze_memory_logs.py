#!/usr/bin/env python3
"""
Memory transaction log analyzer for JK-Agents Framework.

This tool helps troubleshoot memory issues by analyzing log files created by
the memory transaction logging system. It provides summaries, timelines, and
insights into memory operations per conversation thread.
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Optional


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a log line to extract the JSON entry.
    
    Args:
        line: Raw log line
        
    Returns:
        Parsed JSON entry or None if parsing fails
    """
    try:
        # Log format: "2025-01-27 06:22:45,123 - {JSON content}"
        if ' - {' in line:
            json_part = line.split(' - ', 1)[1]
            return json.loads(json_part)
    except (json.JSONDecodeError, IndexError, KeyError):
        pass
    return None


def parse_log_entries_from_file(log_file: Path) -> List[Dict[str, Any]]:
    """
    Parse log entries from a file, handling multi-line JSON.
    
    Args:
        log_file: Path to log file
        
    Returns:
        List of parsed log entries
    """
    entries = []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by timestamp patterns to separate entries
        import re
        # Pattern: YYYY-MM-DD HH:MM:SS,mmm -
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - '
        
        # Split content into chunks
        chunks = re.split(timestamp_pattern, content)
        
        # First chunk is usually empty, skip it
        for chunk in chunks[1:]:  # Skip first empty chunk
            chunk = chunk.strip()
            if chunk:
                try:
                    # Try to parse as JSON
                    entry = json.loads(chunk)
                    entries.append(entry)
                except json.JSONDecodeError:
                    # If it doesn't parse, skip this chunk
                    continue
                    
    except Exception as e:
        print(f"   ⚠️  Error reading {log_file.name}: {e}")
    
    return entries


def analyze_thread_logs(thread_id: str, log_directory: str = "memory_logs") -> None:
    """
    Analyze all log files for a specific thread.
    
    Args:
        thread_id: Thread ID to analyze
        log_directory: Directory containing log files
    """
    log_dir = Path(log_directory)
    
    if not log_dir.exists():
        print(f"❌ Log directory does not exist: {log_directory}")
        return
    
    # Find all log files for this thread
    thread_files = list(log_dir.glob(f"memory_{thread_id}_*.log"))
    
    if not thread_files:
        print(f"❌ No log files found for thread: {thread_id}")
        print(f"   Searched in: {log_dir.absolute()}")
        
        # Show available thread IDs
        all_files = list(log_dir.glob("memory_*.log"))
        if all_files:
            available_threads = set()
            for f in all_files:
                parts = f.stem.split('_')
                if len(parts) >= 2:
                    # Extract thread_id from filename: memory_THREAD_ID_timestamp.log
                    thread_part = '_'.join(parts[1:-1])  # Everything between 'memory' and timestamp
                    available_threads.add(thread_part)
            
            if available_threads:
                print(f"\n📋 Available thread IDs:")
                for tid in sorted(available_threads):
                    print(f"   - {tid}")
        return
    
    print(f"🔍 Analyzing thread: {thread_id}")
    print(f"📁 Found {len(thread_files)} log files")
    print(f"📂 Log directory: {log_dir.absolute()}")
    print()
    
    # Parse all entries
    operations = Counter()
    timeline = []
    operation_details = defaultdict(list)
    total_entries = 0
    
    for log_file in sorted(thread_files):
        print(f"📄 Processing: {log_file.name}")
        
        entries = parse_log_entries_from_file(log_file)
        file_entry_count = len(entries)
        total_entries += file_entry_count
        
        for entry in entries:
            operation = entry.get('operation', 'UNKNOWN')
            operations[operation] += 1
            
            timeline.append({
                'timestamp': entry.get('timestamp', 'unknown'),
                'operation': operation,
                'file': log_file.name,
                'entry': entry
            })
            
            operation_details[operation].append(entry)
        
        print(f"   📊 Parsed {file_entry_count} entries")
    
    print()
    print(f"📈 Total entries processed: {total_entries}")
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 OPERATION SUMMARY")
    print("=" * 60)
    
    if not operations:
        print("❌ No valid operations found in log files")
        return
    
    total_operations = sum(operations.values())
    for op, count in operations.most_common():
        percentage = (count / total_operations) * 100
        print(f"{op:<40} {count:>6} ({percentage:>5.1f}%)")
    
    print(f"\n📈 Total operations: {total_operations}")
    
    # Show timeline
    print("\n" + "=" * 60)
    print("⏰ RECENT TIMELINE (Last 15 operations)")
    print("=" * 60)
    
    recent_timeline = timeline[-15:] if len(timeline) > 15 else timeline
    
    for entry in recent_timeline:
        timestamp = entry['timestamp']
        if timestamp != 'unknown':
            try:
                # Parse and format timestamp for better readability
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M:%S')
            except:
                formatted_time = timestamp[:8] if len(timestamp) > 8 else timestamp
        else:
            formatted_time = 'unknown'
        
        print(f"{formatted_time} - {entry['operation']:<35} ({entry['file']})")
    
    # Show operation details for most common operations
    print("\n" + "=" * 60)
    print("🔍 OPERATION DETAILS")
    print("=" * 60)
    
    for op, count in operations.most_common(3):  # Top 3 operations
        print(f"\n{op} ({count} occurrences):")
        print("-" * 50)
        
        details = operation_details[op]
        
        # Show interesting statistics based on operation type
        if 'STORE_CONVERSATION' in op:
            msg_lengths = [d.get('user_message_length', 0) for d in details if 'user_message_length' in d]
            response_lengths = [d.get('assistant_response_length', 0) for d in details if 'assistant_response_length' in d]
            
            if msg_lengths:
                print(f"  📝 Avg user message length: {sum(msg_lengths) / len(msg_lengths):.0f} chars")
            if response_lengths:
                print(f"  🤖 Avg assistant response length: {sum(response_lengths) / len(response_lengths):.0f} chars")
            
            with_metadata = sum(1 for d in details if d.get('has_metadata', False))
            print(f"  📋 Entries with metadata: {with_metadata}/{len(details)}")
            
        elif 'GET_' in op:
            limits = [d.get('limit', 0) for d in details if 'limit' in d]
            if limits:
                print(f"  📊 Avg limit requested: {sum(limits) / len(limits):.1f}")
                print(f"  📊 Max limit requested: {max(limits)}")
                print(f"  📊 Min limit requested: {min(limits)}")
        
        elif 'ENHANCE_SYSTEM_MESSAGE' in op:
            msg_lengths = [d.get('original_message_length', 0) for d in details if 'original_message_length' in d]
            if msg_lengths:
                print(f"  📝 Avg original message length: {sum(msg_lengths) / len(msg_lengths):.0f} chars")
            
            prepend_count = sum(1 for d in details if d.get('prepend', False))
            print(f"  🔄 Prepend context: {prepend_count}/{len(details)}")
    
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)


def list_available_threads(log_directory: str = "memory_logs") -> None:
    """
    List all available thread IDs in the log directory.
    
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
    
    print(f"📁 Found {len(all_files)} log files in: {log_dir.absolute()}")
    print()
    
    # Extract thread IDs and group by thread
    thread_info = defaultdict(list)
    
    for log_file in all_files:
        parts = log_file.stem.split('_')
        if len(parts) >= 3:
            # memory_THREAD_ID_timestamp.log
            thread_id = '_'.join(parts[1:-1])  # Everything between 'memory' and timestamp
            timestamp = parts[-1]
            thread_info[thread_id].append({
                'file': log_file.name,
                'timestamp': timestamp
            })
    
    if not thread_info:
        print("❌ No valid thread IDs found in log files")
        return
    
    print("📋 Available thread IDs:")
    print("=" * 60)
    
    for thread_id, files in sorted(thread_info.items()):
        file_count = len(files)
        latest_file = max(files, key=lambda x: x['timestamp'])
        
        print(f"🔗 {thread_id}")
        print(f"   Files: {file_count}")
        print(f"   Latest: {latest_file['file']}")
        print()


def show_directory_stats(log_directory: str = "memory_logs") -> None:
    """
    Show statistics about the log directory.
    
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
    
    total_size = sum(f.stat().st_size for f in all_files)
    
    print(f"📁 Directory: {log_dir.absolute()}")
    print(f"📄 Total files: {len(all_files)}")
    print(f"💾 Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    print()
    
    # Show file age distribution
    now = datetime.now()
    age_buckets = {'< 1 hour': 0, '< 1 day': 0, '< 1 week': 0, '> 1 week': 0}
    
    for log_file in all_files:
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        age_hours = (now - mtime).total_seconds() / 3600
        
        if age_hours < 1:
            age_buckets['< 1 hour'] += 1
        elif age_hours < 24:
            age_buckets['< 1 day'] += 1
        elif age_hours < 168:  # 7 days
            age_buckets['< 1 week'] += 1
        else:
            age_buckets['> 1 week'] += 1
    
    print("📅 File age distribution:")
    for age_range, count in age_buckets.items():
        if count > 0:
            print(f"   {age_range}: {count} files")


def main():
    """Main entry point for the memory log analyzer."""
    parser = argparse.ArgumentParser(
        description='Analyze memory transaction logs from JK-Agents Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s thread_123                    # Analyze logs for thread_123
  %(prog)s thread_123 --log-dir logs    # Use custom log directory
  %(prog)s --list                       # List all available thread IDs
  %(prog)s --stats                      # Show directory statistics
        """
    )
    
    parser.add_argument(
        'thread_id', 
        nargs='?',
        help='Thread ID to analyze (required unless using --list or --stats)'
    )
    parser.add_argument(
        '--log-dir', 
        default='memory_logs',
        help='Log directory path (default: memory_logs)'
    )
    parser.add_argument(
        '--list', 
        action='store_true',
        help='List all available thread IDs'
    )
    parser.add_argument(
        '--stats', 
        action='store_true',
        help='Show directory statistics'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_available_threads(args.log_dir)
    elif args.stats:
        show_directory_stats(args.log_dir)
    elif args.thread_id:
        analyze_thread_logs(args.thread_id, args.log_dir)
    else:
        parser.error("Thread ID is required unless using --list or --stats")


if __name__ == "__main__":
    main()