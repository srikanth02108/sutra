"""
Excel Action Library — Sutra
==============================
Every Excel operation coded as deterministic step sequences.
The LLM looks up this library by action ID — it never needs to
invent key sequences.

Each action is a function returning a list of step dicts.
Steps use these action types (handled by actuator.py):
  {"action": "hotkey",    "keys": ["ctrl", "b"]}   — simultaneous
  {"action": "ribbon",    "keys": ["h", "f", "s"]} — sequential after Alt
  {"action": "press_key", "key": "enter"}           — single key
  {"action": "type_text", "text": "Arial"}          — type string
  {"action": "wait",      "seconds": 0.3}           — pause

Usage:
  from excel_actions import REGISTRY, get_steps
  steps = get_steps("bold")
  steps = get_steps("set_font_size", size=14)
  steps = get_steps("set_column_width", width=25)

All action IDs are in REGISTRY dict.
"""

from __future__ import annotations
from typing import Any

# ─── helpers ─────────────────────────────────────────────────────────────────
def _wait(s: float = 0.3) -> dict:
    return {"action": "wait", "seconds": s}

def _hotkey(*keys: str) -> dict:
    return {"action": "hotkey", "keys": list(keys)}

def _ribbon(*keys: str) -> dict:
    """Sequential ribbon key presses after a tab opener."""
    return {"action": "ribbon", "keys": list(keys)}

def _key(k: str) -> dict:
    return {"action": "press_key", "key": k}

def _type(text: str) -> dict:
    return {"action": "type_text", "text": str(text)}

def _home_tab() -> list:
    """Open Home tab and wait."""
    return [_hotkey("alt", "h"), _wait(0.3)]

def _insert_tab() -> list:
    return [_hotkey("alt", "n"), _wait(0.3)]

def _page_layout_tab() -> list:
    return [_hotkey("alt", "p"), _wait(0.3)]

def _formulas_tab() -> list:
    return [_hotkey("alt", "m"), _wait(0.3)]

def _data_tab() -> list:
    return [_hotkey("alt", "a"), _wait(0.3)]

def _review_tab() -> list:
    return [_hotkey("alt", "r"), _wait(0.3)]

def _view_tab() -> list:
    return [_hotkey("alt", "w"), _wait(0.3)]


# ════════════════════════════════════════════════════════════════════════
# ACTION LIBRARY
# Each function returns List[dict] — exact steps to execute
# ════════════════════════════════════════════════════════════════════════

# ── BASIC FORMATTING ─────────────────────────────────────────────────────────

def bold(**kw) -> list:
    """Toggle bold on selected cell(s)."""
    return [_hotkey("ctrl", "b")]

def italic(**kw) -> list:
    """Toggle italic on selected cell(s)."""
    return [_hotkey("ctrl", "i")]

def underline(**kw) -> list:
    """Toggle underline on selected cell(s)."""
    return [_hotkey("ctrl", "u")]

def strikethrough(**kw) -> list:
    """Toggle strikethrough."""
    return [_hotkey("ctrl", "5")]

def bold_italic(**kw) -> list:
    return [_hotkey("ctrl", "b"), _wait(0.1), _hotkey("ctrl", "i")]

def bold_underline(**kw) -> list:
    return [_hotkey("ctrl", "b"), _wait(0.1), _hotkey("ctrl", "u")]

def clear_formatting(**kw) -> list:
    """Remove all formatting from selected cell(s)."""
    return [*_home_tab(), _ribbon("e", "f")]

def clear_contents(**kw) -> list:
    """Delete cell contents (not formatting). requires_confirmation=True."""
    return [_key("delete")]

def clear_all(**kw) -> list:
    """Clear contents AND formatting. requires_confirmation=True."""
    return [*_home_tab(), _ribbon("e", "a")]


# ── FONT ─────────────────────────────────────────────────────────────────────

def set_font_size(size: int = 12, **kw) -> list:
    """Set font size. size = any number e.g. 8,9,10,11,12,14,16,18,20,24,28,36,48,72."""
    return [
        *_home_tab(),
        _ribbon("f", "s"),
        _wait(0.3),
        _hotkey("ctrl", "a"),
        _type(str(size)),
        _key("enter"),
    ]

def increase_font_size(**kw) -> list:
    """Increase font size by one step (Ctrl+Shift+>)."""
    return [_hotkey("ctrl", "shift", ".")]

def decrease_font_size(**kw) -> list:
    """Decrease font size by one step (Ctrl+Shift+<)."""
    return [_hotkey("ctrl", "shift", ",")]

def set_font(font_name: str = "Arial", **kw) -> list:
    """Set font family. font_name = e.g. Arial, Calibri, Times New Roman, Verdana, Courier New."""
    return [
        *_home_tab(),
        _ribbon("f", "f"),
        _wait(0.3),
        _hotkey("ctrl", "a"),
        _type(font_name),
        _key("enter"),
    ]

def set_font_color_last(**kw) -> list:
    """Apply the last-used font color."""
    return [*_home_tab(), _ribbon("f", "c")]

def set_fill_color_last(**kw) -> list:
    """Apply the last-used fill/background color."""
    return [*_home_tab(), _ribbon("h")]

def open_format_cells(**kw) -> list:
    """Open Format Cells dialog (full control over font, border, fill, number)."""
    return [_hotkey("ctrl", "1"), _wait(0.5)]


# ── ALIGNMENT ────────────────────────────────────────────────────────────────

def align_left(**kw) -> list:
    return [_hotkey("ctrl", "l")]

def align_center(**kw) -> list:
    return [_hotkey("ctrl", "e")]

def align_right(**kw) -> list:
    return [*_home_tab(), _ribbon("a", "r")]

def align_top(**kw) -> list:
    return [*_home_tab(), _ribbon("a", "t")]

