CREATE TABLE spotify_tokens (
  user_id       TEXT PRIMARY KEY,
  access_token  TEXT NOT NULL,
  refresh_token TEXT NOT NULL,
  expires_at    BIGINT NOT NULL
);