import json
import random

# -------------------------
# JSON 読み込み
# -------------------------

with open("data/characters.json", encoding="utf-8") as f:
    characters = json.load(f)

with open("data/questions.json", encoding="utf-8") as f:
    questions = json.load(f)

# -------------------------
# 初期化
# -------------------------

scores = {c["id"]: 0 for c in characters}
unused_questions = list(questions.keys())

MAX_QUESTIONS = 20
WIN_DIFF = 3  # 1位と2位の差で確定

# -------------------------
# 判別式
# -------------------------

def update_score(character, attr, answer):
    value = character["attributes"].get(attr, False)
    return 1 if value == answer else -1

# -------------------------
# yes / no 入力
# -------------------------

def ask_yes_no(text):
    while True:
        ans = input(f"{text} (y/n): ").lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("y か n で答えてね")

# -------------------------
# メインループ
# -------------------------

print("=== Akiwalker 開始 ===")

for i in range(MAX_QUESTIONS):
    if not unused_questions:
        break

    attr = random.choice(unused_questions)
    unused_questions.remove(attr)

    answer = ask_yes_no(questions[attr]["text"])

    for c in characters:
        scores[c["id"]] += update_score(c, attr, answer)

    # スコア順位チェック
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if len(ranked) >= 2:
        if ranked[0][1] - ranked[1][1] >= WIN_DIFF:
            break

# -------------------------
# 結果表示
# -------------------------

winner_id = max(scores, key=scores.get)
winner = next(c for c in characters if c["id"] == winner_id)

print("\n=== 推測結果 ===")
print(f"あなたが思い浮かべているのは…")
print(f"👉 {winner['name']} ではありませんか？")

print("\n（スコア）")

ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

for cid, score in ranked:
    name = next(c["name"] for c in characters if c["id"] == cid)
    print(f"{name}: {score}")