def align_middle_vertical(**kw) -> list:
    return [*_home_tab(), _ribbon("a", "m")]

def align_bottom(**kw) -> list:
    return [*_home_tab(), _ribbon("a", "b")]

def wrap_text(**kw) -> list:
    """Toggle wrap text in selected cell(s)."""
    return [*_home_tab(), _ribbon("w")]

def merge_and_center(**kw) -> list:
    """Merge selected cells and center. requires_confirmation=True."""
    return [*_home_tab(), _ribbon("m", "c")]

def merge_cells(**kw) -> list:
    """Merge selected cells (no centering). requires_confirmation=True."""
    return [*_home_tab(), _ribbon("m", "m")]

def unmerge_cells(**kw) -> list:
    """Unmerge merged cells."""
    return [*_home_tab(), _ribbon("m", "u")]

def increase_indent(**kw) -> list:
    return [*_home_tab(), _ribbon("6")]

def decrease_indent(**kw) -> list:
    return [*_home_tab(), _ribbon("5")]

def rotate_text(**kw) -> list:
    """Open text rotation options."""
    return [*_home_tab(), _ribbon("f", "q")]


# ── BORDERS ──────────────────────────────────────────────────────────────────

def borders_all(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "a")]

def borders_outside(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "s")]

def borders_thick_box(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "t")]

def borders_bottom(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "o")]

def borders_top(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "p")]

def borders_left(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "l")]

def borders_right_border(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "r")]

def borders_none(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "n")]

def borders_double_bottom(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "b")]

def borders_thick_bottom(**kw) -> list:
    return [*_home_tab(), _ribbon("b", "k")]

def open_borders_dialog(**kw) -> list:
    """Open More Borders dialog for custom border styles."""
    return [*_home_tab(), _ribbon("b", "m")]


# ── NUMBER FORMAT ────────────────────────────────────────────────────────────

def format_general(**kw) -> list:
    return [_hotkey("ctrl", "shift", "~")]

def format_number(**kw) -> list:
    """Number with 2 decimal places."""
    return [_hotkey("ctrl", "shift", "1")]

def format_currency(**kw) -> list:
    """Currency format ($)."""
    return [_hotkey("ctrl", "shift", "4")]

def format_percentage(**kw) -> list:
    return [_hotkey("ctrl", "shift", "5")]

def format_scientific(**kw) -> list:
    return [_hotkey("ctrl", "shift", "6")]

def format_date(**kw) -> list:
    return [_hotkey("ctrl", "shift", "3")]

def format_time(**kw) -> list:
    return [_hotkey("ctrl", "shift", "2")]

def format_text(**kw) -> list:
    """Format as text (stores as-is, no calculations)."""
    return [*_home_tab(), _ribbon("n", "t")]

def format_custom(format_code: str = "0.00", **kw) -> list:
    """Apply custom number format code. Opens Format Cells → Number → Custom."""
    return [
        _hotkey("ctrl", "1"), _wait(0.6),
        # Format Cells dialog opens on last-used tab; navigate to Number tab
        _key("tab"), _wait(0.2),   # may need Ctrl+Tab to reach Number tab
        # Simpler: just open and let user see it — custom codes need dialog interaction
        # For fully automated: type the code in the Custom field
    ]


# ── COLUMN / ROW SIZE ────────────────────────────────────────────────────────

def autofit_column_width(**kw) -> list:
    """AutoFit selected column(s) width to content."""
    return [*_home_tab(), _ribbon("o", "i")]

def autofit_row_height(**kw) -> list:
    """AutoFit selected row(s) height to content."""
    return [*_home_tab(), _ribbon("o", "a")]

def set_column_width(width: float = 20, **kw) -> list:
    """Set column width to exact value."""
    return [
        *_home_tab(), _ribbon("o", "w"),
        _wait(0.4), _type(str(width)), _key("enter"),
    ]

def set_row_height(height: float = 20, **kw) -> list:
    """Set row height to exact value."""
    return [
        *_home_tab(), _ribbon("o", "h"),
        _wait(0.4), _type(str(height)), _key("enter"),
    ]

def hide_column(**kw) -> list:
    return [_hotkey("ctrl", "0")]

def unhide_column(**kw) -> list:
    return [_hotkey("ctrl", "shift", "0")]

def hide_row(**kw) -> list:
    return [_hotkey("ctrl", "9")]

def unhide_row(**kw) -> list:
    return [_hotkey("ctrl", "shift", "9")]

def group_rows(**kw) -> list:
    return [_hotkey("alt", "shift", "right")]

def ungroup_rows(**kw) -> list:
    return [_hotkey("alt", "shift", "left")]


# ── INSERT / DELETE ROWS & COLUMNS ───────────────────────────────────────────

def insert_row(**kw) -> list:
    """Insert row above selected row. Selects current row first."""
    return [
        _hotkey("shift", "space"),     # select entire row
        _wait(0.2),
        _hotkey("ctrl", "shift", "="), # insert
    ]

def delete_row(**kw) -> list:
    """Delete selected row. requires_confirmation=True."""
    return [
        _hotkey("shift", "space"),
        _wait(0.2),
        _hotkey("ctrl", "-"),
    ]

def insert_column(**kw) -> list:
    """Insert column before selected column."""
    return [
        _hotkey("ctrl", "space"),
        _wait(0.2),
        _hotkey("ctrl", "shift", "="),
    ]

def delete_column(**kw) -> list:
    """Delete selected column. requires_confirmation=True."""
    return [
        _hotkey("ctrl", "space"),
        _wait(0.2),
        _hotkey("ctrl", "-"),
    ]

def insert_rows_n(n: int = 1, **kw) -> list:
    """Insert n rows above current position."""
    steps = []
    for _ in range(n):
        steps += insert_row()
        steps.append(_wait(0.3))
    return steps

