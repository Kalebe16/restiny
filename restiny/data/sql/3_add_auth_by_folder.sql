ALTER TABLE folders
  ADD COLUMN auth_mode TEXT NOT NULL DEFAULT 'basic';

ALTER TABLE folders
  ADD COLUMN auth JSON NOT NULL DEFAULT '{"username":"","password":""}';

ALTER TABLE folders
  ADD COLUMN headers JSON NOT NULL DEFAULT '[]';

ALTER TABLE folders
  ADD COLUMN documentation TEXT NOT NULL DEFAULT '';

-- requests.folder_id required
INSERT INTO folders (uuid, name, auth_mode, auth, headers, documentation)
SELECT lower(hex(randomblob(16))), 'draft', 'basic', '{"username":"","password":""}', '[]', ''
WHERE NOT EXISTS (SELECT 1 FROM folders WHERE name = 'draft');

WITH draft AS (
  SELECT id FROM folders WHERE name = 'draft' LIMIT 1
)
UPDATE requests
SET folder_id = (SELECT id FROM draft)
WHERE folder_id IS NULL;

CREATE TABLE requests_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid TEXT NOT NULL UNIQUE,
  folder_id INTEGER NOT NULL
    REFERENCES folders(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'GET',
  url TEXT NOT NULL DEFAULT '',
  headers JSON NOT NULL DEFAULT '[]',
  params JSON NOT NULL DEFAULT '[]',
  body_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  body_mode TEXT NOT NULL DEFAULT 'raw',
  body JSON NOT NULL DEFAULT '{"language":"plaintext","value":""}',
  auth_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  auth_mode TEXT NOT NULL DEFAULT 'inherited',
  auth JSON NULL,
  option_timeout FLOAT NULL DEFAULT 5.5,
  option_follow_redirects BOOLEAN NOT NULL DEFAULT TRUE,
  option_verify_ssl BOOLEAN NOT NULL DEFAULT TRUE,
  option_attach_cookies BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
  updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL
);

INSERT INTO requests_new
SELECT * FROM requests;

DROP TABLE requests;

ALTER TABLE requests_new RENAME TO requests;
