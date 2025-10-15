#!/usr/bin/env python3
"""
Comprehensive Memory System Diagnostic Tool for JK-Agents Framework

This tool analyzes memory logs, checks database connectivity, validates configuration,
and provides detailed recommendations for fixing memory system issues.

Usage:
    python diagnose_memory_issues.py [--log-file LOG_FILE] [--thread-id THREAD_ID]
"""
import argparse
import asyncio
import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryDiagnostics:
    """Comprehensive memory system diagnostics."""
    
    def __init__(self, log_file: Optional[str] = None, thread_id: Optional[str] = None):
        self.log_file = log_file
        self.thread_id = thread_id
        self.issues = []
        self.recommendations = []
        self.log_entries = []
        self.config = None
        
    def add_issue(self, severity: str, issue: str, recommendation: str):
        """Add an issue with recommendation."""
        self.issues.append({
            'severity': severity,
            'issue': issue,
            'recommendation': recommendation
        })
        self.recommendations.append(recommendation)
        
    def parse_log_entries(self, log_content: str) -> List[Dict]:
        """Parse log entries from log content."""
        entries = []
        current_entry = ""
        
        for line in log_content.split('\n'):
            if line.strip():
                if line.startswith('2025-') and current_entry:
                    # Process previous entry
                    try:
                        timestamp_end = current_entry.find(' - ')
                        if timestamp_end != -1:
                            timestamp = current_entry[:timestamp_end]
                            json_part = current_entry[timestamp_end + 3:]
                            entry_data = json.loads(json_part)
                            entry_data['log_timestamp'] = timestamp
                            entries.append(entry_data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse log entry: {e}")
                    
                    # Start new entry
                    current_entry = line
                else:
                    current_entry += "\n" + line
        
        # Process last entry
        if current_entry:
            try:
                timestamp_end = current_entry.find(' - ')
                if timestamp_end != -1:
                    timestamp = current_entry[:timestamp_end]
                    json_part = current_entry[timestamp_end + 3:]
                    entry_data = json.loads(json_part)
                    entry_data['log_timestamp'] = timestamp
                    entries.append(entry_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse final log entry: {e}")
        
        return entries
    
    def analyze_log_file(self, log_file_path: str) -> Dict[str, Any]:
        """Analyze memory log file for issues."""
        print(f"🔍 Analyzing log file: {log_file_path}")
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
        except FileNotFoundError:
            self.add_issue(
                'CRITICAL',
                f"Log file not found: {log_file_path}",
                f"Ensure the log file exists and check the path: {log_file_path}"
            )
            return {}
        
        self.log_entries = self.parse_log_entries(log_content)
        
        # Analyze patterns
        analysis = {
            'total_entries': len(self.log_entries),
            'operations': defaultdict(int),
            'threads': set(),
            'enhancement_attempts': 0,
            'successful_enhancements': 0,
            'storage_attempts': 0,
            'successful_storage': 0,
            'context_retrievals': 0,
            'successful_context_retrievals': 0,
            'timeline': []
        }
        
        for entry in self.log_entries:
            operation = entry.get('operation', 'UNKNOWN')
            thread_id = entry.get('thread_id', 'UNKNOWN')
            timestamp = entry.get('timestamp', entry.get('log_timestamp', 'UNKNOWN'))
            
            analysis['operations'][operation] += 1
            analysis['threads'].add(thread_id)
            analysis['timeline'].append({
                'timestamp': timestamp,
                'operation': operation,
                'thread_id': thread_id
            })
            
            # Analyze enhancement attempts
            if operation == 'ENHANCE_SYSTEM_MESSAGE_WITH_MEMORY':
                analysis['enhancement_attempts'] += 1
            elif operation == 'ENHANCE_SYSTEM_MESSAGE_COMPLETED':
                analysis['successful_enhancements'] += 1
                enhancement_added = entry.get('enhancement_added', 0)
                if enhancement_added == 0:
                    self.add_issue(
                        'HIGH',
                        f"System message enhancement added no context (thread: {thread_id})",
                        "Check database connectivity and ensure conversations are being stored and retrieved properly"
                    )
            
            # Analyze storage attempts
            if operation == 'STORE_CONVERSATION_MEMORY':
                analysis['storage_attempts'] += 1
                if entry.get('user_message_content') and entry.get('assistant_response_content'):
                    analysis['successful_storage'] += 1
            
            # Analyze context retrieval
            if operation == 'GET_CONVERSATION_CONTEXT':
                analysis['context_retrievals'] += 1
            elif operation == 'GET_CONVERSATION_CONTEXT_RESULT':
                analysis['successful_context_retrievals'] += 1
        
        # Check for missing context retrieval results
        if analysis['context_retrievals'] > analysis['successful_context_retrievals']:
            missing_results = analysis['context_retrievals'] - analysis['successful_context_retrievals']
            self.add_issue(
                'HIGH',
                f"Missing context retrieval results: {missing_results} retrieval attempts have no corresponding results",
                "This indicates database connection issues. Check DATABASE_URL environment variable and database connectivity."
            )
        
        # Check for no enhancements
        if analysis['enhancement_attempts'] > 0 and analysis['successful_enhancements'] > 0:
            # Count enhancements that added context
            enhancements_with_context = 0
            for entry in self.log_entries:
                if entry.get('operation') == 'ENHANCE_SYSTEM_MESSAGE_COMPLETED':
                    if entry.get('enhancement_added', 0) > 0:
                        enhancements_with_context += 1
            
            if enhancements_with_context == 0:
                self.add_issue(
                    'HIGH',
                    "No system message enhancements are adding conversation context",
                    "Check database connectivity, ensure conversations are being stored, and verify thread_id consistency"
                )
        
        analysis['threads'] = list(analysis['threads'])
        return analysis
    
    async def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity and configuration."""
        print("🗃️ Checking database connectivity...")
        
        db_check = {
            'database_url_set': bool(os.getenv('DATABASE_URL')),
            'database_url': os.getenv('DATABASE_URL', 'NOT_SET'),
            'connection_successful': False,
            'tables_exist': False,
            'can_store': False,
            'can_retrieve': False,
            'error_details': None
        }
        
        if not db_check['database_url_set']:
            self.add_issue(
                'CRITICAL',
                "DATABASE_URL environment variable is not set",
                "Set DATABASE_URL environment variable: export DATABASE_URL='postgresql://user:password@localhost:5432/conversations'"
            )
            return db_check
        
        try:
            from app.memory.conversation_store import ConversationStore
            
            # Test database connection
            store = ConversationStore(db_check['database_url'], pool_size=2)
            await store.initialize()
            db_check['connection_successful'] = True
            db_check['tables_exist'] = True
            
            # Test storage
            test_thread = f"__diagnostic_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            await store.store_conversation(
                thread_id=test_thread,
                user_message="Diagnostic test message",
                assistant_response="Diagnostic test response",
                metadata={"diagnostic": True}
            )
            db_check['can_store'] = True
            
            # Test retrieval
            conversations = await store.get_recent_conversations(test_thread, limit=1)
            if conversations and len(conversations) > 0:
                db_check['can_retrieve'] = True
            
            # Clean up test data
            await store.delete_conversation_history(test_thread)
            await store.close()
            
        except Exception as e:
            db_check['error_details'] = str(e)
            self.add_issue(
                'CRITICAL',
                f"Database connectivity failed: {e}",
                "Check PostgreSQL server status, database credentials, and network connectivity. Run: python scripts/setup_conversation_db.py"
            )
        
        return db_check
    
    def check_configuration(self) -> Dict[str, Any]:
        """Check memory configuration."""
        print("⚙️ Checking memory configuration...")
        
        config_check = {
            'config_file_exists': False,
            'conversation_memory_section': False,
            'memory_enabled': False,
            'memory_logging_enabled': False,
            'config_details': {}
        }
        
        try:
            from app.main import load_app_config
            from app.memory.memory_integration import is_conversation_memory_enabled
            
            self.config = load_app_config()
            config_check['config_file_exists'] = True
            
            if hasattr(self.config, 'conversation_memory'):
                config_check['conversation_memory_section'] = True
                config_check['memory_enabled'] = self.config.conversation_memory.enabled
                config_check['config_details']['max_conversations'] = self.config.conversation_memory.max_conversations
                config_check['config_details']['max_context_length'] = self.config.conversation_memory.max_context_length
                config_check['config_details']['database_url'] = self.config.conversation_memory.database_url
            
            if hasattr(self.config, 'memory_logging'):
                config_check['memory_logging_enabled'] = self.config.memory_logging.enabled
                config_check['config_details']['include_content'] = self.config.memory_logging.include_content
                config_check['config_details']['max_content_length'] = self.config.memory_logging.max_content_length
            
            # Check if memory is actually enabled (includes database URL check)
            memory_actually_enabled = is_conversation_memory_enabled(self.config)
            if config_check['memory_enabled'] and not memory_actually_enabled:
                self.add_issue(
                    'HIGH',
                    "Memory is enabled in config but not functional",
                    "Check DATABASE_URL environment variable and database connectivity"
                )
        
        except Exception as e:
            self.add_issue(
                'HIGH',
                f"Failed to load configuration: {e}",
                "Check that config/agents.yaml exists and has proper conversation_memory section"
            )
        
        if not config_check['conversation_memory_section']:
            self.add_issue(
                'MEDIUM',
                "No conversation_memory section in configuration",
                "Add conversation_memory section to config/agents.yaml with enabled: true"
            )
        
        if config_check['conversation_memory_section'] and not config_check['memory_enabled']:
            self.add_issue(
                'MEDIUM',
                "Conversation memory is disabled in configuration",
                "Set conversation_memory.enabled: true in config/agents.yaml"
            )
        
        return config_check
    
    async def check_specific_thread(self, thread_id: str) -> Dict[str, Any]:
        """Check specific thread for memory issues."""
        print(f"🧵 Checking specific thread: {thread_id}")
        
        thread_check = {
            'thread_id': thread_id,
            'conversations_in_db': 0,
            'conversations_in_logs': 0,
            'log_entries': [],
            'database_entries': [],
            'issues_found': []
        }
        
        # Check logs for this thread
        thread_entries = [entry for entry in self.log_entries if entry.get('thread_id') == thread_id]
        thread_check['conversations_in_logs'] = len([e for e in thread_entries if e.get('operation') == 'STORE_CONVERSATION_MEMORY'])
        thread_check['log_entries'] = thread_entries
        
        # Check database for this thread
        try:
            from app.memory.conversation_store import ConversationStore
            
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                store = ConversationStore(database_url, pool_size=2)
                await store.initialize()
                
                conversations = await store.get_conversation_history(thread_id, limit=100)
                thread_check['conversations_in_db'] = len(conversations)
                thread_check['database_entries'] = [
                    {
                        'user_message': conv.user_message,
                        'assistant_response': conv.assistant_response,
                        'timestamp': conv.timestamp.isoformat(),
                        'metadata': conv.metadata
                    }
                    for conv in conversations
                ]
                
                await store.close()
        except Exception as e:
            thread_check['issues_found'].append(f"Database check failed: {e}")
        
        # Analyze discrepancies
        if thread_check['conversations_in_logs'] != thread_check['conversations_in_db']:
            thread_check['issues_found'].append(
                f"Mismatch between log entries ({thread_check['conversations_in_logs']}) and database entries ({thread_check['conversations_in_db']})"
            )
        
        return thread_check
    
    def generate_report(self, analysis: Dict[str, Any], db_check: Dict[str, Any], config_check: Dict[str, Any], thread_check: Optional[Dict[str, Any]] = None) -> str:
        """Generate comprehensive diagnostic report."""
        report = []
        report.append("🔬 JK-Agents Framework Memory System Diagnostic Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Executive Summary
        report.append("📋 EXECUTIVE SUMMARY")
        report.append("-" * 20)
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high_issues = len([i for i in self.issues if i['severity'] == 'HIGH'])
        
        if total_issues == 0:
            report.append("✅ No issues detected - memory system appears to be working correctly")
        else:
            report.append(f"❌ {total_issues} issues detected:")
            report.append(f"   - Critical: {critical_issues}")
            report.append(f"   - High Priority: {high_issues}")
            report.append(f"   - Medium Priority: {total_issues - critical_issues - high_issues}")
        report.append("")
        
        # Configuration Status
        report.append("⚙️ CONFIGURATION STATUS")
        report.append("-" * 22)
        report.append(f"Config file exists: {'✅' if config_check['config_file_exists'] else '❌'}")
        report.append(f"Memory section exists: {'✅' if config_check['conversation_memory_section'] else '❌'}")
        report.append(f"Memory enabled: {'✅' if config_check['memory_enabled'] else '❌'}")
        report.append(f"Logging enabled: {'✅' if config_check['memory_logging_enabled'] else '❌'}")
        if config_check['config_details']:
            report.append("Configuration details:")
            for key, value in config_check['config_details'].items():
                report.append(f"  - {key}: {value}")
        report.append("")
        
        # Database Status
        report.append("🗃️ DATABASE STATUS")
        report.append("-" * 17)
        report.append(f"DATABASE_URL set: {'✅' if db_check['database_url_set'] else '❌'}")
        if db_check['database_url_set'] and db_check['database_url'] != 'NOT_SET':
            # Mask password for security
            url_display = db_check['database_url']
            if '@' in url_display:
                parts = url_display.split('@')
                if ':' in parts[0]:
                    user_part = parts[0].split(':')[0]
                    url_display = f"{user_part}:***@{parts[1]}"
            report.append(f"Database URL: {url_display}")
        report.append(f"Connection successful: {'✅' if db_check['connection_successful'] else '❌'}")
        report.append(f"Tables exist: {'✅' if db_check['tables_exist'] else '❌'}")
        report.append(f"Can store data: {'✅' if db_check['can_store'] else '❌'}")
        report.append(f"Can retrieve data: {'✅' if db_check['can_retrieve'] else '❌'}")
        if db_check['error_details']:
            report.append(f"Error details: {db_check['error_details']}")
        report.append("")
        
        # Log Analysis
        if analysis:
            report.append("📊 LOG ANALYSIS")
            report.append("-" * 13)
            report.append(f"Total log entries: {analysis['total_entries']}")
            report.append(f"Threads analyzed: {len(analysis['threads'])}")
            report.append(f"Enhancement attempts: {analysis['enhancement_attempts']}")
            report.append(f"Successful enhancements: {analysis['successful_enhancements']}")
            report.append(f"Storage attempts: {analysis['storage_attempts']}")
            report.append(f"Successful storage: {analysis['successful_storage']}")
            report.append(f"Context retrievals: {analysis['context_retrievals']}")
            report.append(f"Successful context retrievals: {analysis['successful_context_retrievals']}")
            
            report.append("\nOperation breakdown:")
            for op, count in analysis['operations'].items():
                report.append(f"  - {op}: {count}")
            report.append("")
        
        # Thread-specific analysis
        if thread_check:
            report.append("🧵 THREAD-SPECIFIC ANALYSIS")
            report.append("-" * 26)
            report.append(f"Thread ID: {thread_check['thread_id']}")
            report.append(f"Conversations in logs: {thread_check['conversations_in_logs']}")
            report.append(f"Conversations in database: {thread_check['conversations_in_db']}")
            
            if thread_check['issues_found']:
                report.append("Thread-specific issues:")
                for issue in thread_check['issues_found']:
                    report.append(f"  - {issue}")
            report.append("")
        
        # Issues and Recommendations
        if self.issues:
            report.append("🚨 ISSUES AND RECOMMENDATIONS")
            report.append("-" * 29)
            
            for i, issue in enumerate(self.issues, 1):
                report.append(f"{i}. [{issue['severity']}] {issue['issue']}")
                report.append(f"   💡 {issue['recommendation']}")
                report.append("")
        
        # Quick Fix Commands
        if self.issues:
            report.append("🔧 QUICK FIX COMMANDS")
            report.append("-" * 18)
            
            if any('DATABASE_URL' in issue['issue'] for issue in self.issues):
                report.append("# Set DATABASE_URL (replace with your credentials):")
                report.append("export DATABASE_URL='postgresql://jkagent_user:securepassword@localhost:5432/conversations'")
                report.append("")
            
            if any('database connectivity' in issue['recommendation'] for issue in self.issues):
                report.append("# Setup database:")
                report.append("python scripts/setup_conversation_db.py")
                report.append("")
            
            if any('configuration' in issue['recommendation'] for issue in self.issues):
                report.append("# Check configuration:")
                report.append("cat config/agents.yaml | grep -A 10 conversation_memory")
                report.append("")
        
        return "\n".join(report)
    
    async def run_full_diagnostics(self) -> str:
        """Run complete diagnostic suite."""
        print("🚀 Starting comprehensive memory system diagnostics...")
        
        # Load and analyze log file
        analysis = {}
        if self.log_file:
            analysis = self.analyze_log_file(self.log_file)
        
        # Check configuration
        config_check = self.check_configuration()
        
        # Check database connectivity
        db_check = await self.check_database_connectivity()
        
        # Check specific thread if provided
        thread_check = None
        if self.thread_id and self.log_entries:
            thread_check = await self.check_specific_thread(self.thread_id)
        
        # Generate report
        report = self.generate_report(analysis, db_check, config_check, thread_check)
        
        return report


async def main():
    """Main diagnostic function."""
    parser = argparse.ArgumentParser(
        description='Diagnose JK-Agents Framework memory system issues'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to memory log file to analyze'
    )
    parser.add_argument(
        '--thread-id',
        type=str,
        help='Specific thread ID to analyze in detail'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for diagnostic report (default: print to stdout)'
    )
    parser.add_argument(
        '--auto-detect-log',
        action='store_true',
        help='Auto-detect the most recent log file for analysis'
    )
    
    args = parser.parse_args()
    
    # Auto-detect log file if requested
    log_file = args.log_file
    if args.auto_detect_log and not log_file:
        log_dir = Path('memory_logs')
        if log_dir.exists():
            log_files = list(log_dir.glob('*.log'))
            if log_files:
                log_file = str(max(log_files, key=os.path.getctime))
                print(f"📁 Auto-detected log file: {log_file}")
    
    # Extract thread ID from log file name if not provided
    thread_id = args.thread_id
    if not thread_id and log_file:
        # Extract from filename like memory_ray-10_20250927124520.log
        filename = Path(log_file).stem
        match = re.search(r'memory_([^_]+)_\d+', filename)
        if match:
            thread_id = match.group(1)
            print(f"🧵 Auto-detected thread ID: {thread_id}")
    
    # Run diagnostics
    diagnostics = MemoryDiagnostics(log_file=log_file, thread_id=thread_id)
    report = await diagnostics.run_full_diagnostics()
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📄 Diagnostic report saved to: {args.output}")
    else:
        print("\n" + report)
    
    # Exit with error code if critical issues found
    critical_issues = len([i for i in diagnostics.issues if i['severity'] == 'CRITICAL'])
    if critical_issues > 0:
        print(f"\n❌ {critical_issues} critical issues found. Memory system requires attention.")
        return 1
    else:
        print(f"\n✅ Diagnostic complete. {len(diagnostics.issues)} total issues found.")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)