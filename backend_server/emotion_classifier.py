import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.multioutput import MultiOutputClassifier
import xgboost as xgb
import lightgbm as lgb
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class EmotionClassifier:
    def __init__(self):
        self.data = None
        self.X = None
        self.y = None
        self.scaler = StandardScaler()
        self.models = {}
        self.best_model = None
        self.feature_names = []
        self.emotion_columns = ['Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill']
        
    def load_data(self, file_path: str):
        """Spotify特徴量を含むCSVファイルを読み込み"""
        print("データを読み込み中...")
        self.data = pd.read_csv(file_path)
        print(f"データ形状: {self.data.shape}")
        print(f"列名: {list(self.data.columns)}")
        return self.data
    
    def explore_data(self):
        """データの探索的分析"""
        print("\n=== データ探索 ===")
        
        # 欠損値の確認
        print("欠損値の確認:")
        missing_data = self.data.isnull().sum()
        print(missing_data[missing_data > 0])
        
        # Spotify特徴量の基本統計
        spotify_features = [
            'danceability', 'energy', 'key', 'loudness', 'mode',
            'speechiness', 'acousticness', 'instrumentalness', 'liveness',
            'valence', 'tempo', 'time_signature', 'popularity'
        ]
        
        available_features = [f for f in spotify_features if f in self.data.columns]
        
        if available_features:
            print(f"\nSpotify特徴量の基本統計:")
            print(self.data[available_features].describe())
        
        # 感情カテゴリの分布
        print(f"\n感情カテゴリの分布:")
        for emotion in self.emotion_columns:
            if emotion in self.data.columns:
                print(f"\n{emotion}:")
                print(self.data[emotion].value_counts())
        
        # 感情カテゴリの相関
        emotion_data = self.data[self.emotion_columns].copy()
        emotion_corr = emotion_data.corr()
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(emotion_corr, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5)
        plt.title('感情カテゴリ間の相関')
        plt.tight_layout()
        plt.savefig('emotion_correlation.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def preprocess_data(self):
        """データの前処理"""
        print(f"\n=== データ前処理 ===")
        
        # 欠損値を含む行を削除
        self.data = self.data.dropna()
        print(f"欠損値削除後のデータ形状: {self.data.shape}")
        
        # Spotify特徴量の選択
        spotify_features = [
            'danceability', 'energy', 'key', 'loudness', 'mode',
            'speechiness', 'acousticness', 'instrumentalness', 'liveness',
            'valence', 'tempo', 'time_signature', 'popularity',
            'duration_ms', 'explicit'
        ]
        
        # 利用可能な特徴量のみを選択
        available_features = [f for f in spotify_features if f in self.data.columns]
        
        # 追加の特徴量（ピッチ、ティムブレなど）
        additional_features = [col for col in self.data.columns if col.startswith(('pitch_', 'timbre_', 'num_'))]
        
        self.feature_names = available_features + additional_features
        self.X = self.data[self.feature_names]
        
        # 感情カテゴリを数値化
        self.y = {}
        for emotion in self.emotion_columns:
            if emotion in self.data.columns:
                le = LabelEncoder()
                self.y[emotion] = le.fit_transform(self.data[emotion])
        
        print(f"特徴量の数: {len(self.feature_names)}")
        print(f"感情カテゴリ数: {len(self.y)}")
        print(f"特徴量名: {self.feature_names}")
        
        return self.X, self.y
    
    def train_models(self):
        """複数のモデルを訓練"""
        print(f"\n=== モデル訓練 ===")
        
        # データを訓練・テストに分割
        X_train, X_test, y_train_dict, y_test_dict = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        # 特徴量のスケーリング
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # モデルの定義
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(random_state=42),
            'XGBoost': xgb.XGBClassifier(random_state=42),
            'LightGBM': lgb.LGBMClassifier(random_state=42),
            'SVM': SVC(random_state=42, probability=True)
        }
        
        # 各感情カテゴリごとにモデルを訓練
        results = {}
        
        for emotion in self.emotion_columns:
            if emotion not in self.y:
                continue
                
            print(f"\n{emotion}のモデルを訓練中...")
            
            y_train = y_train_dict[emotion]
            y_test = y_test_dict[emotion]
            
            emotion_results = {}
            
            for name, model in models.items():
                print(f"  {name}を訓練中...")
                
                # クロスバリデーション
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='f1_weighted')
                
                # モデルを訓練
                model.fit(X_train_scaled, y_train)
                
                # テストデータで予測
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                emotion_results[name] = {
                    'model': model,
                    'accuracy': accuracy,
                    'f1_score': f1,
                    'cv_score': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'y_pred': y_pred,
                    'y_test': y_test
                }
                
                print(f"    テスト精度: {accuracy:.4f}, F1スコア: {f1:.4f}")
            
            results[emotion] = emotion_results
        
        self.models = results
        
        # 各感情カテゴリの最良モデルを選択
        self.best_models = {}
        for emotion, emotion_results in results.items():
            best_model_name = max(emotion_results.keys(), 
                                key=lambda k: emotion_results[k]['f1_score'])
            self.best_models[emotion] = emotion_results[best_model_name]['model']
            print(f"\n{emotion}の最良モデル: {best_model_name}")
        
        return results
    
    def evaluate_models(self, results):
        """モデルの詳細評価"""
        print(f"\n=== モデル評価 ===")
        
        # 各感情カテゴリの性能比較
        emotions = list(results.keys())
        model_names = list(results[emotions[0]].keys())
        
        # F1スコアの比較
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.ravel()
        
        for i, emotion in enumerate(emotions):
            f1_scores = [results[emotion][name]['f1_score'] for name in model_names]
            
            bars = axes[i].bar(model_names, f1_scores, color=['skyblue', 'lightgreen', 'lightcoral', 'gold', 'orange'])
            axes[i].set_title(f'{emotion} - F1スコア比較')
            axes[i].set_ylabel('F1スコア')
            axes[i].set_ylim(0, 1)
            
            for bar, score in zip(bars, f1_scores):
                axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                           f'{score:.3f}', ha='center', va='bottom')
            
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('emotion_model_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # 各感情カテゴリの詳細評価
        for emotion, emotion_results in results.items():
            best_model_name = max(emotion_results.keys(), 
                                key=lambda k: emotion_results[k]['f1_score'])
            best_result = emotion_results[best_model_name]
            
            print(f"\n{emotion} - {best_model_name}の詳細評価:")
            print(classification_report(
                best_result['y_test'], 
                best_result['y_pred']
            ))
            
            # 混同行列
            cm = confusion_matrix(best_result['y_test'], best_result['y_pred'])
            plt.figure(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
            plt.title(f'{emotion} - {best_model_name} 混同行列')
            plt.xlabel('予測')
            plt.ylabel('実際')
            plt.tight_layout()
            plt.savefig(f'confusion_matrix_{emotion}.png', dpi=300, bbox_inches='tight')
            plt.show()
    
    def feature_importance_analysis(self):
        """特徴量重要度の分析"""
        print(f"\n=== 特徴量重要度分析 ===")
        
        for emotion, model in self.best_models.items():
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                indices = np.argsort(importances)[::-1]
                
                plt.figure(figsize=(12, 8))
                plt.title(f'{emotion} - 特徴量重要度（上位20件）')
                plt.bar(range(20), importances[indices[:20]])
                plt.xticks(range(20), [self.feature_names[i] for i in indices[:20]], rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(f'feature_importance_{emotion}.png', dpi=300, bbox_inches='tight')
                plt.show()
                
                print(f"\n{emotion} - 特徴量重要度（上位10件）:")
                for i in indices[:10]:
                    print(f"  {self.feature_names[i]}: {importances[i]:.4f}")
    
    def predict_emotions(self, spotify_features: dict):
        """新しい曲の感情を予測"""
        if not self.best_models:
            print("モデルが訓練されていません。")
            return
        
        # 特徴量ベクトルの作成
        feature_vector = []
        for feature in self.feature_names:
            if feature in spotify_features:
                feature_vector.append(spotify_features[feature])
            else:
                feature_vector.append(0)  # デフォルト値
        
        feature_vector = np.array(feature_vector).reshape(1, -1)
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # 各感情カテゴリを予測
        predictions = {}
        probabilities = {}
        
        for emotion, model in self.best_models.items():
            prediction = model.predict(feature_vector_scaled)[0]
            probability = model.predict_proba(feature_vector_scaled)[0]
            
            predictions[emotion] = prediction
            probabilities[emotion] = probability
        
        return predictions, probabilities
    
    def create_ensemble_model(self):
        """アンサンブルモデルの作成"""
        print("アンサンブルモデルを作成中...")
        
        # 各感情カテゴリごとにアンサンブルモデルを作成
        ensemble_models = {}
        
        for emotion in self.emotion_columns:
            if emotion not in self.models:
                continue
            
            # 上位3つのモデルを選択
            emotion_results = self.models[emotion]
            top_models = sorted(emotion_results.items(), 
                              key=lambda x: x[1]['f1_score'], reverse=True)[:3]
            
            estimators = [(name, result['model']) for name, result in top_models]
            
            ensemble = VotingClassifier(
                estimators=estimators,
                voting='soft'
            )
            
            # アンサンブルモデルの訓練
            X_train, X_test, y_train_dict, y_test_dict = train_test_split(
                self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
            )
            
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            y_train = y_train_dict[emotion]
            y_test = y_test_dict[emotion]
            
            ensemble.fit(X_train_scaled, y_train)
            y_pred = ensemble.predict(X_test_scaled)
            
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            ensemble_models[emotion] = {
                'model': ensemble,
                'accuracy': accuracy,
                'f1_score': f1
            }
            
            print(f"{emotion} - アンサンブルモデル: 精度={accuracy:.4f}, F1スコア={f1:.4f}")
        
        return ensemble_models

def main():
    """メイン実行関数"""
    # 感情分類器の初期化
    classifier = EmotionClassifier()
    
    # データの読み込み（Spotify特徴量を含むCSVファイル）
    data = classifier.load_data('melosync_music_data_with_spotify_features.csv')
    
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
    
    # アンサンブルモデルの作成
    ensemble_models = classifier.create_ensemble_model()
    
    # 新しい曲の感情予測例
    print(f"\n=== 新しい曲の感情予測例 ===")
    sample_features = {
        'danceability': 0.8,
        'energy': 0.9,
        'valence': 0.7,
        'tempo': 120,
        'loudness': -5.0,
        'acousticness': 0.1,
        'instrumentalness': 0.0,
        'liveness': 0.3,
        'speechiness': 0.1,
        'mode': 1,
        'key': 5,
        'time_signature': 4,
        'popularity': 80,
        'duration_ms': 180000,
        'explicit': 0
    }
    
    predictions, probabilities = classifier.predict_emotions(sample_features)
    
    print("予測結果:")
    for emotion, prediction in predictions.items():
        prob = max(probabilities[emotion])
        print(f"{emotion}: {prediction} (確信度: {prob:.4f})")

if __name__ == "__main__":
    main() 