def insert_cells_shift_right(**kw) -> list:
    return [*_home_tab(), _ribbon("i", "i"), _wait(0.3), _key("right"), _key("enter")]

def insert_cells_shift_down(**kw) -> list:
    return [*_home_tab(), _ribbon("i", "i"), _wait(0.3), _key("down"), _key("enter")]

def delete_cells_shift_left(**kw) -> list:
    return [*_home_tab(), _ribbon("d", "d"), _wait(0.3), _key("left"), _key("enter")]

def delete_cells_shift_up(**kw) -> list:
    return [*_home_tab(), _ribbon("d", "d"), _wait(0.3), _key("up"), _key("enter")]


# ── EDITING ───────────────────────────────────────────────────────────────────

def undo(**kw) -> list:
    return [_hotkey("ctrl", "z")]

def redo(**kw) -> list:
    return [_hotkey("ctrl", "y")]

def copy(**kw) -> list:
    return [_hotkey("ctrl", "c")]

def cut(**kw) -> list:
    return [_hotkey("ctrl", "x")]

def paste(**kw) -> list:
    return [_hotkey("ctrl", "v")]

def paste_values_only(**kw) -> list:
    """Paste values only (no formatting)."""
    return [_hotkey("ctrl", "alt", "v"), _wait(0.4), _key("v"), _key("enter")]

def paste_formats_only(**kw) -> list:
    """Paste formatting only."""
    return [_hotkey("ctrl", "alt", "v"), _wait(0.4), _key("t"), _key("enter")]

def paste_special(**kw) -> list:
    """Open Paste Special dialog."""
    return [_hotkey("ctrl", "alt", "v"), _wait(0.4)]

def fill_down(**kw) -> list:
    return [_hotkey("ctrl", "d")]

def fill_right(**kw) -> list:
    return [_hotkey("ctrl", "r")]

def fill_up(**kw) -> list:
    return [*_home_tab(), _ribbon("f", "i", "u")]

def flash_fill(**kw) -> list:
    return [_hotkey("ctrl", "e")]

def autosum(**kw) -> list:
    return [_hotkey("alt", "=")]

def find(**kw) -> list:
    return [_hotkey("ctrl", "f")]

def find_replace(**kw) -> list:
    return [_hotkey("ctrl", "h")]

def edit_cell(**kw) -> list:
    """Enter edit mode for current cell (F2)."""
    return [_key("f2")]

def select_all(**kw) -> list:
    return [_hotkey("ctrl", "a")]

def select_row(**kw) -> list:
    return [_hotkey("shift", "space")]

def select_column(**kw) -> list:
    """Select entire column (uses Ctrl+Space for Excel select — no conflict with Alt+. hotkey)."""
    return [*_home_tab(), _ribbon("s", "s", "c")]  # Home → Format → Select column

def type_in_cell(text: str = "", **kw) -> list:
    """Type text into the current cell and press Enter."""
    return [{"action": "type_text", "text": str(text)}, _key("enter")]

def enter_formula(formula: str = "=SUM(A1:A10)", **kw) -> list:
    """Type a formula and press Enter. formula should start with ="""
    if not formula.startswith("="):
        formula = "=" + formula
    return [{"action": "type_text", "text": formula}, _key("enter")]


# ── NAVIGATION ────────────────────────────────────────────────────────────────

def go_to_cell(cell_ref: str = "A1", **kw) -> list:
    """Navigate to a specific cell reference like A1, B5, C10."""
    return [_hotkey("ctrl", "g"), _wait(0.4), _type(cell_ref), _key("enter")]

def go_to_a1(**kw) -> list:
    return [_hotkey("ctrl", "home")]

def go_to_last_cell(**kw) -> list:
    return [_hotkey("ctrl", "end")]

def next_sheet(**kw) -> list:
    return [_hotkey("ctrl", "pagedown")]

def previous_sheet(**kw) -> list:
    return [_hotkey("ctrl", "pageup")]

def move_right(**kw) -> list:
    return [_key("tab")]

def move_down(**kw) -> list:
    return [_key("enter")]

def move_up(**kw) -> list:
    return [_key("up")]

def move_left(**kw) -> list:
    return [_key("left")]


# ── WORKBOOK / FILE ───────────────────────────────────────────────────────────

def save(**kw) -> list:
    return [_hotkey("ctrl", "s")]

def save_as(**kw) -> list:
    return [_key("f12")]

def new_workbook(**kw) -> list:
    return [_hotkey("ctrl", "n")]

def open_file(**kw) -> list:
    return [_hotkey("ctrl", "o")]

def print_file(**kw) -> list:
    return [_hotkey("ctrl", "p")]

def close_workbook(**kw) -> list:
    """requires_confirmation=True."""
    return [_hotkey("ctrl", "w")]

def new_sheet(**kw) -> list:
    return [_hotkey("shift", "f11")]

def rename_sheet(**kw) -> list:
    """Double-click tab to rename — opens rename mode via ribbon."""
    return [*_home_tab(), _ribbon("o", "r"), _wait(0.4)]

def delete_sheet(**kw) -> list:
    """requires_confirmation=True."""
    return [*_home_tab(), _ribbon("d", "s")]

def move_sheet_left(**kw) -> list:
    return [*_home_tab(), _ribbon("o", "m"), _wait(0.4)]


# ── DATA / SORT / FILTER ──────────────────────────────────────────────────────

def sort_ascending(**kw) -> list:
    return [*_data_tab(), _ribbon("s", "a")]

def sort_descending(**kw) -> list:
    return [*_data_tab(), _ribbon("s", "d")]

def open_sort_dialog(**kw) -> list:
    return [*_data_tab(), _ribbon("s", "s"), _wait(0.4)]

def toggle_filter(**kw) -> list:
    return [_hotkey("ctrl", "shift", "l")]

def clear_filter(**kw) -> list:
    return [*_data_tab(), _ribbon("s", "c")]

