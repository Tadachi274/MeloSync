# -*- coding: utf-8 -*-
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout
from tensorflow.keras.optimizers import Adam

# Kerasを使って多出力のニューラルネットワークモデルを構築する関数
def build_model(input_dim, num_start_moods=4, num_end_moods=4):
    # 入力層を定義（次元数は特徴量の数）
    inputs = Input(shape=(input_dim,), name='main_input')
    
    # 隠れ層（中間層）を定義。Dropoutで過学習を防ぐ
    x = Dense(128, activation='relu')(inputs)
    x = Dropout(0.3)(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.3)(x)
    
    # 出力層を定義
    outputs = []
    # 開始感情の数（4つ）だけループし、それぞれに独立した出力層を作成
    for i in range(num_start_moods):
        # 各出力層は、終了感情の数（4つ）のユニットを持ち、softmaxで確率を出力
        output_layer = Dense(num_end_moods, activation='softmax', name=f'start_mood_{i}_output')(x)
        outputs.append(output_layer)
        
    # 入力と複数の出力を結合してモデルを定義
    model = Model(inputs=inputs, outputs=outputs)
    
    # モデルのコンパイル。各出力層に categorical_crossentropy損失関数を指定
    model.compile(optimizer='adam',
                  loss=['categorical_crossentropy'] * num_start_moods,
                  metrics=['accuracy'] * num_start_moods)
                  
    return model