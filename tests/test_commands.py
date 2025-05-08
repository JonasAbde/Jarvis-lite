"""
Tests for kommando-modulet.
"""

import pytest
from datetime import datetime
from src.jarvis_commands import (
    get_time,
    open_youtube,
    open_gmail,
    save_note,
    tell_joke,
    stop_sound,
    COMMANDS
)

def test_get_time():
    """Test at get_time returnerer korrekt format."""
    time_str = get_time()
    assert time_str.startswith("Klokken er ")
    # Verificer at tiden er i korrekt format (HH:MM)
    time_part = time_str.split("er ")[1]
    assert len(time_part) == 5
    assert time_part[2] == ":"

def test_tell_joke():
    """Test at tell_joke returnerer en ikke-tom streng."""
    joke = tell_joke()
    assert isinstance(joke, str)
    assert len(joke) > 0

def test_save_note(tmp_path):
    """Test at save_note gemmer noter korrekt."""
    # Opret midlertidig notes-fil
    notes_file = tmp_path / "noter.txt"
    notes_file.parent.mkdir(exist_ok=True)
    
    # Test at gemme en note
    note_text = "Test note"
    result = save_note(note_text)
    assert result == "Noten er gemt."
    
    # Verificer at noten blev gemt
    assert notes_file.exists()
    content = notes_file.read_text(encoding="utf-8")
    assert note_text in content

def test_commands_mapping():
    """Test at alle kommandoer er korrekt mappet."""
    required_commands = {
        "klokken",
        "youtube",
        "gmail",
        "gem_note",
        "joke",
        "stop_lyd"
    }
    assert all(cmd in COMMANDS for cmd in required_commands)
    assert all(callable(COMMANDS[cmd]) for cmd in COMMANDS) 