def remove_duplicates(**kw) -> list:
    return [*_data_tab(), _ribbon("m"), _wait(0.4)]

def text_to_columns(**kw) -> list:
    return [*_data_tab(), _ribbon("e"), _wait(0.4)]

def data_validation(**kw) -> list:
    return [*_data_tab(), _ribbon("v", "v"), _wait(0.4)]

def group_data(**kw) -> list:
    return [*_data_tab(), _ribbon("g", "g"), _wait(0.4)]

def ungroup_data(**kw) -> list:
    return [*_data_tab(), _ribbon("u", "u"), _wait(0.4)]

def subtotal(**kw) -> list:
    return [*_data_tab(), _ribbon("b"), _wait(0.4)]

def refresh_all(**kw) -> list:
    return [_hotkey("ctrl", "alt", "f5")]

def what_if_analysis(**kw) -> list:
    return [*_data_tab(), _ribbon("w"), _wait(0.4)]


# ── INSERT TAB ────────────────────────────────────────────────────────────────

def insert_table(**kw) -> list:
    return [_hotkey("ctrl", "t"), _wait(0.4)]

def insert_pivot_table(**kw) -> list:
    return [*_insert_tab(), _ribbon("v"), _wait(0.4)]

def insert_chart_embedded(**kw) -> list:
    """Insert chart on same sheet from selected data."""
    return [_hotkey("alt", "f1")]

def insert_chart_new_sheet(**kw) -> list:
    return [_key("f11")]

def insert_sparkline(**kw) -> list:
    return [*_insert_tab(), _ribbon("s", "n"), _wait(0.4)]

def insert_hyperlink(**kw) -> list:
    return [_hotkey("ctrl", "k"), _wait(0.4)]

def insert_comment(**kw) -> list:
    return [_hotkey("shift", "f2")]

def insert_function(**kw) -> list:
    return [_hotkey("shift", "f3"), _wait(0.4)]

def insert_picture(**kw) -> list:
    return [*_insert_tab(), _ribbon("p", "p"), _wait(0.4)]

def insert_shapes(**kw) -> list:
    return [*_insert_tab(), _ribbon("s", "h"), _wait(0.4)]

def insert_text_box(**kw) -> list:
    return [*_insert_tab(), _ribbon("x"), _wait(0.4)]

def insert_wordart(**kw) -> list:
    return [*_insert_tab(), _ribbon("w"), _wait(0.4)]

def insert_header_footer(**kw) -> list:
    return [*_insert_tab(), _ribbon("h"), _wait(0.4)]


# ── PAGE LAYOUT ───────────────────────────────────────────────────────────────

def page_orientation_portrait(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("o", "r")]

def page_orientation_landscape(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("o", "l")]

def page_margins(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("m"), _wait(0.4)]

def page_size(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("s", "z"), _wait(0.4)]

def set_print_area(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("r", "s")]

def clear_print_area(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("r", "c")]

def fit_to_one_page(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("s", "f"), _wait(0.3), _type("1"), _key("tab"), _type("1"), _key("enter")]

def show_gridlines(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("v", "g")]

def show_headings(**kw) -> list:
    return [*_page_layout_tab(), _ribbon("v", "h")]


# ── VIEW ──────────────────────────────────────────────────────────────────────

def freeze_top_row(**kw) -> list:
    return [*_view_tab(), _ribbon("f", "r")]

def freeze_first_column(**kw) -> list:
    return [*_view_tab(), _ribbon("f", "c")]

def freeze_panes(**kw) -> list:
    """Freeze at current cell position."""
    return [*_view_tab(), _ribbon("f", "f")]

def unfreeze_panes(**kw) -> list:
    return [*_view_tab(), _ribbon("f", "f")]   # same toggle

def zoom_100(**kw) -> list:
    return [*_view_tab(), _ribbon("j")]

def zoom_to_selection(**kw) -> list:
    return [*_view_tab(), _ribbon("g")]

def split_view(**kw) -> list:
    return [*_view_tab(), _ribbon("s")]

def normal_view(**kw) -> list:
    return [*_view_tab(), _ribbon("l")]

def page_layout_view(**kw) -> list:
    return [*_view_tab(), _ribbon("p")]

def page_break_view(**kw) -> list:
    return [*_view_tab(), _ribbon("i")]


# ── FORMULAS ──────────────────────────────────────────────────────────────────

def toggle_show_formulas(**kw) -> list:
    return [_hotkey("ctrl", "`")]

def calculate_now(**kw) -> list:
    return [_key("f9")]

def calculate_sheet(**kw) -> list:
    return [_hotkey("shift", "f9")]

def name_manager(**kw) -> list:
    return [_hotkey("ctrl", "f3"), _wait(0.4)]

def trace_precedents(**kw) -> list:
    return [*_formulas_tab(), _ribbon("p"), _wait(0.3)]

def trace_dependents(**kw) -> list:
    return [*_formulas_tab(), _ribbon("d"), _wait(0.3)]

def remove_arrows(**kw) -> list:
    return [*_formulas_tab(), _ribbon("a", "a")]

def evaluate_formula(**kw) -> list:
    return [*_formulas_tab(), _ribbon("v"), _wait(0.4)]


# ── REVIEW ────────────────────────────────────────────────────────────────────

def spell_check(**kw) -> list:
    return [_key("f7")]

def protect_sheet(**kw) -> list:
    return [*_review_tab(), _ribbon("p", "s"), _wait(0.4)]

def protect_workbook(**kw) -> list:
    return [*_review_tab(), _ribbon("p", "w"), _wait(0.4)]

def share_workbook(**kw) -> list:
    return [*_review_tab(), _ribbon("s", "h"), _wait(0.4)]

def track_changes(**kw) -> list:
    return [*_review_tab(), _ribbon("g"), _wait(0.4)]

