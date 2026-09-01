from app.etl.operations.append_text import AppendTextOperation
from app.etl.operations.concatenate import ConcatenateOperation
from app.etl.operations.constant import ConstantOperation
from app.etl.operations.copy import CopyOperation
from app.etl.operations.date_format import DateFormatOperation
from app.etl.operations.date_standardize import DateStandardizeOperation
from app.etl.operations.duration_format import DurationFormatOperation
from app.etl.operations.duration_pair_merge import DurationPairMergeOperation
from app.etl.operations.multiply import MultiplyOperation
from app.etl.operations.replace import ReplaceOperation
from app.etl.operations.slice_text import SliceOperation
from app.etl.operations.text_case import LowercaseOperation, UppercaseOperation
from app.etl.operations.trim import TrimOperation


def test_copy_operation_returns_first_value():
    assert CopyOperation().execute(["hello"], options={}) == "hello"


def test_trim_operation_strips_whitespace():
    assert TrimOperation().execute(["  hi  "], options={}) == "hi"


def test_uppercase_and_lowercase():
    assert UppercaseOperation().execute(["abc"], options={}) == "ABC"
    assert LowercaseOperation().execute(["ABC"], options={}) == "abc"


def test_concatenate_joins_non_empty_values_with_separator():
    result = ConcatenateOperation().execute(["1 Main St", "", "Suite 5"], options={"separator": ", "})
    assert result == "1 Main St, Suite 5"


def test_concatenate_default_separator_is_space():
    assert ConcatenateOperation().execute(["Foo", "Bar"], options={}) == "Foo Bar"


def test_multiply_operation_computes_product():
    assert MultiplyOperation().execute([10, 3], options={}) == 30.0


def test_multiply_operation_with_no_sources_returns_none():
    assert MultiplyOperation().execute([], options={}) is None


def test_concatenate_with_formats_applies_duration_and_suffix_per_source():
    result = ConcatenateOperation().execute(
        ["12530", "4321"],
        options={
            "separator": ", ",
            "formats": [{"duration_format": True, "suffix": " FH"}, {"suffix": " FC"}],
        },
    )
    assert result == "12530:00 FH, 4321 FC"


def test_append_text_operation_wraps_value_with_prefix_and_suffix():
    result = AppendTextOperation().execute(["12530:00"], options={"suffix": " FH"})
    assert result == "12530:00 FH"


def test_append_text_operation_returns_none_for_missing_value():
    assert AppendTextOperation().execute([], options={"suffix": " FH"}) is None


def test_append_text_operation_joins_multiple_sources_with_separator():
    result = AppendTextOperation().execute(
        ["12530", "4321"], options={"separator": " / ", "prefix": "(", "suffix": ")"}
    )
    assert result == "(12530 / 4321)"


def test_append_text_operation_skips_blank_sources_when_joining():
    result = AppendTextOperation().execute(
        ["12530", None, ""], options={"separator": " / ", "suffix": " FH"}
    )
    assert result == "12530 FH"


def test_duration_format_appends_zero_minutes_for_whole_hours():
    assert DurationFormatOperation().execute(["12530"], options={}) == "12530:00"


def test_duration_format_converts_decimal_hours_to_minutes():
    assert DurationFormatOperation().execute([12530.5], options={}) == "12530:30"


def test_duration_format_leaves_already_formatted_value_untouched():
    assert DurationFormatOperation().execute(["12530:15"], options={}) == "12530:15"


def test_duration_pair_merge_matches_tsn_csn_example():
    result = DurationPairMergeOperation().execute([12530, 4321], options={})
    assert result == "12530:00 FH, 4321 FC"


def test_duration_pair_merge_uses_custom_suffixes_and_separator():
    result = DurationPairMergeOperation().execute(
        ["100:30", "50"],
        options={"separator": " | ", "first_suffix": " Hrs", "second_suffix": " Cyc"},
    )
    assert result == "100:30 Hrs | 50 Cyc"


def test_duration_pair_merge_skips_missing_values():
    assert DurationPairMergeOperation().execute([None, 4321], options={}) == "4321 FC"
    assert DurationPairMergeOperation().execute([12530], options={}) == "12530:00 FH"
    assert DurationPairMergeOperation().execute([], options={}) == ""


def test_slice_operation_positive_length_takes_from_start():
    assert SliceOperation().execute(["ABC12345"], options={"length": 3}) == "ABC"


def test_slice_operation_negative_length_takes_from_end():
    assert SliceOperation().execute(["ABC12345"], options={"length": -4}) == "2345"


def test_slice_operation_trims_whitespace_by_default_before_slicing():
    assert SliceOperation().execute(["  ABC12345  "], options={"length": 3}) == "ABC"
    assert SliceOperation().execute(["  ABC12345  "], options={"length": -3}) == "345"


def test_slice_operation_can_disable_trim():
    result = SliceOperation().execute(["  ABC  "], options={"length": 3, "trim": False})
    assert result == "  A"


def test_slice_operation_without_length_returns_trimmed_value():
    assert SliceOperation().execute(["  hello  "], options={}) == "hello"


def test_slice_operation_returns_none_for_missing_value():
    assert SliceOperation().execute([], options={"length": 3}) is None


def test_slice_operation_retain_false_drops_from_start():
    result = SliceOperation().execute(["ABC12345"], options={"length": 4, "retain": False})
    assert result == "2345"


def test_slice_operation_retain_false_drops_from_end():
    result = SliceOperation().execute(["ABC12345"], options={"length": -4, "retain": False})
    assert result == "ABC1"


def test_slice_operation_retain_true_matches_default_keep_behavior():
    assert SliceOperation().execute(["ABC12345"], options={"length": 4, "retain": True}) == "ABC1"
    assert SliceOperation().execute(["ABC12345"], options={"length": -4, "retain": True}) == "2345"

def test_replace_operation_substitutes_text():
    result = ReplaceOperation().execute(["hello world"], options={"find": "world", "replace": "there"})
    assert result == "hello there"


def test_date_format_operation_formats_iso_string():
    result = DateFormatOperation().execute(["2026-01-05T00:00:00"], options={"format": "%d/%m/%Y"})
    assert result == "05/01/2026"


def test_date_standardize_handles_day_first_format():
    assert DateStandardizeOperation().execute(["13/04/2005"], options={}) == "13-Apr-2005"


def test_date_standardize_handles_year_first_format():
    assert DateStandardizeOperation().execute(["2005-04-13"], options={}) == "13-Apr-2005"


def test_date_standardize_handles_us_month_first_format():
    # Unambiguous only because 13 can't be a month; falls through to %m/%d/%Y.
    assert DateStandardizeOperation().execute(["04/13/2005"], options={}) == "13-Apr-2005"


def test_date_standardize_handles_datetime_object():
    from datetime import datetime

    value = datetime(2005, 4, 13)  # noqa: DTZ001
    assert DateStandardizeOperation().execute([value], options={}) == "13-Apr-2005"


def test_date_standardize_leaves_unparseable_value_unchanged():
    assert DateStandardizeOperation().execute(["not a date"], options={}) == "not a date"


def test_date_standardize_returns_none_for_missing_value():
    assert DateStandardizeOperation().execute([], options={}) is None


def test_constant_operation_returns_configured_value():
    assert ConstantOperation().execute([], options={"value": "N/A"}) == "N/A"
