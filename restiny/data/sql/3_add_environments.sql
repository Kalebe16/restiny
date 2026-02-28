CREATE TABLE environments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  name TEXT NOT NULL UNIQUE,
  variables JSON NOT NULL DEFAULT '[]',

  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

INSERT INTO environments (name, variables, created_at, updated_at)
VALUES ('global', '[]', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

CREATE TRIGGER trg_environments_prevent_global_delete
BEFORE DELETE ON environments
FOR EACH ROW
WHEN OLD.name = 'global'
BEGIN
  SELECT RAISE(ABORT, 'Cannot delete global environment');
END;

CREATE TRIGGER trg_environments_prevent_global_rename
BEFORE UPDATE OF name ON environments
FOR EACH ROW
WHEN OLD.name = 'global'
BEGIN
  SELECT RAISE(ABORT, 'Cannot rename global environment');
END;