def add_comment(**kw) -> list:
    return [_hotkey("shift", "f2")]

def delete_comment(**kw) -> list:
    return [*_review_tab(), _ribbon("d", "d")]

def show_all_comments(**kw) -> list:
    return [*_review_tab(), _ribbon("s", "h", "c")]


# ── COMPOUND ACTIONS (multi-step common tasks) ────────────────────────────────

def format_as_header(size: int = 14, **kw) -> list:
    """Bold + larger font + center — common for header rows."""
    return [
        _hotkey("ctrl", "b"),
        _wait(0.1),
        _hotkey("ctrl", "e"),
        _wait(0.1),
        *set_font_size(size),
    ]

def format_as_currency_with_borders(**kw) -> list:
    return [*format_currency(), _wait(0.1), *borders_all()]

def highlight_row(**kw) -> list:
    """Select the entire row and apply fill color."""
    return [*select_row(), _wait(0.1), *set_fill_color_last()]

def make_table_with_filter(**kw) -> list:
    return [*insert_table()]

def sum_column(**kw) -> list:
    """AutoSum the column."""
    return [*autosum()]

def copy_format(**kw) -> list:
    """Format Painter — copy formatting (opens painter, user clicks target)."""
    return [*_home_tab(), _ribbon("f", "p")]

def center_across_selection(**kw) -> list:
    """Center text across selection without merging."""
    return [
        _hotkey("ctrl", "1"), _wait(0.5),
        # In Format Cells dialog, navigate to Alignment tab
        _hotkey("ctrl", "tab"), _wait(0.2),
    ]

def apply_table_style(style: str = "TableStyleMedium2", **kw) -> list:
    """Apply a named table style. Must have a table selected first."""
    return [*_home_tab(), _ribbon("t"), _wait(0.4)]

def autofit_all_columns(**kw) -> list:
    """Select all then autofit all columns."""
    return [
        _hotkey("ctrl", "a"),
        _wait(0.2),
        *_home_tab(),
        _ribbon("o", "i"),
    ]

def remove_all_filters(**kw) -> list:
    return [*_data_tab(), _ribbon("s", "c")]

def select_visible_cells(**kw) -> list:
    """Alt+; selects only visible cells (useful after filtering)."""
    return [_hotkey("alt", ";")]

def enter_current_date(**kw) -> list:
    """Type today's date in the cell."""
    return [_hotkey("ctrl", ";"), _key("enter")]

def enter_current_time(**kw) -> list:
    return [_hotkey("ctrl", "shift", ";"), _key("enter")]

def repeat_last_action(**kw) -> list:
    """F4 repeats the last action."""
    return [_key("f4")]


# ════════════════════════════════════════════════════════════════════════
# REGISTRY — maps action_id → (function, description, requires_confirmation, param_names)
# ════════════════════════════════════════════════════════════════════════

