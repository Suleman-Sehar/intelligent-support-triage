import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from guardrails import GuardrailPipeline

pipe = GuardrailPipeline(confidence_threshold=0.75, llm_classifier=None, use_llm=False)

vague_tickets = [
    ("help", ""),
    ("it's not working", "it is not working"),
    ("?", "???"),
    ("asdf", ""),
    ("please fix", "please fix this issue"),
]

print("=== VAGUE TICKET CHECK ===")
for subject, body in vague_tickets:
    result = pipe.classify_with_guardrails(subject, body)
    output = {
        "issue_type": result.issue_type,
        "team": result.team,
        "confidence": round(result.confidence, 4),
        "human_review": result.human_review,
        "reasoning": result.reasoning[:120]
    }
    print(f"\nInput: subject='{subject}', body='{body}'")
    print(f"Output: {json.dumps(output, indent=2)}")
    assert result.human_review == True, f"FAIL: {subject} was not flagged!"
    print("  -> needs_human_review = true [OK]")

# Edge case set
print("\n=== 10-TICKET AMBIGUOUS EDGE-CASE SET ===")
import csv
edge_path = Path(__file__).parent / "data" / "edge_cases.csv"
edge_tickets = []
with open(edge_path, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        edge_tickets.append(row)

flagged = 0
for tc in edge_tickets:
    result = pipe.classify_with_guardrails(tc["subject"], tc["body"])
    status = "FLAGGED" if result.human_review else "AUTO-ROUTED"
    if result.human_review:
        flagged += 1
    print(f"  {tc['id']}: {status} (conf={result.confidence:.2f}, reason={result.reasoning[:80]})")

not_flagged = len(edge_tickets) - flagged
print(f"\nReview rate: {flagged}/{len(edge_tickets)} ({flagged/len(edge_tickets)*100:.1f}%)")
print(f"Auto-routed: {not_flagged}")
if not_flagged > 0:
    print("WARNING: Some vague tickets were auto-routed - investigating below")
else:
    print("All edge cases flagged for review [OK]")