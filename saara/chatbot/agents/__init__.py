from .attendance_agent import AttendanceAgent
from .fees_agent import FeesAgent
from .assignment_agent import AssignmentAgent
from .results_agent import ResultsAgent
from .teacher_agents import (
    TeacherAttendanceAgent,
    TeacherAssignmentAgent,
    TeacherResultsAgent
)
from .admin_agents import (
    AdminAttendanceAgent,
    AdminFeesAgent,
    AdminAssignmentAgent,
    AdminResultsAgent
)

__all__ = [
    # Student agents
    'AttendanceAgent',
    'FeesAgent',
    'AssignmentAgent',
    'ResultsAgent',
    # Teacher agents
    'TeacherAttendanceAgent',
    'TeacherAssignmentAgent',
    'TeacherResultsAgent',
    # Admin agents
    'AdminAttendanceAgent',
    'AdminFeesAgent',
    'AdminAssignmentAgent',
    'AdminResultsAgent',
]

