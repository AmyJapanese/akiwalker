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

MAX_QUESTIONS = len(questions)
WIN_DIFF = 5  # 1位と2位の差で確定
TOP_N = 5 #最大の行数
id_to_name = {c["id"]: c["name"] for c in characters}

# -------------------------
# alive_idが持つ属性集め
# -------------------------

def collect_true_attributes(characters, alive_ids):
    attrs = set()
    for c in characters:
        if c["id"] not in alive_ids:
            continue
        for attr, value in c["attributes"].items():
            if value is True:
                attrs.add(attr)
    return attrs

# -------------------------
# 質問候補作成
# -------------------------

def select_next_question(characters, alive_ids, unused_questions, questions):
    true_attrs = collect_true_attributes(characters, alive_ids)

    # 質問に使える属性だけ残す
    candidates = [
        attr for attr in true_attrs
        if attr in unused_questions and attr in questions
    ]

    # 候補があればそこから選ぶ
    if candidates:
        return random.choice(candidates)

    # なければフォールバック（完全ランダム）
    return random.choice(list(unused_questions))

# -------------------------
# 判別式（5段階・属性は True/False）
# -------------------------

def update_score(character, attr, answer_value):
    # わからないは即スキップ
    if answer_value == 0:
        return 0

    # JSONに無い属性は False 扱い
    char_value = character["attributes"].get(attr, False)

    # プレイヤー回答が肯定側か否定側か
    answer_is_positive = answer_value > 0  # はい / 多分そう
    answer_strength = abs(answer_value)    # 1 or 2

    # キャラ属性と一致しているか
    if char_value == answer_is_positive:
        return answer_strength
    else:
        return -answer_strength

# -------------------------
# 5段階入力
# -------------------------

def ask_answer(text ,question_number):
    prompt = (
        f"Q.{question_number}.{text}\n"
        "  [y] はい\n"
        "  [p] 多分そう\n"
        "  [u] わからない\n"
        "  [m] 多分違う\n"
        "  [n] いいえ\n"
        "> "
    )

    while True:
        ans = input(prompt).lower()
        if ans in ("y", "yes"):
            return 2
        if ans in ("p", "probably", "maybe"):
            return 1
        if ans in ("u", "unknown", "idk"):
            return 0
        if ans in ("m", "probably_not"):
            return -1
        if ans in ("n", "no"):
            return -2
        print("y / p / u / m / n のどれかで答えてね")

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

    attr = select_next_question(
        characters,
        alive_ids,
        unused_questions,
        questions
    )
    unused_questions.remove(attr)

    answer = ask_answer(questions[attr]["text"], i+1)

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

    if (i + 1) % 5 == 0: #5問ごとに候補を表示
        print(f"\n--- 現在の候補数：{len(alive_ids)} 人 ---\n")
# -------------------------
# 結果表示
# -------------------------

winner_id = max(alive_ids, key=lambda cid: scores[cid])
winner = next(c for c in characters if c["id"] == winner_id)

print("\n=== 推測結果 ===")
print(f"あなたが思い浮かべているのは…")
print(f"→ {winner['name']} ではありませんか？")

print("\n（スコア）")

ranked = sorted(
    ((cid, scores[cid]) for cid in alive_ids),
    key=lambda x: x[1],
    reverse=True
)

for cid, score in ranked:
    name = next(c["name"] for c in characters if c["id"] == cid)
    print(f"{name}: {score}")