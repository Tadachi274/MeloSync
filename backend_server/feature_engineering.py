# -*- coding: utf-8 -*-
import pandas as pd
from sklearn.preprocessing import StandardScaler

# 数値特徴量を標準化（平均0、分散1に変換）する関数
def standardize_features(df, feature_cols):
    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    return df, scaler

# カテゴリカル特徴量（例：キー、モード）をワンホットエンコーディングする関数
def one_hot_encode(df, cols):
    return pd.get_dummies(df, columns=cols, drop_first=False)