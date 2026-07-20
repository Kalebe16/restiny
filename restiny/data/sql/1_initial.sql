CREATE TABLE folders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid TEXT NOT NULL UNIQUE,
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
  uuid TEXT NOT NULL UNIQUE,
  folder_id INTEGER NULL
    REFERENCES folders(id) ON DELETE CASCADE,
  name TEXT NOT NULL,

  method TEXT NOT NULL,
  url TEXT NOT NULL,
  headers JSON NOT NULL DEFAULT '[]',
  params JSON NOT NULL DEFAULT '[]',

  body_enabled BOOLEAN NOT NULL,
  body_mode TEXT NOT NULL,
  body JSON NOT NULL,

  auth_enabled BOOLEAN NOT NULL,
  auth_mode TEXT NOT NULL,
  auth JSON NULL,

  option_timeout FLOAT NULL,
  option_follow_redirects BOOLEAN NOT NULL,
  option_verify_ssl BOOLEAN NOT NULL,
  option_attach_cookies BOOLEAN NOT NULL,

  created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
  updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL
);

-- equivalent to UNIQUE (folder_id, name)
CREATE UNIQUE INDEX uq_requests_folder_id_name
  ON requests (IFNULL(folder_id, -1), name);


CREATE TABLE environments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  name TEXT NOT NULL UNIQUE,
  variables JSON NOT NULL DEFAULT '[]',

  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  theme TEXT NOT NULL,

  created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
  updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL
);

INSERT INTO environments (name, variables, created_at, updated_at)
VALUES ('global', '[]', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO requests (
  uuid,
  folder_id,
  name,
  method,
  url,
  headers,
  params,
  body_enabled,
  body_mode,
  body,
  auth_enabled,
  auth_mode,
  auth,
  option_timeout,
  option_follow_redirects,
  option_verify_ssl,
  option_attach_cookies,
  created_at,
  updated_at
) VALUES (
  lower(hex(randomblob(16))),
  NULL,
  'draft',
  'GET',
  '',
  '[]',
  '[]',
  0,
  'raw',
  '{"language":"plaintext","value":""}',
  0,
  'basic',
  '{"username":"","password":""}',
  5.5,
  1,
  1,
  1,
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP
);

