# -*- coding: utf-8 -*-
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout
from tensorflow.keras.optimizers import Adam

def build_classification_model(input_dim, num_classes=4):
    """
    標準的な多クラス分類（4クラス）のニューラルネットワークモデルを構築する関数。
    
    引数:
        input_dim (int): 入力特徴量の次元数。
        num_classes (int): 出力クラスの数（ここでは4つの感情）。
        
    戻り値:
        Keras Model: コンパイル済みの分類モデル。
    """
    # 入力層
    inputs = Input(shape=(input_dim,), name='main_input')
    
    # 隠れ層
    x = Dense(128, activation='relu')(inputs)
    x = Dropout(0.3)(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.3)(x)
    
    # 出力層：単一の出力で、4つのニューロン（クラス数）を持ち、多クラス分類のためにsoftmaxを使用
    outputs = Dense(num_classes, activation='softmax', name='output')(x)
    
    model = Model(inputs=inputs, outputs=outputs)
    
    # モデルのコンパイル
    # ラベル(Y)がone-hotエンコーディングではなく整数（0,1,2,3）であるため、
    # 損失関数には sparse_categorical_crossentropy を使用する。
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
                  
    return model