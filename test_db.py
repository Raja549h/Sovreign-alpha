import sys
sys.path.insert(0, 'C:/Users/lokes/Downloads/project/sovereign-alpha')
from database import get_connection, init_pool
init_pool()
from dashboard.app import get_decisions
decisions = get_decisions()
print("Decisions length:", len(decisions))
if decisions:
    print(decisions[0])
