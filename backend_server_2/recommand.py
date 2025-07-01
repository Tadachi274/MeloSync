# -*- coding: utf-8 -*-
import numpy as np

# 学習済みモデルを使って、条件に合う曲を推薦する関数
def recommend_songs(model, X, track_ids, start_mood_code, target_mood_code, top_k=10):
    # モデルで全曲の遷移確率を予測
    predictions = model.predict(X)
    # predictions はリストであり、各要素のshapeは(サンプル数, 4)
    
    # ユーザーの「開始感情」に対応する予測結果を取得
    # predictions[0]は「Angryから」の予測、[1]は「Happyから」の予測...
    mood_probs = predictions[start_mood_code]  # shape=(サンプル数, 4)
    
    # その中で、ユーザーの「目標感情」への遷移確率だけを抜き出す
    target_probs = mood_probs[:, target_mood_code]
    
    # 目標感情への遷移確率が高い順に曲のインデックスをソート
    sorted_indices = np.argsort(-target_probs)
    
    # 上位k件のトラックIDと対応する確率をリストとして返す
    recommended = [(track_ids[i], target_probs[i]) for i in sorted_indices[:top_k]]
    return recommended