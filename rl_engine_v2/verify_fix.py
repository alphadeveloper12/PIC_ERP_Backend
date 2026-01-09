import sys
import os

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

try:
    from rl_engine_v2.rl_feedback_v2 import RLFeedbackHandler
    print("Attempting to initialize RLFeedbackHandler...")
    handler = RLFeedbackHandler()
    print("SUCCESS: RLFeedbackHandler initialized correcly.")
except Exception as e:
    print(f"FAILURE: Could not initialize RLFeedbackHandler. Error: {e}")
    sys.exit(1)
