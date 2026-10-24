-- ESPN athlete ids, so nightly ESPN box scores can be matched to NBA.com players.
-- Players ESPN knows but NBA.com hasn't been loaded for yet get a placeholder row with a
-- negative id (minus the ESPN id); the next NBA.com players run folds them into the real row.
ALTER TABLE players ADD COLUMN espn_id text UNIQUE;
