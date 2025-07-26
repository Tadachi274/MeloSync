# -*- coding: utf-8 -*-
import numpy as np
# joblib 可能需要在這邊或 main.py 中被用來載入模型

def recommend_songs_for_target(model, X, track_ids, target_mood_code, top_k=10):
    """
    訓練済みの LightGBM モデルを使用し、目標感情に合わせた楽曲を推薦する関数。
    """
    # 1. 【修改點】使用 .predict_proba() 來獲取機率
    # 輸出 shape: (樣本數, 類別數)，這裡會是 (樣本數, 4)
    predictions = model.predict_proba(X)

    # 2. 全楽曲の中から、指定された「目標感情」への遷移確率のみを抽出する (這部分邏輯不變)
    target_probs = predictions[:, target_mood_code]
    
    # 3. 目標確率に基づいて降順にソートする (這部分邏輯不變)
    sorted_indices = np.argsort(-target_probs)
    
    # 4. Top-Kの推薦結果を整形して返す (這部分邏輯不變)
    recommended = [(track_ids[i], target_probs[i]) for i in sorted_indices[:top_k]]
    return recommended
