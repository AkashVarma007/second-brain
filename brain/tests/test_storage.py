from app import storage


def test_save_note_returns_row_with_id(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)

    saved = storage.save_note(db, "buy milk")

    assert saved.id == 1
    assert saved.text == "buy milk"
    assert saved.created_at != ""


def test_list_notes_returns_newest_first(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)
    storage.save_note(db, "first")
    storage.save_note(db, "second")

    notes = storage.list_notes(db)

    assert [note.text for note in notes] == ["second", "first"]


def test_save_task_persists_priority(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)

    saved = storage.save_task(db, "Call the dentist", "high")
    tasks = storage.list_tasks(db)

    assert saved.id == 1
    assert tasks[0].title == "Call the dentist"
    assert tasks[0].priority == "high"


def test_lists_are_empty_on_fresh_db(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)

    assert storage.list_notes(db) == []
    assert storage.list_tasks(db) == []


def test_init_db_is_idempotent(tmp_path):
    db = tmp_path / "test.sqlite3"
    storage.init_db(db)
    storage.save_note(db, "kept")
    storage.init_db(db)

    assert [note.text for note in storage.list_notes(db)] == ["kept"]