REGISTRY: dict[str, dict] = {
    # id: {fn, desc, confirm, params}
    "bold":                    {"fn": bold,                    "desc": "Toggle bold",                                   "confirm": False, "params": []},
    "italic":                  {"fn": italic,                  "desc": "Toggle italic",                                 "confirm": False, "params": []},
    "underline":               {"fn": underline,               "desc": "Toggle underline",                              "confirm": False, "params": []},
    "strikethrough":           {"fn": strikethrough,           "desc": "Toggle strikethrough",                          "confirm": False, "params": []},
    "bold_italic":             {"fn": bold_italic,             "desc": "Bold and italic",                               "confirm": False, "params": []},
    "bold_underline":          {"fn": bold_underline,          "desc": "Bold and underline",                            "confirm": False, "params": []},
    "clear_formatting":        {"fn": clear_formatting,        "desc": "Remove all formatting",                         "confirm": False, "params": []},
    "clear_contents":          {"fn": clear_contents,          "desc": "Delete cell contents",                          "confirm": True,  "params": []},
    "clear_all":               {"fn": clear_all,               "desc": "Clear contents and formatting",                 "confirm": True,  "params": []},

    "set_font_size":           {"fn": set_font_size,           "desc": "Set font size",                                 "confirm": False, "params": ["size"]},
    "increase_font_size":      {"fn": increase_font_size,      "desc": "Increase font size by one step",                "confirm": False, "params": []},
    "decrease_font_size":      {"fn": decrease_font_size,      "desc": "Decrease font size by one step",                "confirm": False, "params": []},
    "set_font":                {"fn": set_font,                "desc": "Set font family",                               "confirm": False, "params": ["font_name"]},
    "set_font_color_last":     {"fn": set_font_color_last,     "desc": "Apply last-used font color",                    "confirm": False, "params": []},
    "set_fill_color_last":     {"fn": set_fill_color_last,     "desc": "Apply last-used fill color",                    "confirm": False, "params": []},
    "open_format_cells":       {"fn": open_format_cells,       "desc": "Open Format Cells dialog",                      "confirm": False, "params": []},

    "align_left":              {"fn": align_left,              "desc": "Align text left",                               "confirm": False, "params": []},
    "align_center":            {"fn": align_center,            "desc": "Align text center",                             "confirm": False, "params": []},
    "align_right":             {"fn": align_right,             "desc": "Align text right",                              "confirm": False, "params": []},
    "align_top":               {"fn": align_top,               "desc": "Align cell content to top",                     "confirm": False, "params": []},
    "align_middle_vertical":   {"fn": align_middle_vertical,   "desc": "Align cell content to middle vertically",       "confirm": False, "params": []},
    "align_bottom":            {"fn": align_bottom,            "desc": "Align cell content to bottom",                  "confirm": False, "params": []},
    "wrap_text":               {"fn": wrap_text,               "desc": "Toggle wrap text",                              "confirm": False, "params": []},
    "merge_and_center":        {"fn": merge_and_center,        "desc": "Merge cells and center",                        "confirm": True,  "params": []},
    "merge_cells":             {"fn": merge_cells,             "desc": "Merge cells only",                              "confirm": True,  "params": []},
    "unmerge_cells":           {"fn": unmerge_cells,           "desc": "Unmerge cells",                                 "confirm": False, "params": []},
    "increase_indent":         {"fn": increase_indent,         "desc": "Increase indent",                               "confirm": False, "params": []},
    "decrease_indent":         {"fn": decrease_indent,         "desc": "Decrease indent",                               "confirm": False, "params": []},

    "borders_all":             {"fn": borders_all,             "desc": "Apply all borders",                             "confirm": False, "params": []},
    "borders_outside":         {"fn": borders_outside,         "desc": "Apply outside border only",                     "confirm": False, "params": []},
    "borders_thick_box":       {"fn": borders_thick_box,       "desc": "Apply thick box border",                        "confirm": False, "params": []},
    "borders_bottom":          {"fn": borders_bottom,          "desc": "Apply bottom border",                           "confirm": False, "params": []},
    "borders_top":             {"fn": borders_top,             "desc": "Apply top border",                              "confirm": False, "params": []},
    "borders_none":            {"fn": borders_none,            "desc": "Remove all borders",                            "confirm": False, "params": []},
    "open_borders_dialog":     {"fn": open_borders_dialog,     "desc": "Open More Borders dialog",                      "confirm": False, "params": []},

    "format_general":          {"fn": format_general,          "desc": "Format as general",                             "confirm": False, "params": []},
    "format_number":           {"fn": format_number,           "desc": "Format as number (2 decimal places)",           "confirm": False, "params": []},
    "format_currency":         {"fn": format_currency,         "desc": "Format as currency",                            "confirm": False, "params": []},
    "format_percentage":       {"fn": format_percentage,       "desc": "Format as percentage",                          "confirm": False, "params": []},
    "format_scientific":       {"fn": format_scientific,       "desc": "Format as scientific notation",                 "confirm": False, "params": []},
    "format_date":             {"fn": format_date,             "desc": "Format as date",                                "confirm": False, "params": []},
    "format_time":             {"fn": format_time,             "desc": "Format as time",                                "confirm": False, "params": []},

    "autofit_column_width":    {"fn": autofit_column_width,    "desc": "AutoFit column width",                          "confirm": False, "params": []},
    "autofit_row_height":      {"fn": autofit_row_height,      "desc": "AutoFit row height",                            "confirm": False, "params": []},
    "autofit_all_columns":     {"fn": autofit_all_columns,     "desc": "AutoFit all columns",                           "confirm": False, "params": []},
    "set_column_width":        {"fn": set_column_width,        "desc": "Set column width to exact value",               "confirm": False, "params": ["width"]},
    "set_row_height":          {"fn": set_row_height,          "desc": "Set row height to exact value",                 "confirm": False, "params": ["height"]},
    "hide_column":             {"fn": hide_column,             "desc": "Hide selected column",                          "confirm": False, "params": []},
    "unhide_column":           {"fn": unhide_column,           "desc": "Unhide column",                                 "confirm": False, "params": []},
    "hide_row":                {"fn": hide_row,                "desc": "Hide selected row",                             "confirm": False, "params": []},
    "unhide_row":              {"fn": unhide_row,              "desc": "Unhide row",                                    "confirm": False, "params": []},

    "insert_row":              {"fn": insert_row,              "desc": "Insert row above current",                      "confirm": False, "params": []},
    "delete_row":              {"fn": delete_row,              "desc": "Delete current row",                            "confirm": True,  "params": []},
    "insert_column":           {"fn": insert_column,           "desc": "Insert column before current",                  "confirm": False, "params": []},
    "delete_column":           {"fn": delete_column,           "desc": "Delete current column",                         "confirm": True,  "params": []},

    "undo":                    {"fn": undo,                    "desc": "Undo last action",                              "confirm": False, "params": []},
    "redo":                    {"fn": redo,                    "desc": "Redo last undone action",                       "confirm": False, "params": []},
    "copy":                    {"fn": copy,                    "desc": "Copy selected cell(s)",                         "confirm": False, "params": []},
    "cut":                     {"fn": cut,                     "desc": "Cut selected cell(s)",                          "confirm": False, "params": []},
    "paste":                   {"fn": paste,                   "desc": "Paste",                                         "confirm": False, "params": []},
    "paste_values_only":       {"fn": paste_values_only,       "desc": "Paste values only (no formatting)",             "confirm": False, "params": []},
    "paste_formats_only":      {"fn": paste_formats_only,      "desc": "Paste formatting only",                         "confirm": False, "params": []},
    "paste_special":           {"fn": paste_special,           "desc": "Open Paste Special dialog",                     "confirm": False, "params": []},
    "fill_down":               {"fn": fill_down,               "desc": "Fill down",                                     "confirm": False, "params": []},
    "fill_right":              {"fn": fill_right,              "desc": "Fill right",                                    "confirm": False, "params": []},
    "flash_fill":              {"fn": flash_fill,              "desc": "Flash fill (pattern recognition)",              "confirm": False, "params": []},
    "autosum":                 {"fn": autosum,                 "desc": "AutoSum selected range",                        "confirm": False, "params": []},
    "find":                    {"fn": find,                    "desc": "Open Find dialog",                              "confirm": False, "params": []},
    "find_replace":            {"fn": find_replace,            "desc": "Open Find & Replace dialog",                    "confirm": False, "params": []},
    "edit_cell":               {"fn": edit_cell,               "desc": "Enter edit mode for current cell",              "confirm": False, "params": []},
    "select_all":              {"fn": select_all,              "desc": "Select all cells",                              "confirm": False, "params": []},
    "type_in_cell":            {"fn": type_in_cell,            "desc": "Type text into current cell",                   "confirm": False, "params": ["text"]},
    "enter_formula":           {"fn": enter_formula,           "desc": "Enter a formula",                               "confirm": False, "params": ["formula"]},
    "enter_current_date":      {"fn": enter_current_date,      "desc": "Insert today's date",                           "confirm": False, "params": []},
    "enter_current_time":      {"fn": enter_current_time,      "desc": "Insert current time",                           "confirm": False, "params": []},
    "repeat_last_action":      {"fn": repeat_last_action,      "desc": "Repeat last action (F4)",                       "confirm": False, "params": []},

    "go_to_cell":              {"fn": go_to_cell,              "desc": "Navigate to a specific cell",                   "confirm": False, "params": ["cell_ref"]},
    "go_to_a1":                {"fn": go_to_a1,                "desc": "Go to cell A1",                                 "confirm": False, "params": []},
    "go_to_last_cell":         {"fn": go_to_last_cell,         "desc": "Go to last used cell",                          "confirm": False, "params": []},
    "next_sheet":              {"fn": next_sheet,              "desc": "Go to next sheet",                              "confirm": False, "params": []},
    "previous_sheet":          {"fn": previous_sheet,          "desc": "Go to previous sheet",                          "confirm": False, "params": []},

    "save":                    {"fn": save,                    "desc": "Save workbook",                                 "confirm": False, "params": []},
    "save_as":                 {"fn": save_as,                 "desc": "Save As",                                       "confirm": False, "params": []},
    "new_workbook":            {"fn": new_workbook,            "desc": "Create new workbook",                           "confirm": False, "params": []},
    "open_file":               {"fn": open_file,               "desc": "Open file dialog",                              "confirm": False, "params": []},
    "print_file":              {"fn": print_file,              "desc": "Print",                                         "confirm": False, "params": []},
    "close_workbook":          {"fn": close_workbook,          "desc": "Close workbook",                                "confirm": True,  "params": []},
    "new_sheet":               {"fn": new_sheet,               "desc": "Insert new sheet",                              "confirm": False, "params": []},
    "delete_sheet":            {"fn": delete_sheet,            "desc": "Delete current sheet",                          "confirm": True,  "params": []},

    "sort_ascending":          {"fn": sort_ascending,          "desc": "Sort ascending (A to Z)",                       "confirm": False, "params": []},
    "sort_descending":         {"fn": sort_descending,         "desc": "Sort descending (Z to A)",                      "confirm": False, "params": []},
    "open_sort_dialog":        {"fn": open_sort_dialog,        "desc": "Open Sort dialog",                              "confirm": False, "params": []},
    "toggle_filter":           {"fn": toggle_filter,           "desc": "Toggle AutoFilter",                             "confirm": False, "params": []},
    "remove_duplicates":       {"fn": remove_duplicates,       "desc": "Remove duplicate rows",                         "confirm": True,  "params": []},
    "text_to_columns":         {"fn": text_to_columns,         "desc": "Text to columns wizard",                        "confirm": False, "params": []},
    "data_validation":         {"fn": data_validation,         "desc": "Open Data Validation dialog",                   "confirm": False, "params": []},
    "refresh_all":             {"fn": refresh_all,             "desc": "Refresh all data connections",                  "confirm": False, "params": []},

    "insert_table":            {"fn": insert_table,            "desc": "Insert table from selection",                   "confirm": False, "params": []},
    "insert_pivot_table":      {"fn": insert_pivot_table,      "desc": "Insert PivotTable",                             "confirm": False, "params": []},
    "insert_chart_embedded":   {"fn": insert_chart_embedded,   "desc": "Insert chart on current sheet",                 "confirm": False, "params": []},
    "insert_chart_new_sheet":  {"fn": insert_chart_new_sheet,  "desc": "Insert chart on new sheet",                     "confirm": False, "params": []},
    "insert_hyperlink":        {"fn": insert_hyperlink,        "desc": "Insert hyperlink",                              "confirm": False, "params": []},
    "insert_comment":          {"fn": insert_comment,          "desc": "Insert comment",                                "confirm": False, "params": []},
    "insert_function":         {"fn": insert_function,         "desc": "Open Insert Function dialog",                   "confirm": False, "params": []},
    "insert_picture":          {"fn": insert_picture,          "desc": "Insert picture",                                "confirm": False, "params": []},

    "page_orientation_portrait":  {"fn": page_orientation_portrait,  "desc": "Set page orientation to portrait",  "confirm": False, "params": []},
    "page_orientation_landscape": {"fn": page_orientation_landscape, "desc": "Set page orientation to landscape", "confirm": False, "params": []},
    "set_print_area":          {"fn": set_print_area,          "desc": "Set print area",                                "confirm": False, "params": []},
    "clear_print_area":        {"fn": clear_print_area,        "desc": "Clear print area",                              "confirm": False, "params": []},
    "show_gridlines":          {"fn": show_gridlines,          "desc": "Toggle gridlines visibility",                   "confirm": False, "params": []},

    "freeze_top_row":          {"fn": freeze_top_row,          "desc": "Freeze top row",                                "confirm": False, "params": []},
    "freeze_first_column":     {"fn": freeze_first_column,     "desc": "Freeze first column",                           "confirm": False, "params": []},
    "freeze_panes":            {"fn": freeze_panes,            "desc": "Freeze panes at current cell",                  "confirm": False, "params": []},
    "unfreeze_panes":          {"fn": unfreeze_panes,          "desc": "Unfreeze panes",                                "confirm": False, "params": []},
    "zoom_100":                {"fn": zoom_100,                "desc": "Zoom to 100%",                                  "confirm": False, "params": []},

    "toggle_show_formulas":    {"fn": toggle_show_formulas,    "desc": "Show/hide formulas",                            "confirm": False, "params": []},
    "calculate_now":           {"fn": calculate_now,           "desc": "Calculate now",                                 "confirm": False, "params": []},
    "spell_check":             {"fn": spell_check,             "desc": "Run spell check",                               "confirm": False, "params": []},
    "protect_sheet":           {"fn": protect_sheet,           "desc": "Protect sheet",                                 "confirm": False, "params": []},
    "protect_workbook":        {"fn": protect_workbook,        "desc": "Protect workbook",                              "confirm": False, "params": []},
    "add_comment":             {"fn": add_comment,             "desc": "Add comment to cell",                           "confirm": False, "params": []},

    # Compound
    "format_as_header":        {"fn": format_as_header,        "desc": "Format as header (bold + center + larger font)", "confirm": False, "params": ["size"]},
    "format_currency_borders": {"fn": format_as_currency_with_borders, "desc": "Currency format with all borders",      "confirm": False, "params": []},
    "make_table_with_filter":  {"fn": make_table_with_filter,  "desc": "Create table with filter from selection",       "confirm": False, "params": []},
    "sum_column":              {"fn": sum_column,              "desc": "AutoSum at current position",                   "confirm": False, "params": []},
    "copy_format":             {"fn": copy_format,             "desc": "Copy formatting with Format Painter",           "confirm": False, "params": []},
    "select_visible_cells":    {"fn": select_visible_cells,    "desc": "Select only visible cells",                     "confirm": False, "params": []},
    "group_rows":              {"fn": group_rows,              "desc": "Group selected rows",                           "confirm": False, "params": []},
    "ungroup_rows":            {"fn": ungroup_rows,            "desc": "Ungroup selected rows",                         "confirm": False, "params": []},
}

