import pandas as pd
import matplotlib.pyplot as plt

# CSVファイルの読み込み
df = pd.read_csv('data/processed_music_data.csv')

# modeとvalenceの相関係数を計算
correlation = df['mode'].corr(df['valence'])
print('modeとvalenceの相関係数:', correlation)

# modeとvalenceの散布図を作成
plt.scatter(df['mode'], df['valence'])
plt.xlabel('mode')
plt.ylabel('valence')
plt.title('Scatter plot of mode vs valence')
plt.grid(True)
plt.show()
