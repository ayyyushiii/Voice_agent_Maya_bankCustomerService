# Banking tools for Maya voice agent

from agent.tools.verify_user import verify_user
from agent.tools.get_balance import get_balance
from agent.tools.block_card import block_card
from agent.tools.create_complaint import create_complaint
from agent.tools.escalate import escalate
from agent.tools.get_branch_hours import get_branch_hours

ALL_TOOLS = [
    verify_user,
    get_balance,
    block_card,
    create_complaint,
    escalate,
    get_branch_hours,
]
