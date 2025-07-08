CREATE TABLE spotify_tokens (
    access_token TEXT NOT NULL,
    token_type VARCHAR(50) NOT NULL,
    expires_in INTEGER NOT NULL,
    refresh_token TEXT NOT NULL,
    scope TEXT NOT NULL,
    expires_at BIGINT NOT NULL
);