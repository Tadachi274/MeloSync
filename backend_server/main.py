import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class MusicClassifier:
    def __init__(self):
        self.data = None
        self.X = None
        self.y = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.models = {}
        self.best_model = None
        
    def load_data(self, file_path):
        """CSVファイルからデータを読み込み"""
        print("データを読み込み中...")
        self.data = pd.read_csv(file_path)
        print(f"データ形状: {self.data.shape}")
        print(f"列名: {list(self.data.columns)}")
        return self.data
    
    def explore_data(self):
        """データの探索的分析"""
        print("\n=== データ探索 ===")
        print(f"欠損値の確認:")
        print(self.data.isnull().sum())
        
        print(f"\n基本統計:")
        print(self.data.describe())
        
        print(f"\nジャンルの分布:")
        print(self.data['ジャンル'].value_counts())
        
        print(f"\nアーティストの分布（上位10件）:")
        print(self.data['アーティスト'].value_counts().head(10))
        
        # 感情カテゴリの分布を可視化
        emotion_cols = ['Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill']
        plt.figure(figsize=(15, 10))
        
        for i, col in enumerate(emotion_cols, 1):
            plt.subplot(2, 2, i)
            self.data[col].value_counts().plot(kind='bar')
            plt.title(f'{col}の分布')
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('emotion_distribution.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def preprocess_data(self, target_column='ジャンル'):
        """データの前処理"""
        print(f"\n=== データ前処理 ===")
        
        # 欠損値を含む行を削除
        self.data = self.data.dropna()
        print(f"欠損値削除後のデータ形状: {self.data.shape}")
        
        # 特徴量エンジニアリング
        # 1. アーティスト名を数値化
        le_artist = LabelEncoder()
        self.data['artist_encoded'] = le_artist.fit_transform(self.data['アーティスト'])
        self.label_encoders['artist'] = le_artist
        
        # 2. 感情カテゴリを数値化
        emotion_cols = ['Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill']
        for col in emotion_cols:
            le_emotion = LabelEncoder()
            self.data[f'{col}_encoded'] = le_emotion.fit_transform(self.data[col])
            self.label_encoders[col] = le_emotion
        
        # 3. 曲名の長さを特徴量として追加
        self.data['song_name_length'] = self.data['曲名（optional）'].str.len()
        
        # 4. URLの長さを特徴量として追加
        self.data['url_length'] = self.data['URL'].str.len()
        
        # 特徴量の選択
        feature_columns = [
            'artist_encoded',
            'song_name_length',
            'url_length',
            'Happy/Excited_encoded',
            'Angry/Frustrated_encoded',
            'Tired/Sad_encoded',
            'Relax/Chill_encoded'
        ]
        
        self.X = self.data[feature_columns]
        
        # ターゲット変数の準備
        le_target = LabelEncoder()
        self.y = le_target.fit_transform(self.data[target_column])
        self.label_encoders['target'] = le_target
        
        print(f"特徴量の数: {len(feature_columns)}")
        print(f"クラス数: {len(np.unique(self.y))}")
        print(f"特徴量名: {feature_columns}")
        
        return self.X, self.y
    
    def train_models(self):
        """複数のモデルを訓練"""
        print(f"\n=== モデル訓練 ===")
        
        # データを訓練・テストに分割
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        # 特徴量のスケーリング
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # モデルの定義
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(random_state=42),
            'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
            'SVM': SVC(random_state=42, probability=True)
        }
        
        # 各モデルを訓練・評価
        results = {}
        for name, model in models.items():
            print(f"\n{name}を訓練中...")
            
            # クロスバリデーション
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            print(f"クロスバリデーションスコア: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            # モデルを訓練
            model.fit(X_train_scaled, y_train)
            
            # テストデータで予測
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'cv_score': cv_scores.mean(),
                'y_pred': y_pred,
                'y_test': y_test
            }
            
            print(f"テスト精度: {accuracy:.4f}")
        
        self.models = results
        
        # 最良のモデルを選択
        best_model_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
        self.best_model = results[best_model_name]['model']
        
        print(f"\n最良のモデル: {best_model_name} (精度: {results[best_model_name]['accuracy']:.4f})")
        
        return results
    
    def evaluate_models(self, results):
        """モデルの詳細評価"""
        print(f"\n=== モデル評価 ===")
        
        # 各モデルの性能比較
        model_names = list(results.keys())
        accuracies = [results[name]['accuracy'] for name in model_names]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(model_names, accuracies, color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
        plt.title('モデル性能比較')
        plt.ylabel('精度')
        plt.ylim(0, 1)
        
        # バーの上に数値を表示
        for bar, acc in zip(bars, accuracies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{acc:.3f}', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # 最良モデルの詳細評価
        best_model_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
        best_result = results[best_model_name]
        
        print(f"\n{best_model_name}の詳細評価:")
        print(classification_report(
            best_result['y_test'], 
            best_result['y_pred'],
            target_names=self.label_encoders['target'].classes_
        ))
        
        # 混同行列の可視化
        cm = confusion_matrix(best_result['y_test'], best_result['y_pred'])
        plt.figure(figsize=(12, 10))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=self.label_encoders['target'].classes_,
                   yticklabels=self.label_encoders['target'].classes_)
        plt.title(f'{best_model_name} - 混同行列')
        plt.xlabel('予測')
        plt.ylabel('実際')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def feature_importance_analysis(self):
        """特徴量重要度の分析"""
        print(f"\n=== 特徴量重要度分析 ===")
        
        if hasattr(self.best_model, 'feature_importances_'):
            feature_names = self.X.columns
            importances = self.best_model.feature_importances_
            
            # 重要度を降順にソート
            indices = np.argsort(importances)[::-1]
            
            plt.figure(figsize=(10, 6))
            plt.title('特徴量重要度')
            plt.bar(range(len(importances)), importances[indices])
            plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45)
            plt.tight_layout()
            plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            print("特徴量重要度（降順）:")
            for i in indices:
                print(f"{feature_names[i]}: {importances[i]:.4f}")
    
    def predict_new_song(self, artist, song_name, url, emotions):
        """新しい曲のジャンルを予測"""
        if self.best_model is None:
            print("モデルが訓練されていません。")
            return
        
        # 新しいデータの前処理
        artist_encoded = self.label_encoders['artist'].transform([artist])[0]
        song_length = len(song_name)
        url_length = len(url)
        
        emotion_encoded = []
        emotion_cols = ['Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill']
        for i, col in enumerate(emotion_cols):
            emotion_encoded.append(self.label_encoders[col].transform([emotions[i]])[0])
        
        # 特徴量ベクトルの作成
        features = np.array([artist_encoded, song_length, url_length] + emotion_encoded).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        
        # 予測
        prediction = self.best_model.predict(features_scaled)[0]
        probability = self.best_model.predict_proba(features_scaled)[0]
        
        predicted_genre = self.label_encoders['target'].inverse_transform([prediction])[0]
        
        print(f"\n予測結果:")
        print(f"予測ジャンル: {predicted_genre}")
        print(f"確信度: {max(probability):.4f}")
        
        # 上位3つの予測を表示
        top_indices = np.argsort(probability)[::-1][:3]
        print(f"\n上位3つの予測:")
        for i, idx in enumerate(top_indices):
            genre = self.label_encoders['target'].classes_[idx]
            prob = probability[idx]
            print(f"{i+1}. {genre}: {prob:.4f}")

def main():
    """メイン実行関数"""
    # 分類器の初期化
    classifier = MusicClassifier()
    
    # データの読み込み
    data = classifier.load_data('melosync_music_data.csv')
    
    # データの探索
    classifier.explore_data()
    
    # データの前処理
    X, y = classifier.preprocess_data()
    
    # モデルの訓練
    results = classifier.train_models()
    
    # モデルの評価
    classifier.evaluate_models(results)
    
    # 特徴量重要度の分析
    classifier.feature_importance_analysis()
    
    # 新しい曲の予測例
    print(f"\n=== 新しい曲の予測例 ===")
    classifier.predict_new_song(
        artist="嵐",
        song_name="Happiness",
        url="https://open.spotify.com/track/example",
        emotions=["Happy/Excited", "Relax/Chill", "Relax/Chill", "Happy/Excited"]
    )

if __name__ == "__main__":
    main()
