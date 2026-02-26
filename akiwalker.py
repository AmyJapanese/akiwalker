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
CUT_RATE = 0.10     # 下位10%
MIN_ALIVE = 2       # 最低限残す人数（安全装置）

scores = {c["id"]: 0 for c in characters}
alive_ids = {c["id"] for c in characters}
unused_questions = list(questions.keys())

MAX_QUESTIONS = len(questions)
WIN_DIFF = 5  # 1位と2位の差で確定
TOP_N = 5     # 最大の行数（未使用）
id_to_name = {c["id"]: c["name"] for c in characters}

# -------------------------
# 状態スナップショット（1問戻る用）
# -------------------------

def snapshot_state(scores, alive_ids, unused_questions):
    return {
        "scores": scores.copy(),
        "alive_ids": set(alive_ids),
        "unused_questions": list(unused_questions),
        "rng_state": random.getstate(),
    }

def restore_state(state):
    random.setstate(state["rng_state"])
    return (
        state["scores"].copy(),
        set(state["alive_ids"]),
        list(state["unused_questions"]),
    )

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
# 5段階入力（＋戻る / （隠し）Redo）
# -------------------------

def ask_answer(text, question_number, allow_back=False, allow_redo=False):
    # Redo は “隠しキー” なので通常プロンプトには出さない
    lines = [
        f"Q.{question_number}.{text}",
        "  [y] はい",
        "  [p] 多分そう",
        "  [u] わからない",
        "  [m] 多分違う",
        "  [n] いいえ",
    ]
    if allow_back:
        lines.append("  [b] 1問前に戻る")
    prompt = "\n".join(lines) + "\n> "

    while True:
        ans = input(prompt).lower()

        # （隠し）Redo
        if ans in ("f", "redo"):
            if allow_redo:
                return "REDO"
            print("（やり直し履歴がありません）")
            continue

        # Undo（2問目以降のみ）
        if ans in ("b", "back"):
            if allow_back:
                return "BACK"
            print("（まだ戻れません：2問目以降で使えます）")
            continue

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

history = [snapshot_state(scores, alive_ids, unused_questions)]  # 0問回答時点の状態
asked_attrs = []  # 回答済みの質問（attr）を順番に保持
forced_attr = None  # 戻った直後に「その質問」をもう一度聞くため
redo_stack = []  # （隠し）Redo 用：Undoした履歴を積む

while True:
    # 終了条件
    if not unused_questions:
        break

    # 残り1人なら即確定
    if len(alive_ids) == 1:
        break

    if len(asked_attrs) >= MAX_QUESTIONS:
        break

    qnum = len(asked_attrs) + 1

    # 質問選択（戻った直後は同じ質問をもう一度）
    if forced_attr is not None and forced_attr in unused_questions and forced_attr in questions:
        attr = forced_attr
        forced_attr = None
    else:
        attr = select_next_question(
            characters,
            alive_ids,
            unused_questions,
            questions
        )

    answer = ask_answer(
        questions[attr]["text"],
        qnum,
        allow_back=(qnum >= 2),
        allow_redo=(len(redo_stack) > 0),
    )

    # -------------------------
    # （隠し）Redo
    # -------------------------
    if answer == "REDO":
        if not redo_stack:
            # ask_answer側で基本弾くけど安全装置
            forced_attr = attr
            continue

        redo_attr, redo_state = redo_stack.pop()

        # 「Undoを取り消す」＝ state_after を復元
        scores, alive_ids, unused_questions = restore_state(redo_state)
        asked_attrs.append(redo_attr)
        history.append(redo_state)

        # もう答え直しではないので強制出題は解除
        forced_attr = None
        continue

    # -------------------------
    # 1問前に戻る
    # -------------------------
    if answer == "BACK":
        if not asked_attrs:
            print("（最初の問題なので、これ以上戻れません）")
            continue

        # 直前の質問（＝1問前）を未回答扱いに戻す
        forced_attr = asked_attrs.pop()

        # Redo 用に「巻き戻す前の状態（＝直前回答後）」を退避
        undone_state = history.pop()
        redo_stack.append((forced_attr, undone_state))

        # 状態を「1問前のさらに前（＝巻き戻し後）」へ復元
        scores, alive_ids, unused_questions = restore_state(history[-1])

        # 念のため：質問がunusedに戻っていなければ戻す
        if forced_attr not in unused_questions:
            unused_questions.append(forced_attr)

        continue

    # -------------------------
    # 通常回答：質問を使用済みにする
    # -------------------------
    # ここで回答が確定したので、Redo履歴は破棄（分岐が生まれるため）
    redo_stack.clear()

    if attr in unused_questions:
        unused_questions.remove(attr)
    asked_attrs.append(attr)

    # スコア更新（生存者のみ）
    for c in characters:
        cid = c["id"]
        if cid not in alive_ids:
            continue
        scores[cid] += update_score(c, attr, answer)

    # -------------------------
    # 脱落ロジック
    # -------------------------
    if qnum >= CUTOFF_START and len(alive_ids) > MIN_ALIVE:
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

    if (qnum % 5) == 0:  # 5問ごとに候補を表示
        print(f"\n--- 現在の候補数：{len(alive_ids)} 人 ---\n")

    # ここまでの状態を保存（＝この問題に回答し終わった時点）
    history.append(snapshot_state(scores, alive_ids, unused_questions))

    if len(ranked) >= 2:
        if ranked[0][1] - ranked[1][1] >= WIN_DIFF:
            break

# -------------------------
# 結果表示
# -------------------------

if not alive_ids:
    print("\n=== 推測結果 ===")
    print("候補が0人になってしまったので終了します（設定を見直してね）")
else:
    winner_id = max(alive_ids, key=lambda cid: scores[cid])
    winner = next(c for c in characters if c["id"] == winner_id)

    print("\n=== 推測結果 ===")
    print("あなたが思い浮かべているのは…")
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
