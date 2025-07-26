# -*- coding: utf-8 -*-
import pandas as pd

def create_target_label_for_start_mood(df, start_mood_code):
    """
    特定の「開始感情」に対して、各曲で最も頻繁に出現する「終了感情」をラベルとして特定する関数。
    
    引数:
        df (pd.DataFrame): 'track_id', 'start_mood_encoded', 'end_mood_encoded' を含むデータ。
        start_mood_code (int): 対象とする開始感情のコード (0-3)。
        
    戻り値:
        pd.DataFrame: 'track_id' と 'target_mood' (最頻出の終了感情) を含むDataFrame。
    """
    # 1. 特定の開始感情のデータのみを抽出する
    df_filtered = df[df['start_mood_encoded'] == start_mood_code].copy()
    
    # 2. この開始感情のデータが存在しない場合、空のDataFrameを返す
    if df_filtered.empty:
        return pd.DataFrame(columns=['track_id', 'target_mood'])

    # 3. 各track_idについて、'end_mood_encoded'列の最頻値を計算する
    # .agg() 内の lambda 式が核心部分。
    # 各グループ（track_idごと）で'end_mood_encoded'列の値の頻度を計算し、最頻値（idxmax）を取得する。
    most_common_end_mood = df_filtered.groupby('track_id')['end_mood_encoded'].agg(lambda x: x.value_counts().idxmax()).reset_index()
    
    # 4. 後続のマージ処理のために列名を変更する
    most_common_end_mood.rename(columns={'end_mood_encoded': 'target_mood'}, inplace=True)
    
    return most_common_end_mood