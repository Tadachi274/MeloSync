import pandas as pd
from openai import OpenAI
import os
import time
import numpy as np

# --- 1. OpenAIクライアントの初期化 ---
# 環境変数 `OPENAI_API_KEY` を設定してください
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print(f"OpenAIクライアントの初期化に失敗しました: {e}")
    client = None

# --- 2. 予測のための関数定義 ---

def create_transition_prompt(current_emotion, track_name, artist_name, emotion_choices):
    """感情遷移を予測させるためのプロンプトを生成する関数"""
    choices_str = ", ".join(emotion_choices)
    user_prompt = f"""
ある人は現在「{current_emotion}」という感情です。
その人が、これから「{artist_name}」の「{track_name}」という曲を聴きます。

この曲を聴き終えた後、その人の感情は以下の選択肢のうちどれに最も近くなる可能性が高いですか？

選択肢: {choices_str}
"""
    return user_prompt

def predict_emotion_transition(prompt, emotion_choices):
    """プロンプトをOpenAI APIに送り、予測された感情を取得する関数"""
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"あなたは、音楽が人間の感情に与える影響を分析する専門家です。提示された情報に基づき、最も可能性の高い感情を選択肢の中から一つだけ選び、その単語のみを回答してください。例えば「{emotion_choices[0]}」のように答えてください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )
        text_response = response.choices[0].message.content.strip()
        for choice in emotion_choices:
            if choice in text_response:
                return choice
        print(f"  - 解析不能な回答: {text_response}")
        return None
    except Exception as e:
        print(f"  - APIエラー: {e}")
        return None

# --- 3. データ準備 ---
dataset_files = {
    'Happy/Excited': 'data/music_data_happy_normalized_encoded.csv',
    'Angry/Frustrated': 'data/music_data_angry_normalized_encoded.csv',
    'Tired/Sad': 'data/music_data_tired_normalized_encoded.csv',
    'Relax/Chill': 'data/music_data_relax_normalized_encoded.csv'
}
emotion_list = list(dataset_files.keys())
all_songs_list = []

print("データを読み込んでいます...")
for emotion, file_path in dataset_files.items():
    try:
        df = pd.read_csv(file_path)
        df_subset = df[['アーティスト', '曲名（optional）']].copy()
        # 将来の感情を予測するための正解ラベルとして、現在の感情と同じものを設定
        df_subset['future_emotion'] = emotion
        all_songs_list.append(df_subset)
    except FileNotFoundError:
        print(f"警告: ファイルが見つかりません - {file_path}")

if not all_songs_list:
    raise ValueError("データファイルが一つも見つかりませんでした。処理を中断します。")

# 全てのデータを結合し、開始感情をランダムに割り当てる
master_df = pd.concat(all_songs_list, ignore_index=True).sample(n=60, random_state=42)
master_df['current_emotion'] = np.random.choice(emotion_list, size=len(master_df))


# --- 4. 感情遷移の予測と評価 ---

# <--- 変更点 1: 全ての予測結果を保存するリストをループの前に用意
all_predictions = []

print(f"{len(master_df)}曲の予測を開始します...")
# 各曲に対してループ
for index, row in master_df.iterrows():
    current_emotion = row["current_emotion"]
    track_name = row['曲名（optional）']
    artist_name = row['アーティスト']
    true_future_emotion = row['future_emotion'] # 正解ラベル

    print(f"\n({index + 1}/{len(master_df)}) 曲: {track_name} by {artist_name}")
    print(f"  現在の感情: '{current_emotion}' -> 予測 (正解: '{true_future_emotion}')")
    
    prompt = create_transition_prompt(current_emotion, track_name, artist_name, emotion_list)
    predicted_emotion = predict_emotion_transition(prompt, emotion_list)
    
    if predicted_emotion:
        print(f"    -> 予測結果: {predicted_emotion}")
        # <--- 変更点 2: タプルで(予測, 正解)をリストに追加
        all_predictions.append({'predicted': predicted_emotion, 'true': true_future_emotion, 'start': current_emotion})
    else:
        print(f"    -> 予測失敗")
        
    time.sleep(1) # APIのレート制限対策

# <--- 変更点 3: ループが完全に終わった後で、まとめて結果を計算 ---
print("\n\n=================================================")
print("最終評価結果まとめ")
print("=================================================")

if all_predictions:
    # DataFrameに変換して集計を容易にする
    results_df = pd.DataFrame(all_predictions)
    results_df['is_correct'] = results_df['predicted'] == results_df['true']

    # --- 開始感情ごとの正解率を計算 ---
    print("--- 開始感情ごとの正解率 ---")
    summary_by_start = results_df.groupby('start')['is_correct'].agg(['mean', 'count'])
    summary_by_start.rename(columns={'mean': '正解率', 'count': '件数'}, inplace=True)
    summary_by_start['正解率'] = summary_by_start['正解率'].map('{:.2%}'.format)
    print(summary_by_start)
    
    # --- 全体の正解率を計算 ---
    overall_accuracy = results_df['is_correct'].mean()
    print("\n-------------------------------------------------")
    print(f"総合平均正解率: {overall_accuracy:.2%} ({len(results_df)}件中)")
    print("=================================================")
else:
    print("有効な予測がありませんでした。")