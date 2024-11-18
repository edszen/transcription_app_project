# Business logic & session state management

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import json
import os

# Custom exceptions for better error handling
class SessionError(Exception):
    """Base exception class for all session-related errors"""
    pass

class SessionLoadError(SessionError):
    """Raised when there's an error loading a session"""
    pass

class SessionSaveError(SessionError):
    """Raised when there's an error saving a session"""
    pass

@dataclass
class SessionData:
    """Data class representing a session's data"""
    # Required fields
    transcript: str
    chat_history: List[Dict[str, str]]
    date_modified: datetime
    
    # Optional fields with defaults
    name: str = ""
    version: str = "1.0"
    
    @classmethod
    def create_empty(cls) -> 'SessionData':
        """Creates an empty session with default values"""
        return cls(
            transcript="",
            chat_history=[],
            date_modified=datetime.now(),
            name="New Session"
        )
    
    def to_dict(self) -> Dict:
        """Convert session data to dictionary for serialization"""
        return {
            'transcript': self.transcript,
            'chat_history': self.chat_history,
            'date_modified': self.date_modified.isoformat(),
            'name': self.name,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionData':
        """Create SessionData instance from dictionary"""
        try:
            return cls(
                transcript=data['transcript'],
                chat_history=data['chat_history'],
                date_modified=datetime.fromisoformat(data['date_modified']),
                name=data.get('name', ""),
                version=data.get('version', "1.0")
            )
        except (KeyError, ValueError) as e:
            raise SessionLoadError(f"Failed to load session data: {e}")

class SessionState(QObject):
    """
    Manages the state of the current session and provides signals for state changes.
    Using QObject for Qt's signal/slot mechanism.
    """
    # Signals for state changes
    session_modified = pyqtSignal(bool) # Emits modified state
    session_saved = pyqtSignal(str)  # Emits path
    session_error = pyqtSignal(str)  # Emits error message
    session_loaded = pyqtSignal(SessionData) # Emits session data
    session_changed = pyqtSignal(SessionData)
    session_cleared = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._current_session: Optional[SessionData] = None
        self._current_path: Optional[str] = None
        self._is_modified: bool = False
        self._last_saved_state: Optional[str] = None
        
    @property
    def current_session(self) -> Optional[SessionData]:
        return self._current_session
    
    @property
    def is_modified(self) -> bool:
        """Check if current session has unsaved changes"""
        return self._is_modified
    
    @property
    def current_path(self) -> Optional[str]:
        """Get current session file path"""
        return self._current_path
    
    def set_current_session(self, session: SessionData, path: Optional[str] = None):
        """Update current session and emit change signal"""
        self._current_session = session
        self._current_path = path
        self._last_saved_state = self._get_state_hash(session)
        self._is_modified = False
        self.session_changed.emit(session)
        self.session_modified.emit(False)
    
    def update_state(self, transcript: str, chat_history: List[Dict]):
        """Update current session state and check for modifications"""
        if not self._current_session:
            self._current_session = SessionData.create_empty()
        
        self._current_session.transcript = transcript
        self._current_session.chat_history = chat_history
        
        current_state = self._get_state_hash(self._current_session)
        is_modified = current_state != self._last_saved_state
        
        if self._is_modified != is_modified:
            self._is_modified = is_modified
            self.session_modified.emit(is_modified)
    
    def mark_as_saved(self, path: str):
        """Mark current session as saved and update path"""
        self._current_path = path
        self._is_modified = False
        self._last_saved_state = self._get_state_hash(self._current_session)
        self.session_saved.emit(path)
        self.session_modified.emit(False)
    
    def clear(self):
        """Clear current session state"""
        self._current_session = None
        self._current_path = None
        self._is_modified = False
        self._last_saved_state = None
        self.session_cleared.emit()
        self.session_modified.emit(False)
    
    def _get_state_hash(self, session: Optional[SessionData]) -> str:
        """Get a hash of the session state for comparison"""
        if not session:
            return ""
        state_str = json.dumps({
            'transcript': session.transcript,
            'chat_history': session.chat_history
        }, sort_keys=True)
        return hash(state_str)

class SessionManager(QObject):
    """Manages session operations and coordinates with UI"""
    
    session_loaded = pyqtSignal(object)  # Emits SessionData
    session_saved = pyqtSignal(str)      # Emits path
    session_error = pyqtSignal(str)      # Emits error message
    
    def __init__(self, file_ops):
        super().__init__()
        self.file_ops = file_ops
        self._state = SessionState()
        
        # Setup auto-save timer (5 minutes)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setInterval(300000)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start()
        
        # Connect state signals to manager signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect internal state signals to manager signals"""
        self._state.session_loaded.connect(self.session_loaded)
        self._state.session_saved.connect(self.session_saved)

    def new_session(self) -> None:
        """Create a new empty session"""
        try:
            new_session = SessionData.create_empty()
            self._state.set_current_session(new_session)
        except Exception as e:
            self._handle_error(f"Failed to create new session: {e}")

    def load_session(self, path: Optional[str] = None) -> Optional[SessionData]:
        """Load a session from file"""
        try:
            if not path:
                path, _ = self.file_ops.get_open_file_path(
                    "Load Session",
                    self.file_ops.get_default_directory('sessions'),
                    "Session Files (*.gss)"
                )
                if not path:
                    return None

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = SessionData.from_dict(data)
            self._state.set_current_session(session, path)
            return session

        except Exception as e:
            self._handle_error(f"Failed to load session: {e}")
            return None

    def save_session(self, transcript: str, chat_history: List[Dict], 
                    path: Optional[str] = None) -> bool:
        """Save current session"""
        try:
            # Update session data
            self._state.update_state(transcript, chat_history)
            current_session = self._state.current_session
            if not current_session:
                current_session = SessionData.create_empty()
            
            # Get save path
            save_path = path or self._state.current_path
            if not save_path:
                save_path, _ = self.file_ops.get_save_file_path(
                    "Save Session",
                    self.file_ops.get_default_directory('sessions'),
                    "Session Files (*.gss)"
                )
                if not save_path:
                    return False

            # Ensure proper extension and save
            save_path = self.file_ops.ensure_file_extension(save_path, '.gss')
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(current_session.to_dict(), f, indent=2)

            self._state.mark_as_saved(save_path)
            return True

        except Exception as e:
            self._handle_error(f"Failed to save session: {e}")
            return False

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return self._state.is_modified

    def update_session_state(self, transcript: str, chat_history: List[Dict]):
        """Update current session state"""
        self._state.update_state(transcript, chat_history)

    def _auto_save(self):
        """Perform auto-save if needed"""
        if self._state.is_modified and self._state.current_session:
            try:
                backup_path = os.path.join(
                    self.file_ops.sessions_dir,
                    f"autosave_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gss"
                )
                self.save_session(
                    self._state.current_session.transcript,
                    self._state.current_session.chat_history,
                    backup_path
                )
            except Exception as e:
                print(f"Auto-save failed: {e}")

    def _handle_error(self, message: str):
        """Handle errors and emit signal"""
        print(f"SessionManager error: {message}")
        self.session_error.emit(str(message))

    def cleanup(self):
        """Cleanup resources"""
        if self._auto_save_timer.isActive():
            self._auto_save_timer.stop()
            if self._state.is_modified:
                self._auto_save()