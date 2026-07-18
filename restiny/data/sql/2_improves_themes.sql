UPDATE settings
  SET theme='dark';

ALTER TABLE settings
  ADD COLUMN accent_color TEXT NOT NULL DEFAULT '#99c1f1';