# ─── Public API ───────────────────────────────────────────────────────────────

def get_steps(action_id: str, **params: Any) -> list:
    """Return step list for action_id with optional params."""
    entry = REGISTRY.get(action_id)
    if not entry:
        raise KeyError(f"Unknown action: {action_id!r}. Available: {sorted(REGISTRY.keys())}")
    return entry["fn"](**params)

def get_description(action_id: str) -> str:
    return REGISTRY.get(action_id, {}).get("desc", action_id)

def requires_confirmation(action_id: str) -> bool:
    return REGISTRY.get(action_id, {}).get("confirm", False)

def list_actions() -> list[dict]:
    """Return all actions as a list of {id, desc, confirm, params} for the LLM prompt."""
    return [
        {"id": k, "desc": v["desc"], "confirm": v["confirm"], "params": v["params"]}
        for k, v in REGISTRY.items()
    ]

def build_action_menu_for_llm() -> str:
    """Build a compact string listing all available actions for the LLM system prompt."""
    lines = []
    categories = {
        "FORMATTING":    ["bold","italic","underline","strikethrough","bold_italic","bold_underline","clear_formatting","clear_contents","clear_all"],
        "FONT":          ["set_font_size","increase_font_size","decrease_font_size","set_font","set_font_color_last","set_fill_color_last","open_format_cells"],
        "ALIGNMENT":     ["align_left","align_center","align_right","align_top","align_middle_vertical","align_bottom","wrap_text","merge_and_center","merge_cells","unmerge_cells","increase_indent","decrease_indent"],
        "BORDERS":       ["borders_all","borders_outside","borders_thick_box","borders_bottom","borders_top","borders_none","open_borders_dialog"],
        "NUMBER FMT":    ["format_general","format_number","format_currency","format_percentage","format_scientific","format_date","format_time"],
        "COL/ROW SIZE":  ["autofit_column_width","autofit_row_height","autofit_all_columns","set_column_width","set_row_height","hide_column","unhide_column","hide_row","unhide_row"],
        "INSERT/DELETE": ["insert_row","delete_row","insert_column","delete_column"],
        "EDITING":       ["undo","redo","copy","cut","paste","paste_values_only","paste_formats_only","fill_down","fill_right","flash_fill","autosum","find","find_replace","type_in_cell","enter_formula","enter_current_date","repeat_last_action"],
        "NAVIGATE":      ["go_to_cell","go_to_a1","go_to_last_cell","next_sheet","previous_sheet"],
        "FILE":          ["save","save_as","new_workbook","print_file","close_workbook","new_sheet","delete_sheet"],
        "DATA":          ["sort_ascending","sort_descending","open_sort_dialog","toggle_filter","remove_duplicates","text_to_columns","data_validation","refresh_all"],
        "INSERT OBJ":    ["insert_table","insert_pivot_table","insert_chart_embedded","insert_chart_new_sheet","insert_hyperlink","insert_comment","insert_function"],
        "PAGE LAYOUT":   ["page_orientation_portrait","page_orientation_landscape","set_print_area","show_gridlines"],
        "VIEW":          ["freeze_top_row","freeze_first_column","freeze_panes","unfreeze_panes","zoom_100"],
        "FORMULAS":      ["toggle_show_formulas","calculate_now","insert_function"],
        "REVIEW":        ["spell_check","protect_sheet","protect_workbook","add_comment"],
        "COMPOUND":      ["format_as_header","format_currency_borders","make_table_with_filter","sum_column","copy_format","select_visible_cells","group_rows","ungroup_rows"],
    }
    for cat, ids in categories.items():
        lines.append(f"\n[{cat}]")
        for aid in ids:
            entry = REGISTRY.get(aid)
            if not entry:
                continue
            params = ", ".join(entry["params"]) if entry["params"] else ""
            confirm = " ⚠" if entry["confirm"] else ""
            param_str = f"({params})" if params else ""
            lines.append(f"  {aid}{param_str} — {entry['desc']}{confirm}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(f"Total actions: {len(REGISTRY)}")
    print(build_action_menu_for_llm())
    print("\nTest: set_font_size(16)")
    for s in get_steps("set_font_size", size=16):
        print(" ", s)
