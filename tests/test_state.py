from app.state import ConversationStore, FlowState

def test_state_default_and_transition():
    s = ConversationStore(); assert s.get(7) == FlowState.IDLE
    s.set(7, FlowState.SOURCE); assert s.get(7) == FlowState.SOURCE
    s.set(7, FlowState.TARGET); assert s.get(7) == FlowState.TARGET

def test_reset():
    s = ConversationStore(); s.set(7, FlowState.TARGET); s.reset(7)
    assert s.get(7) == FlowState.IDLE
