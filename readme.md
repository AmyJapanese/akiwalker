# Akiwalker

Akinator風のキャラクター推測ゲーム（軽量版）です。  
JSONで定義したキャラクター設定をもとに、  
Yes / No の質問をランダムに投げて推測します。

機械学習・重たいDBは使わず、  
**Python + JSONだけ**で動くことを目的にしています。

---

## 特徴

- Pythonのみで動作
- JSON駆動（キャラ・質問は外部定義）
- クローズドクエスチョン（Yes / No）
- 属性が未定義の場合は自動で False 扱い
- ランダム質問でも自然に収束する軽量ロジック

---

## 動作環境

- Python 3.10 以降（たぶん 3.8 でも可）
- 追加ライブラリ不要

---

## 使い方

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourname/akiwalker.git
cd akiwalker
````

### 2. data を用意する

このリポジトリでは、以下のファイルは **`.gitignore` 対象**です。

* `characters.json`
* `questions.json`

それぞれ自分で用意してください。

#### characters.json（例）

```json
[
  {
    "id": "emily_walker",
    "name": "エミリー・ウォーカー",
    "attributes": {
      "female": true,
      "magic_user": true,
      "america": true
    }
  }
]
```

#### questions.json（例）

```json
{
  "female": { "text": "女性ですか？" },
  "magic_user": { "text": "魔法使いですか？" },
  "america": { "text": "アメリカ出身ですか？" }
}
```

---

### 3. 実行

```bash
python akiwalker.py
```

---

## 設計メモ

* 質問ID = 属性名
* キャラの attributes に存在しない属性は False として扱う
* 完全一致検索ではなくスコアリング方式
* スコア差が一定以上ついた場合、早期に推測を行う

---

## 注意

* 本プロジェクトは個人制作・実験目的です
* Akinator とは無関係です
* データ（キャラ設定）は各自で管理してください

---

## ライセンス

MIT License
