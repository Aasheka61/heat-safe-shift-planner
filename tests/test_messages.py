from heatplanner.messages import TEXT, hour_allowances, merge_blocks, render_message

DAY = {6: 24.0, 7: 24.0, 8: 29.0, 9: 31.5, 10: 31.5, 11: 31.5}


def test_blocks_merge_consecutive_identical_hours():
    blocks = merge_blocks(hour_allowances(DAY))
    assert blocks[0] == (6, 8, (60, 60, 60))
    assert blocks[-1] == (9, 12, (0, 0, 0))


def test_message_english_contains_windows_and_stop():
    blocks = merge_blocks(hour_allowances(DAY))
    msg = render_message("Site A", "2025-04-20", blocks, "en")
    assert "06:00-08:00" in msg and "STOP all work" in msg and "Normal work" in msg
    assert "{" not in msg


def test_message_tamil_has_no_unfilled_placeholders():
    blocks = merge_blocks(hour_allowances(DAY))
    msg = render_message("Site A", "2025-04-20", blocks, "ta")
    assert "{" not in msg and "}" not in msg
    assert TEXT["ta"]["title"] in msg


def test_buffer_changes_allowances():
    a = hour_allowances({8: 27.5})[8]
    b = hour_allowances({8: 27.5}, buffer=1.5)[8]
    assert b[0] <= a[0]
