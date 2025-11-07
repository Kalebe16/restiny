CREATE TABLE folders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  parent_id INTEGER NULL
    REFERENCES folders(id) ON DELETE CASCADE,
  name TEXT NOT NULL,

  created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
  updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL
);

-- equivalent to UNIQUE (parent_id, name)
CREATE UNIQUE INDEX uq_folders_parent_id_name
  ON folders (IFNULL(parent_id, -1), name);

CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  folder_id INTEGER NOT NULL
    REFERENCES folders(id) ON DELETE CASCADE,
  name TEXT NOT NULL,

  method TEXT NOT NULL,
  url TEXT NULL,
  headers JSON NOT NULL DEFAULT '[]',
  params JSON NOT NULL DEFAULT '[]',

  body_enabled BOOLEAN NOT NULL,
  body_mode TEXT NOT NULL,
  body JSON NULL,

  auth_enabled BOOLEAN NOT NULL,
  auth_mode TEXT NOT NULL,
  auth JSON NULL,

  option_timeout FLOAT NULL,
  option_follow_redirects BOOLEAN NOT NULL,
  option_verify_ssl BOOLEAN NOT NULL,

  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

-- equivalent to UNIQUE (folder_id, name)
CREATE UNIQUE INDEX uq_requests_folder_id_name
  ON requests (IFNULL(folder_id, -1), name);
