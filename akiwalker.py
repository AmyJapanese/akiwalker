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

CUTOFF_START = 3    # 何問目から脱落を始めるか
CUT_RATE = 0.10    # 下位10%
MIN_ALIVE = 2      # 最低限残す人数（安全装置）

scores = {c["id"]: 0 for c in characters}
alive_ids = {c["id"] for c in characters}
unused_questions = list(questions.keys())

MAX_QUESTIONS = 20
WIN_DIFF = 3  # 1位と2位の差で確定
TOP_N = 5 #最大の行数
id_to_name = {c["id"]: c["name"] for c in characters}

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

    # 残り1人なら即確定
    if len(alive_ids) == 1:
        break

    attr = random.choice(unused_questions)
    unused_questions.remove(attr)

    answer = ask_yes_no(questions[attr]["text"])

    # スコア更新（生存者のみ）
    for c in characters:
        cid = c["id"]
        if cid not in alive_ids:
            continue
        scores[cid] += update_score(c, attr, answer)

    # -------------------------
    # 脱落ロジック
    # -------------------------
    if i + 1 >= CUTOFF_START and len(alive_ids) > MIN_ALIVE:
        # 生存者だけでランキング（昇順）
        ranked_alive = sorted(
            ((cid, scores[cid]) for cid in alive_ids),
            key=lambda x: x[1]
        )

        cut = int(len(ranked_alive) * CUT_RATE)

        if cut > 0:
            cut = min(cut, len(ranked_alive) - MIN_ALIVE)
            for cid, _ in ranked_alive[:cut]:
                alive_ids.remove(cid)

    # -------------------------
    # 早期確定（任意：残すなら）
    # -------------------------
    ranked = sorted(
        ((cid, scores[cid]) for cid in alive_ids),
        key=lambda x: x[1],
        reverse=True
    )

    if len(ranked) >= 2:
        if ranked[0][1] - ranked[1][1] >= WIN_DIFF:
            break

# -------------------------
# 結果表示
# -------------------------

winner_id = max(alive_ids, key=lambda cid: scores[cid])
winner = next(c for c in characters if c["id"] == winner_id)

print("\n=== 推測結果 ===")
print(f"あなたが思い浮かべているのは…")
print(f"👉 {winner['name']} ではありませんか？")

print("\n（スコア TOP）")

ranked = sorted(
    ((cid, scores[cid]) for cid in alive_ids),
    key=lambda x: x[1],
    reverse=True
)

for cid, score in ranked[:TOP_N]:
    print(f"{id_to_name[cid]}: {score}")

rest = len(ranked) - TOP_N
if rest > 0:
    print(f"...他 {rest} 件")
