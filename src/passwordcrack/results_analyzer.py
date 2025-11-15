"""
Results analysis and statistics module.

Provides analysis of cracking attempts and generates reports.
NOTE: ALL REPORTING IS LOCAL ONLY - NO NETWORK
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import platform


class ResultsAnalyzer:
    """Analyzes cracking session results and generates reports."""
    
    def __init__(self, report_dir: Optional[Path] = None):
        """
        Initialize results analyzer.
        
        Args:
            report_dir: Directory for report files (default: reports/)
        """
        if report_dir is None:
            self.report_dir = Path.cwd() / "reports"
        else:
            self.report_dir = Path(report_dir)
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a completed session.
        
        Args:
            session_data: Session dictionary
            
        Returns:
            Analysis results
        """
        attempts = session_data.get("attempts", 0)
        found = session_data.get("found", False)
        created_at = session_data.get("created_at")
        last_updated = session_data.get("last_updated")
        
        # Calculate duration
        duration_seconds = 0
        if created_at and last_updated:
            try:
                start = datetime.fromisoformat(created_at)
                end = datetime.fromisoformat(last_updated)
                duration_seconds = (end - start).total_seconds()
            except Exception:
                pass
        
        # Calculate attempts per second
        attempts_per_sec = attempts / duration_seconds if duration_seconds > 0 else 0
        
        return {
            "session_id": session_data.get("session_id"),
            "attack_type": session_data.get("attack_type"),
            "algorithm": session_data.get("algorithm"),
            "success": found,
            "password_found": session_data.get("password") if found else None,
            "total_attempts": attempts,
            "duration_seconds": round(duration_seconds, 2),
            "attempts_per_second": round(attempts_per_sec, 2),
            "created_at": created_at,
            "completed_at": last_updated,
            "parameters": session_data.get("parameters", {})
        }
    
    def generate_report_json(
        self,
        session_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate JSON report.
        
        Args:
            session_data: Session data
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        analysis = self.analyze_session(session_data)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{session_data.get('session_id', timestamp)}.json"
        
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        return str(filepath)
    
    def generate_report_txt(
        self,
        session_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate plain text report.
        
        Args:
            session_data: Session data
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        analysis = self.analyze_session(session_data)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{session_data.get('session_id', timestamp)}.txt"
        
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("PASSWORD CRACKING SESSION REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Session ID: {analysis['session_id']}\n")
            f.write(f"Attack Type: {analysis['attack_type']}\n")
            f.write(f"Hash Algorithm: {analysis['algorithm']}\n")
            f.write(f"Success: {'YES' if analysis['success'] else 'NO'}\n")
            
            if analysis['success']:
                f.write(f"Password Found: {analysis['password_found']}\n")
            
            f.write(f"\nTotal Attempts: {analysis['total_attempts']:,}\n")
            f.write(f"Duration: {analysis['duration_seconds']:.2f} seconds\n")
            f.write(f"Speed: {analysis['attempts_per_second']:.2f} attempts/sec\n")
            
            f.write(f"\nStarted: {analysis['created_at']}\n")
            f.write(f"Completed: {analysis['completed_at']}\n")
            
            f.write("\nParameters:\n")
            for key, value in analysis['parameters'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\n" + "=" * 70 + "\n")
        
        return str(filepath)
    
    def generate_report_csv(
        self,
        sessions: List[Dict[str, Any]],
        filename: str = "sessions_summary.csv"
    ) -> str:
        """
        Generate CSV report for multiple sessions.
        
        Args:
            sessions: List of session data dictionaries
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Session ID",
                "Attack Type",
                "Algorithm",
                "Success",
                "Password",
                "Attempts",
                "Duration (s)",
                "Speed (attempts/s)",
                "Created At"
            ])
            
            # Data rows
            for session in sessions:
                analysis = self.analyze_session(session)
                writer.writerow([
                    analysis['session_id'],
                    analysis['attack_type'],
                    analysis['algorithm'],
                    'Yes' if analysis['success'] else 'No',
                    analysis['password_found'] or 'N/A',
                    analysis['total_attempts'],
                    analysis['duration_seconds'],
                    analysis['attempts_per_second'],
                    analysis['created_at']
                ])
        
        return str(filepath)
    
    def generate_report_html(
        self,
        session_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate HTML report.
        
        Args:
            session_data: Session data
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        analysis = self.analyze_session(session_data)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{session_data.get('session_id', timestamp)}.html"
        
        filepath = self.report_dir / filename
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PasswordCrack Suite - Session Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .success {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .failure {{
            color: #f44336;
            font-weight: bold;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 10px;
            margin: 20px 0;
        }}
        .info-label {{
            font-weight: bold;
            color: #666;
        }}
        .password {{
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 PasswordCrack Suite - Session Report</h1>
        
        <div class="info-grid">
            <div class="info-label">Session ID:</div>
            <div>{analysis['session_id']}</div>
            
            <div class="info-label">Attack Type:</div>
            <div>{analysis['attack_type']}</div>
            
            <div class="info-label">Hash Algorithm:</div>
            <div>{analysis['algorithm']}</div>
            
            <div class="info-label">Result:</div>
            <div class="{'success' if analysis['success'] else 'failure'}">
                {'✓ PASSWORD FOUND' if analysis['success'] else '✗ PASSWORD NOT FOUND'}
            </div>
            
            <div class="info-label">Total Attempts:</div>
            <div>{analysis['total_attempts']:,}</div>
            
            <div class="info-label">Duration:</div>
            <div>{analysis['duration_seconds']:.2f} seconds</div>
            
            <div class="info-label">Speed:</div>
            <div>{analysis['attempts_per_second']:.2f} attempts/second</div>
            
            <div class="info-label">Started:</div>
            <div>{analysis['created_at']}</div>
            
            <div class="info-label">Completed:</div>
            <div>{analysis['completed_at']}</div>
        </div>
        
        {'<div class="password"><strong>Password Found:</strong> ' + analysis['password_found'] + '</div>' if analysis['success'] else ''}
        
        <div class="footer">
            Generated by PasswordCrack Suite - Educational Use Only<br>
            Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
            System: {platform.system()} {platform.release()}
        </div>
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w') as f:
            f.write(html)
        
        return str(filepath)
    
    def generate_siem_json(
        self,
        session_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate SIEM-style JSON export for defensive exercises.
        
        Args:
            session_data: Session data
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        analysis = self.analyze_session(session_data)
        
        # SIEM-compatible event format
        siem_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "password_cracking_attempt",
            "severity": "high" if analysis['success'] else "medium",
            "source": "PasswordCrack Suite",
            "session_id": analysis['session_id'],
            "attack_details": {
                "method": analysis['attack_type'],
                "hash_algorithm": analysis['algorithm'],
                "attempts": analysis['total_attempts'],
                "success": analysis['success'],
                "duration_seconds": analysis['duration_seconds']
            },
            "system_info": {
                "platform": platform.system(),
                "release": platform.release(),
                "machine": platform.machine()
            }
        }
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"siem_event_{timestamp}.json"
        
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(siem_event, f, indent=2)
        
        return str(filepath)
