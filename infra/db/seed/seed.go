package main

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "os"
    "path/filepath"

    _ "github.com/lib/pq" // PostgreSQL driver
)

// SpotifyToken は seeds.json の要素に対応します
// JSON が配列であることを考慮して構造体スライスを使用します
type SpotifyToken struct {
    AccessToken  string `json:"access_token"`
    TokenType    string `json:"token_type"`
    ExpiresIn    int    `json:"expires_in"`
    RefreshToken string `json:"refresh_token"`
    Scope        string `json:"scope"`
    ExpiresAt    int64 `json:"expires_at"` // RFC3339 形式のタイムスタンプ
}

func main() {
    log.Println("Starting Spotify token seeding...")

    // 環境変数取得
    dbHost := getEnv("DB_HOST", "localhost")
    dbPort := getEnv("DB_PORT", "5433")
    dbUser := getEnv("DB_USER", "user")
    dbPass := getEnv("DB_PASSWORD", "password")
    dbName := getEnv("DB_NAME", "devdb")

    // DB 接続
    dsn := fmt.Sprintf(
        "host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
        dbHost, dbPort, dbUser, dbPass, dbName,
    )
    db, err := sql.Open("postgres", dsn)
    if err != nil {
        log.Fatalf("Error connecting to DB: %v", err)
    }
    defer db.Close()
    if err := db.Ping(); err != nil {
        log.Fatalf("Error pinging DB: %v", err)
    }
    log.Println("Successfully connected to database.")

    // シードファイルのパス (CWD が infra/db/seed)
    seedFile := "seed.json"

    // JSON 読み込み
    tokens, err := loadSeedData(seedFile)
    if err != nil {
        log.Fatalf("Failed to load seed data: %v", err)
    }
    if len(tokens) == 0 {
        log.Fatalf("No seed data found in %s", seedFile)
    }
    token := tokens[0]
    log.Printf("Loaded Spotify token (expires_in=%d, scope=%q, expires_at=%s)", token.ExpiresIn, token.Scope, token.ExpiresAt)

    // データ挿入
    insert := `
        INSERT INTO spotify_tokens
            (access_token, token_type, expires_in, refresh_token, scope, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6)
    `
    if _, err := db.Exec(insert,
        token.AccessToken,
        token.TokenType,
        token.ExpiresIn,
        token.RefreshToken,
        token.Scope,
        token.ExpiresAt,
    ); err != nil {
        log.Fatalf("Error inserting Spotify token: %v", err)
    }
    log.Println("Seed completed: Spotify token inserted.")
}

// getEnv は環境変数を取得し、なければデフォルト値を返します
func getEnv(key, fallback string) string {
    if v, ok := os.LookupEnv(key); ok {
        return v
    }
    log.Printf("Environment variable %s not set, using default %q", key, fallback)
    return fallback
}

// loadSeedData は指定ファイルから JSON 配列を読み込み SpotifyToken のスライスにアンマーシャルします
func loadSeedData(filePath string) ([]SpotifyToken, error) {
    abs, err := filepath.Abs(filePath)
    if err != nil {
        log.Printf("Warning: could not get absolute path for %s: %v", filePath, err)
    }
    log.Printf("Loading seed file: %s (abs: %s)", filePath, abs)

    data, err := os.ReadFile(filePath)
    if err != nil {
        cwd, _ := os.Getwd()
        return nil, fmt.Errorf("could not read %s (cwd=%s): %w", filePath, cwd, err)
    }

    var tokens []SpotifyToken
    if err := json.Unmarshal(data, &tokens); err != nil {
        return nil, fmt.Errorf("JSON unmarshal error for %s: %w", filePath, err)
    }
    return tokens, nil
}
