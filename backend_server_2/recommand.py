# -*- coding: utf-8 -*-
import numpy as np

def recommend_songs_for_target(model, X, track_ids, target_mood_code, top_k=10):
    """
    訓練済みの専用モデルを使用し、目標感情に合わせた楽曲を推薦する関数。

    引数:
        model: 特定の開始感情に合わせて訓練されたKerasモデル。
        X (pd.DataFrame): 入力特徴量。
        track_ids (list): 楽曲IDのリスト。
        target_mood_code (int): 目標感情のコード。
        top_k (int): 推薦する曲数。

    戻り値:
        list: 推薦された(track_id, 確率)のリスト。
    """
    # 1. モデルを使い、全楽曲が各目標感情へ遷移する確率を予測する
    # 出力 shape: (サンプル数, 4)
    predictions = model.predict(X)
    
    # 2. 全楽曲の中から、指定された「目標感情」への遷移確率のみを抽出する
    target_probs = predictions[:, target_mood_code]
    
    # 3. 目標確率に基づいて降順にソートする
    sorted_indices = np.argsort(-target_probs)
    
    # 4. Top-Kの推薦結果を整形して返す
    recommended = [(track_ids[i], target_probs[i]) for i in sorted_indices[:top_k]]
    return recommended