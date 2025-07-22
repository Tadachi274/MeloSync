import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 相関係数をまとめる辞書
valence_corr_dict = {}
arousal_corr_dict = {}
    
name_list = ["chen", "obayashi", "kuroda", "watanabe", "tadachi", "yifan"]
name_list2 = ["Chen", "大林", "黒田", "渡邊", "忠地", "Yifan"]
for name, name2 in zip(name_list, name_list2):
    # --- 1. 全データの読み込みと結合 ---
    dataset_files = {
        'Happy/Excited': 'data/music_data_happy_normalized_encoded.csv',
        'Angry/Frustrated': 'data/music_data_angry_normalized_encoded.csv',
        'Tired/Sad': 'data/music_data_tired_normalized_encoded.csv',
        'Relax/Chill': 'data/music_data_relax_normalized_encoded.csv'
    }

    for emotion, file in dataset_files.items():
        try:
            df = pd.read_csv(file)
            
            # 黒田のデータを抽出
            df = df[df["担当者"] == name2]
            df = df.drop(df.columns[list(range(0, 7)) + [21]], axis=1)
        except FileNotFoundError:
            print(f"エラー: '{file}' が見つかりませんでした。")
            continue
        print(df.head())

        # --- 2. 2軸ラベルの作成 ---
        df['Valence'] = df[emotion].apply(lambda x: 1 if x in ['Happy/Excited', 'Relax/Chill'] else -1)
        df['Arousal'] = df[emotion].apply(lambda x: 1 if x in ['Happy/Excited', 'Angry/Frustrated'] else -1)

        df = df.drop(df.columns[-3], axis=1)
        # 相関行列
        correlation_matrix = df.corr()


        valence_corr = correlation_matrix['Valence'].drop(['Valence', 'Arousal'], errors='ignore')
        arousal_corr = correlation_matrix['Arousal'].drop(['Valence', 'Arousal'], errors='ignore')

        valence_corr_dict[emotion] = valence_corr
        arousal_corr_dict[emotion] = arousal_corr


    print(f"valence_corr_dict: {valence_corr_dict}")
    avg_abs_valence_corr = sum(map(abs, valence_corr_dict.values())) / len(valence_corr_dict)
    print(f"avg_abs_valence_corr: {avg_abs_valence_corr}")

    avg_abs_arousal_corr = sum(map(abs, arousal_corr_dict.values())) / len(arousal_corr_dict)
    print(f"avg_abs_arousal_corr: {avg_abs_arousal_corr}")


    plt.figure(figsize=(14, 6))

    # Valence
    plt.plot(avg_abs_valence_corr.index, avg_abs_valence_corr.values, marker='o', label='Valence')

    # Arousal
    plt.plot(avg_abs_arousal_corr.index, avg_abs_arousal_corr.values, marker='s', label='Arousal')

    # 共通設定
    plt.xticks(rotation=90)
    plt.axhline(0, color='gray', linestyle='--')
    plt.title('Valence & Arousal Correlations (Average) - All Emotions')
    plt.ylabel('Correlation')
    plt.ylim(0, 0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'data/analysis/valence_arousal_correlations_all_emotions_{name}.png', dpi=300)
    plt.show()