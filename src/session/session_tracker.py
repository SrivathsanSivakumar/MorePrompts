### Identifies and groups [UsageData] into sessions

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from data.log_reader import UsageData

@dataclass
class Session:
    session_id: str
    start_time: datetime
    entries: List[UsageData]

    @property
    def end_time(self) -> datetime:
        """Tells when session expires - 5 hours from start"""
        return self.start_time + timedelta(hours=5)
    
    @property
    def is_active(self) -> bool:
        """checks if session is within 5 hours window"""
        return datetime.now(timezone.utc) < self.end_time
    
    @property
    def total_input_usage(self) -> tuple:
        """Returns total input tokens in session"""
        token_usage, dollar_cost = 0, 0
        for entry in self.entries:
            token_usage += entry.input_tokens
            dollar_cost += entry.input_tokens_cost[0]
        return token_usage, dollar_cost
    
    @property
    def total_output_usage(self) -> tuple:
        """Returns total output tokens in session"""
        token_usage, dollar_cost = 0, 0
        for entry in self.entries:
            token_usage += entry.output_tokens
            dollar_cost += entry.output_tokens_cost[0]
        return token_usage, dollar_cost
    
    @property
    def total_tokens(self) -> int:
        """Returns total input + output tokens in session"""
        inp_tokens, inp_cost = self.total_input_usage
        out_tokens, out_cost = self.total_output_usage
        return (inp_tokens + out_tokens, inp_cost + out_cost)
    
class SessionTracker:
    def __init__(self):
        self.sessions: List[Session] = []

    def generate_session_id(self, timestamp: datetime) -> str:
        """Generate unique session id based on timestamp"""
        return f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    def get_active_sessions(self) -> List[Session]:
        return [session for session in self.sessions if session.is_active]
    
    def get_current_session(self) -> Session:
        """Get most recent session"""
        active = self.get_active_sessions()
        return active[-1] if active else None

    def build_sessions(self, entries: List[UsageData]):
        """Build session windows from usage entries
        
            Args:
                entries: List of UsageData objects with timestamps

        """
        self.sessions=[]
        current_session: Session = None

        if not entries:
            return
        
        # sort UsageData objects by time created
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)
        
        for entry in sorted_entries:
            if current_session is None:
                current_session = Session(
                    session_id=self.generate_session_id(entry.timestamp),
                    start_time=entry.timestamp,
                    entries=[entry]
                )
                self.sessions.append(current_session)

            # if entry is after session block, create a new session
            elif entry.timestamp > current_session.end_time:
                current_session = Session(
                    session_id=self.generate_session_id(entry.timestamp),
                    start_time=entry.timestamp,
                    entries=[entry]
                )
                self.sessions.append(current_session)
            
            # add entry to existing session
            else:
                current_session.entries.append(entry)