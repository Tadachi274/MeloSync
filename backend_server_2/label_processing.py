# -*- coding: utf-8 -*-
import pandas as pd

# 感情遷移のログデータから、曲ごとの4x4の遷移確率行列を作成する関数
def build_transition_matrix(df, mood_map):
    # 'start_mood' と 'end_mood' の文字列を数値（0-3）に変換
    df['start_mood_encoded'] = df['start_mood'].map(mood_map)
    df['end_mood_encoded'] = df['end_mood'].map(mood_map)
    
    # 曲ごと、開始感情ごと、終了感情ごとに遷移回数を集計
    mood_transitions_counts = df.groupby(['track_id', 'start_mood_encoded', 'end_mood_encoded']).size().unstack(fill_value=0)
    
    # 行（各開始感情）ごとに確率を計算（合計が1になるように正規化）するヘルパー関数
    def normalize_row(row):
        total = row.sum()
        return row / total if total > 0 else row
        
    final_labels_data = []
    # ユニークな各トラックIDに対してループ
    for track_id in df['track_id'].unique():
        song_labels = {'track_id': track_id}
        # 4つの開始感情（0, 1, 2, 3）に対してループ
        for start_mood_code in mood_map.values():
            try:
                # 現在の曲と開始感情に対応する遷移回数を取得
                current_transitions = mood_transitions_counts.loc[(track_id, start_mood_code)]
            except KeyError:
                # 遷移ログが存在しない場合は、全ての遷移回数を0とする
                current_transitions = pd.Series([0]*len(mood_map), index=list(mood_map.values()))
            
            # 全ての終了感情（4つ）を列に持つSeriesを準備
            full_transitions = pd.Series([0]*len(mood_map), index=list(mood_map.values()))
            full_transitions.update(current_transitions)
            
            # 遷移回数を確率に正規化
            normalized_transitions = normalize_row(full_transitions)
            
            # 4x4=16個の確率値を辞書に格納
            for end_mood_code in mood_map.values():
                col_name = f'start_{start_mood_code}_end_{end_mood_code}'
                song_labels[col_name] = normalized_transitions.get(end_mood_code, 0.0)
                
        final_labels_data.append(song_labels)
        
    # 結果をDataFrameに変換して返す
    final_labels_df = pd.DataFrame(final_labels_data)
    return final_labels_df