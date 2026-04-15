import sys
sys.path.insert(0, 'backend')

import json
from modules.sentiment.sentiment import SentimentAnalyser, compute_hedge_ratio, compute_trajectory, split_sentences

# ── Test 1: Sentence splitter ─────────────────────────────────────────────────
text = "Revenue grew by 18% to Rs. 12,500 crore in Q3. However, margins came under pressure due to higher input costs. Management remains confident about FY24 guidance."
sents = split_sentences(text)
assert len(sents) == 3, "Expected 3 sentences, got " + str(len(sents))
print("split_sentences PASS - " + str(len(sents)) + " sentences")

# ── Test 2: Hedge ratio (phrase matching) ─────────────────────────────────────
hedge_text = "We expect margins may improve if conditions stabilize, subject to approval from regulators."
ratio = compute_hedge_ratio(hedge_text)
assert ratio > 0, "Expected non-zero hedge ratio"
print("compute_hedge_ratio PASS - ratio: " + str(ratio))

# ── Test 3: Document analysis (lexicon) ───────────────────────────────────────
analyser = SentimentAnalyser(force_lexicon=True)

positive_text = (
    "Revenue grew strongly with record profits. "
    "Management is confident and delivered solid growth. "
    "Earnings exceeded expectations and margins expanded."
)
result = analyser.analyse_document(positive_text)
assert result["pos_ratio"] > result["neg_ratio"], "Expected net positive"
assert result["tier"] == "lexicon"
assert result["sentence_results"] is None, "sentence_results should be None by default"
assert "confidence" in result
assert 0 <= result["sentiment_score"] <= 1
assert 0 <= result["confidence"] <= 1
print("analyse_document PASS (positive) - score: " + str(result["sentiment_score"]) + ", confidence: " + str(result["confidence"]))

# Test include_sentences flag
result_with_sents = analyser.analyse_document(positive_text, include_sentences=True)
assert result_with_sents["sentence_results"] is not None
assert len(result_with_sents["sentence_results"]) == 3
print("include_sentences PASS - " + str(len(result_with_sents["sentence_results"])) + " sentences returned")

negative_text = (
    "Revenue declined and losses mounted significantly. "
    "Challenging headwinds pressured margins severely. "
    "Management expressed concern over weakening demand and uncertainty."
)
result2 = analyser.analyse_document(negative_text)
assert result2["neg_ratio"] > result2["pos_ratio"], "Expected net negative"
print("analyse_document PASS (negative) - score: " + str(result2["sentiment_score"]) + ", neg_ratio: " + str(result2["neg_ratio"]))

# ── Test 4: Trajectory with configurable threshold ────────────────────────────
series_result = analyser.analyse_series([negative_text, negative_text, positive_text])
assert series_result["trajectory"] == "improving"
print("analyse_series PASS - trajectory: " + series_result["trajectory"] + ", scores: " + str(series_result["score_series"]))

traj = compute_trajectory([0.4, 0.42, 0.44], threshold=0.10)
assert traj == "stable", "With threshold=0.10 small improvement should be stable"
traj2 = compute_trajectory([0.4, 0.42, 0.44], threshold=0.01)
assert traj2 == "improving"
print("compute_trajectory threshold PASS")

# ── Test 5: Empty input ───────────────────────────────────────────────────────
empty_result = analyser.analyse_document("")
assert empty_result["tier"] == "none"
assert "empty_text" in empty_result["data_flags"][0]
assert empty_result["sentence_results"] is None
print("empty input PASS")

print()
print("ALL SENTIMENT SMOKE TESTS PASSED")
print()
print("=== SAMPLE OUTPUT ===")
print(json.dumps({k: v for k, v in result.items() if k != "sentence_results"}, indent=2))
