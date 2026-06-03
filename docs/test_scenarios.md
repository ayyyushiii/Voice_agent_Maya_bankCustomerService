# Test Scenarios

## 1. Basic call flow

1. Start backend, agent, and frontend
2. Enter name "Test User" → **Start Call**
3. Wait for Maya greeting
4. Verify connection status = `connected`, agent status = `online`
5. End call → status returns to idle

**Expected:** Greeting heard, timeline shows `room_created`, `agent_joined`, `user_joined`

---

## 2. Balance inquiry (with verification)

1. Start call
2. Say: "What is my account balance?"
3. Maya asks for verification
4. Provide phone: `9999999999`, birth year: `1990`
5. Maya reads balance: ₹52,430

**Expected:** `verify_user` → `get_balance` in timeline; tool results in debug panel

---

## 3. Balance without verification

1. Start call
2. Trigger balance before verifying (if agent skips verification prompt)

**Expected:** `get_balance` returns error "Verification required"

---

## 4. Card blocking

1. Verify identity (phone + birth year)
2. Say: "Please block my debit card"
3. Confirm when asked

**Expected:** `block_card` success; card marked blocked in mock DB

---

## 5. UPI complaint

1. Say: "My UPI payment failed but money was debited"
2. Describe the issue

**Expected:** `create_complaint` with complaint ID returned

---

## 6. Branch hours (no verification)

1. Ask: "What are your branch timings?"

**Expected:** `get_branch_hours` → "Mon-Sat 9:00 AM - 5:00 PM"

---

## 7. Escalation

1. Say: "I want to speak to a human agent"

**Expected:** `escalate` tool called; wait time message

---

## 8. Interruption (barge-in)

1. Start call, let Maya speak
2. Interrupt mid-sentence by speaking

**Expected:** `interruption_detected` in timeline; Maya stops and listens

---

## 9. Silence handling

1. Start call, do not speak for 10+ seconds

**Expected:** Maya says "Are you still there?"; `silence_timeout` event (count: 1)

2. Stay silent another 10+ seconds

**Expected:** Call ends gracefully; `call_ended` with reason `silence_timeout`

---

## 10. Tool failure simulation

1. Start call
2. Enable **Tool Failure** toggle in UI
3. Attempt verified balance check

**Expected:** Tool returns simulated failure; `tool_failure` in timeline

---

## 11. Call replay

1. Complete a call with some conversation
2. Navigate to `/debug/{callId}`

**Expected:** Transcript, timeline, latency, tools, summary displayed

---

## 12. Mute / unmute

1. During call, click **Mute**
2. Speak — agent should not respond to muted audio
3. Click **Unmute** — agent responds again

**Expected:** Mute state toggles; no STT events while muted

---

## 13. Wrong verification

1. Provide phone `9999999999`, birth year `1985` (wrong)

**Expected:** Verification fails; balance not accessible

---

## 14. Angry user

1. Say: "This is ridiculous, your service is terrible!"

**Expected:** Maya responds calmly; may offer escalation
