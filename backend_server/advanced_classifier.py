import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import xgboost as xgb
import lightgbm as lgb
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class AdvancedMusicClassifier:
    def __init__(self):
        self.data = None
        self.X = None
        self.y = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.models = {}
        self.best_model = None
        self.feature_names = []
        
    def load_data(self, file_path):
        """CSVファイルからデータを読み込み"""
        print("データを読み込み中...")
        self.data = pd.read_csv(file_path)
        print(f"データ形状: {self.data.shape}")
        return self.data
    
    def advanced_feature_engineering(self):
        """高度な特徴量エンジニアリング"""
        print("高度な特徴量エンジニアリングを実行中...")
        
        # 基本的前処理
        self.data = self.data.dropna()
        
        # 1. アーティスト関連の特徴量
        le_artist = LabelEncoder()
        self.data['artist_encoded'] = le_artist.fit_transform(self.data['アーティスト'])
        self.label_encoders['artist'] = le_artist
        
        # アーティストごとの曲数
        artist_counts = self.data['アーティスト'].value_counts()
        self.data['artist_song_count'] = self.data['アーティスト'].map(artist_counts)
        
        # 2. 感情カテゴリの高度な特徴量
        emotion_cols = ['Happy/Excited', 'Angry/Frustrated', 'Tired/Sad', 'Relax/Chill']
        
        # 感情カテゴリを数値化
        for col in emotion_cols:
            le_emotion = LabelEncoder()
            self.data[f'{col}_encoded'] = le_emotion.fit_transform(self.data[col])
            self.label_encoders[col] = le_emotion
        
        # 感情の多様性（異なる感情カテゴリの数）
        self.data['emotion_diversity'] = self.data[emotion_cols].nunique(axis=1)
        
        # 主要感情（最も頻繁に出現する感情）
        def get_primary_emotion(row):
            emotions = [row[col] for col in emotion_cols]
            return max(set(emotions), key=emotions.count)
        
        self.data['primary_emotion'] = self.data.apply(get_primary_emotion, axis=1)
        le_primary = LabelEncoder()
        self.data['primary_emotion_encoded'] = le_primary.fit_transform(self.data['primary_emotion'])
        self.label_encoders['primary_emotion'] = le_primary
        
        # 3. テキスト関連の特徴量
        # 曲名の特徴
        self.data['song_name_length'] = self.data['曲名（optional）'].str.len()
        self.data['song_name_word_count'] = self.data['曲名（optional）'].str.count(' ') + 1
        
        # 曲名に含まれる特殊文字の数
        self.data['song_name_special_chars'] = self.data['曲名（optional）'].str.count(r'[^\w\s]')
        
        # 4. URL関連の特徴量
        self.data['url_length'] = self.data['URL'].str.len()
        self.data['url_has_parameters'] = self.data['URL'].str.contains('\?').astype(int)
        
        # 5. ジャンル関連の特徴量
        # ジャンルの出現頻度
        genre_counts = self.data['ジャンル'].value_counts()
        self.data['genre_frequency'] = self.data['ジャンル'].map(genre_counts)
        
        # 6. アーティストとジャンルの組み合わせ特徴量
        self.data['artist_genre_combination'] = self.data['アーティスト'] + '_' + self.data['ジャンル']
        le_combination = LabelEncoder()
        self.data['artist_genre_encoded'] = le_combination.fit_transform(self.data['artist_genre_combination'])
        self.label_encoders['artist_genre'] = le_combination
        
        # 7. 感情の組み合わせパターン
        emotion_pattern = self.data[emotion_cols].apply(lambda x: '_'.join(x), axis=1)
        le_pattern = LabelEncoder()
        self.data['emotion_pattern_encoded'] = le_pattern.fit_transform(emotion_pattern)
        self.label_encoders['emotion_pattern'] = le_pattern
        
        # 特徴量の選択
        self.feature_names = [
            'artist_encoded',
            'artist_song_count',
            'song_name_length',
            'song_name_word_count',
            'song_name_special_chars',
            'url_length',
            'url_has_parameters',
            'genre_frequency',
            'artist_genre_encoded',
            'emotion_diversity',
            'primary_emotion_encoded',
            'emotion_pattern_encoded',
            'Happy/Excited_encoded',
            'Angry/Frustrated_encoded',
            'Tired/Sad_encoded',
            'Relax/Chill_encoded'
        ]
        
        self.X = self.data[self.feature_names]
        
        # ターゲット変数の準備
        le_target = LabelEncoder()
        self.y = le_target.fit_transform(self.data['ジャンル'])
        self.label_encoders['target'] = le_target
        
        print(f"特徴量の数: {len(self.feature_names)}")
        print(f"クラス数: {len(np.unique(self.y))}")
        
        return self.X, self.y
    
    def train_advanced_models(self, use_pca=False):
        """高度なモデルの訓練"""
        print("高度なモデルを訓練中...")
        
        # データ分割
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        # スケーリング
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # モデルの定義
        models = {
            'Random Forest': RandomForestClassifier(
                n_estimators=200, 
                max_depth=10, 
                min_samples_split=5,
                random_state=42
            ),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'XGBoost': xgb.XGBClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'LightGBM': lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'SVM': SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                random_state=42,
                probability=True
            )
        }
        
        # ハイパーパラメータチューニング
        param_grids = {
            'Random Forest': {
                'n_estimators': [100, 200, 300],
                'max_depth': [5, 10, 15],
                'min_samples_split': [2, 5, 10]
            },
            'Gradient Boosting': {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1, 0.2],
                'max_depth': [4, 6, 8]
            },
            'XGBoost': {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1, 0.2],
                'max_depth': [4, 6, 8]
            }
        }
        
        results = {}
        for name, model in models.items():
            print(f"\n{name}を訓練中...")
            
            if name in param_grids:
                # グリッドサーチ
                grid_search = GridSearchCV(
                    model, 
                    param_grids[name], 
                    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
                    scoring='f1_weighted',
                    n_jobs=-1
                )
                grid_search.fit(X_train_scaled, y_train)
                best_model = grid_search.best_estimator_
                print(f"最良パラメータ: {grid_search.best_params_}")
            else:
                best_model = model.fit(X_train_scaled, y_train)
            
            # 評価
            y_pred = best_model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # クロスバリデーション
            cv_scores = cross_val_score(
                best_model, X_train_scaled, y_train, 
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
                scoring='f1_weighted'
            )
            
            results[name] = {
                'model': best_model,
                'accuracy': accuracy,
                'f1_score': f1,
                'cv_score': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'y_pred': y_pred,
                'y_test': y_test
            }
            
            print(f"テスト精度: {accuracy:.4f}")
            print(f"F1スコア: {f1:.4f}")
            print(f"CV F1スコア: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        self.models = results
        
        # 最良モデルの選択
        best_model_name = max(results.keys(), key=lambda k: results[k]['f1_score'])
        self.best_model = results[best_model_name]['model']
        
        print(f"\n最良のモデル: {best_model_name}")
        print(f"F1スコア: {results[best_model_name]['f1_score']:.4f}")
        
        return results
    
    def create_ensemble_model(self, results):
        """アンサンブルモデルの作成"""
        print("アンサンブルモデルを作成中...")
        
        # 上位3つのモデルを選択
        top_models = sorted(results.items(), key=lambda x: x[1]['f1_score'], reverse=True)[:3]
        
        estimators = [(name, result['model']) for name, result in top_models]
        
        ensemble = VotingClassifier(
            estimators=estimators,
            voting='soft'
        )
        
        # アンサンブルモデルの訓練
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        ensemble.fit(X_train_scaled, y_train)
        y_pred = ensemble.predict(X_test_scaled)
        
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        print(f"アンサンブルモデルの精度: {accuracy:.4f}")
        print(f"アンサンブルモデルのF1スコア: {f1:.4f}")
        
        return ensemble, accuracy, f1
    
    def detailed_evaluation(self, results):
        """詳細な評価"""
        print("詳細な評価を実行中...")
        
        # モデル比較
        model_names = list(results.keys())
        f1_scores = [results[name]['f1_score'] for name in model_names]
        accuracies = [results[name]['accuracy'] for name in model_names]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # F1スコア比較
        bars1 = ax1.bar(model_names, f1_scores, color=['skyblue', 'lightgreen', 'lightcoral', 'gold', 'orange'])
        ax1.set_title('F1スコア比較')
        ax1.set_ylabel('F1スコア')
        ax1.set_ylim(0, 1)
        for bar, score in zip(bars1, f1_scores):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{score:.3f}', ha='center', va='bottom')
        
        # 精度比較
        bars2 = ax2.bar(model_names, accuracies, color=['skyblue', 'lightgreen', 'lightcoral', 'gold', 'orange'])
        ax2.set_title('精度比較')
        ax2.set_ylabel('精度')
        ax2.set_ylim(0, 1)
        for bar, acc in zip(bars2, accuracies):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{acc:.3f}', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('advanced_model_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # 最良モデルの詳細評価
        best_model_name = max(results.keys(), key=lambda k: results[k]['f1_score'])
        best_result = results[best_model_name]
        
        print(f"\n{best_model_name}の詳細評価:")
        print(classification_report(
            best_result['y_test'], 
            best_result['y_pred'],
            target_names=self.label_encoders['target'].classes_
        ))
        
        # 混同行列
        cm = confusion_matrix(best_result['y_test'], best_result['y_pred'])
        plt.figure(figsize=(12, 10))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=self.label_encoders['target'].classes_,
                   yticklabels=self.label_encoders['target'].classes_)
        plt.title(f'{best_model_name} - 混同行列')
        plt.xlabel('予測')
        plt.ylabel('実際')
        plt.tight_layout()
        plt.savefig('advanced_confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def feature_importance_analysis(self):
        """特徴量重要度の詳細分析"""
        print("特徴量重要度を分析中...")
        
        if hasattr(self.best_model, 'feature_importances_'):
            importances = self.best_model.feature_importances_
            indices = np.argsort(importances)[::-1]
            
            plt.figure(figsize=(12, 8))
            plt.title('特徴量重要度（降順）')
            plt.bar(range(len(importances)), importances[indices])
            plt.xticks(range(len(importances)), [self.feature_names[i] for i in indices], rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig('advanced_feature_importance.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            print("特徴量重要度（上位10件）:")
            for i in indices[:10]:
                print(f"{self.feature_names[i]}: {importances[i]:.4f}")
        
        # 特徴量間の相関分析
        plt.figure(figsize=(15, 12))
        correlation_matrix = self.X.corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5)
        plt.title('特徴量間の相関行列')
        plt.tight_layout()
        plt.savefig('feature_correlation.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    """メイン実行関数"""
    # 高度な分類器の初期化
    classifier = AdvancedMusicClassifier()
    
    # データの読み込み
    data = classifier.load_data('melosync_music_data.csv')
    
    # 高度な特徴量エンジニアリング
    X, y = classifier.advanced_feature_engineering()
    
    # 高度なモデルの訓練
    results = classifier.train_advanced_models()
    
    # アンサンブルモデルの作成
    ensemble, ensemble_acc, ensemble_f1 = classifier.create_ensemble_model(results)
    
    # 詳細な評価
    classifier.detailed_evaluation(results)
    
    # 特徴量重要度の分析
    classifier.feature_importance_analysis()
    
    print(f"\n=== 最終結果 ===")
    print(f"アンサンブルモデルの精度: {ensemble_acc:.4f}")
    print(f"アンサンブルモデルのF1スコア: {ensemble_f1:.4f}")

if __name__ == "__main__":
    main() 