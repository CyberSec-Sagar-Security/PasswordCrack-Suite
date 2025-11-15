"""
Session management module.

Handles saving, loading, and resuming cracking sessions.
NOTE: ALL DATA STORED LOCALLY ONLY - NO NETWORK
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class SessionManager:
    """Manages cracking session persistence and resume."""
    
    def __init__(self, session_dir: Optional[Path] = None):
        """
        Initialize session manager.
        
        Args:
            session_dir: Directory for session files (default: sessions/)
        """
        if session_dir is None:
            # Use sessions/ relative to project root
            self.session_dir = Path.cwd() / "sessions"
        else:
            self.session_dir = Path(session_dir)
        
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Dict[str, Any]] = None
        self.session_id: Optional[str] = None
    
    def create_session(
        self,
        attack_type: str,
        algorithm: str,
        hash_value: str,
        **kwargs
    ) -> str:
        """
        Create a new session.
        
        Args:
            attack_type: Type of attack (dictionary, bruteforce, etc.)
            algorithm: Hash algorithm
            hash_value: Target hash
            **kwargs: Additional session parameters
            
        Returns:
            Session ID
        """
        self.session_id = str(uuid.uuid4())
        
        self.current_session = {
            "session_id": self.session_id,
            "attack_type": attack_type,
            "algorithm": algorithm,
            "hash_value": hash_value,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "attempts": 0,
            "found": False,
            "password": None,
            "parameters": kwargs,
            "checkpoints": []
        }
        
        return self.session_id
    
    def save_session(self, encrypt: bool = False) -> str:
        """
        Save current session to disk.
        
        Args:
            encrypt: Whether to encrypt session data (requires security module)
            
        Returns:
            Path to saved session file
        """
        if not self.current_session:
            raise ValueError("No active session to save")
        
        filename = f"session_{self.session_id}.json"
        filepath = self.session_dir / filename
        
        # Update last saved timestamp
        self.current_session["last_saved"] = datetime.now().isoformat()
        
        data = json.dumps(self.current_session, indent=2)
        
        if encrypt:
            # Import security module for encryption
            from .security import SecurityManager
            security = SecurityManager()
            data = security.encrypt_data(data)
        
        with open(filepath, 'w' if not encrypt else 'wb') as f:
            if encrypt:
                f.write(data)
            else:
                f.write(data)
        
        return str(filepath)
    
    def load_session(self, session_id: str, encrypted: bool = False) -> Dict[str, Any]:
        """
        Load a session from disk.
        
        Args:
            session_id: Session ID to load
            encrypted: Whether session is encrypted
            
        Returns:
            Session data dictionary
        """
        filename = f"session_{session_id}.json"
        filepath = self.session_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        
        mode = 'rb' if encrypted else 'r'
        with open(filepath, mode) as f:
            data = f.read()
        
        if encrypted:
            # Import security module for decryption
            from .security import SecurityManager
            security = SecurityManager()
            data = security.decrypt_data(data)
        
        self.current_session = json.loads(data)
        self.session_id = session_id
        
        return self.current_session
    
    def update_session(self, **kwargs) -> None:
        """
        Update current session with new data.
        
        Args:
            **kwargs: Fields to update
        """
        if not self.current_session:
            raise ValueError("No active session")
        
        self.current_session.update(kwargs)
        self.current_session["last_updated"] = datetime.now().isoformat()
    
    def add_checkpoint(self, position: Any, data: Optional[Dict] = None) -> None:
        """
        Add a checkpoint to current session.
        
        Args:
            position: Current position (word index, attempt count, etc.)
            data: Optional checkpoint data
        """
        if not self.current_session:
            raise ValueError("No active session")
        
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "position": position,
            "attempts": self.current_session.get("attempts", 0),
            "data": data or {}
        }
        
        self.current_session["checkpoints"].append(checkpoint)
    
    def get_last_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Get the last checkpoint from current session.
        
        Returns:
            Last checkpoint dictionary or None
        """
        if not self.current_session or not self.current_session["checkpoints"]:
            return None
        
        return self.current_session["checkpoints"][-1]
    
    def list_sessions(self) -> list:
        """
        List all saved sessions.
        
        Returns:
            List of session summaries
        """
        sessions = []
        
        for filepath in self.session_dir.glob("session_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                sessions.append({
                    "session_id": data.get("session_id"),
                    "attack_type": data.get("attack_type"),
                    "algorithm": data.get("algorithm"),
                    "created_at": data.get("created_at"),
                    "status": data.get("status"),
                    "found": data.get("found", False),
                    "filename": filepath.name
                })
            except Exception:
                continue
        
        return sorted(sessions, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a saved session.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        filename = f"session_{session_id}.json"
        filepath = self.session_dir / filename
        
        if filepath.exists():
            filepath.unlink()
            
            if self.session_id == session_id:
                self.current_session = None
                self.session_id = None
            
            return True
        
        return False
    
    def export_session(self, session_id: str, output_path: str) -> str:
        """
        Export a session to a specific location.
        
        Args:
            session_id: Session ID to export
            output_path: Destination path
            
        Returns:
            Path to exported file
        """
        filename = f"session_{session_id}.json"
        filepath = self.session_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        
        import shutil
        shutil.copy(filepath, output_path)
        
        return output_path
    
    def import_session(self, input_path: str) -> str:
        """
        Import a session from a file.
        
        Args:
            input_path: Path to session file
            
        Returns:
            Session ID of imported session
        """
        import shutil
        
        # Load to validate
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        session_id = data.get("session_id", str(uuid.uuid4()))
        filename = f"session_{session_id}.json"
        filepath = self.session_dir / filename
        
        shutil.copy(input_path, filepath)
        
        return session_id
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information dictionary
        """
        session = self.load_session(session_id)
        
        return {
            "session_id": session.get("session_id"),
            "attack_type": session.get("attack_type"),
            "algorithm": session.get("algorithm"),
            "created_at": session.get("created_at"),
            "last_updated": session.get("last_updated"),
            "status": session.get("status"),
            "attempts": session.get("attempts"),
            "found": session.get("found"),
            "password": session.get("password"),
            "checkpoint_count": len(session.get("checkpoints", [])),
            "parameters": session.get("parameters", {})
        }
