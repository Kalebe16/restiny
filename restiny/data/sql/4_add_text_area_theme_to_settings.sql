UPDATE settings SET theme='textual-dark' WHERE theme IN ('dark', 'dracula', 'forest');

ALTER TABLE settings
ADD COLUMN editor_theme TEXT NOT NULL DEFAULT 'vscode_dark';
