from typing import Any
from unittest import TestCase, mock

from bme280pi.raspberry_pi_version import (
    detect_raspberry_pi_version,
    get_list_of_revisions,
    normalize_revision,
)


def raise_exception(*args: Any, **kwargs: Any) -> None:
    raise FileNotFoundError


class TestDetectRaspberryPiVersion(TestCase):
    def test(self) -> None:
        known_revisions = get_list_of_revisions()

        known_revisions["bad_id"] = "Unknown"

        for revision in known_revisions:
            mopen = mock.mock_open(read_data="\nRevision:" + revision + "\n")
            with mock.patch("builtins.open", mopen):
                self.assertEqual(
                    detect_raspberry_pi_version(), known_revisions[revision]
                )

    def test_exception(self) -> None:
        mopen = raise_exception
        with mock.patch("builtins.open", mopen):
            with self.assertWarns(Warning):
                self.assertEqual(detect_raspberry_pi_version(), "Unknown")

    def test_cpuinfo_is_closed(self) -> None:
        mopen = mock.mock_open(read_data="Revision\t: 0002\n")
        with mock.patch("builtins.open", mopen):
            detect_raspberry_pi_version()
        mopen.return_value.__exit__.assert_called_once()

    def test_overvoltage_flag_is_ignored(self) -> None:
        # boards with a blown over-voltage fuse report an extra flag bit
        for revision, model in [
            ("1000002", "Model B R1"),
            ("1000003", "Model B R1"),
            ("1000010", "Model B+"),
        ]:
            mopen = mock.mock_open(read_data="Revision\t: " + revision + "\n")
            with mock.patch("builtins.open", mopen):
                self.assertEqual(detect_raspberry_pi_version(), model)

    def test_upper_case_revision(self) -> None:
        mopen = mock.mock_open(read_data="Revision\t: A01041\n")
        with mock.patch("builtins.open", mopen):
            self.assertEqual(detect_raspberry_pi_version(), "Pi 2 Model B")


class TestNormalizeRevision(TestCase):
    def test_old_style(self) -> None:
        self.assertEqual(normalize_revision("0002"), "0002")
        self.assertEqual(normalize_revision("000D"), "000d")
        self.assertEqual(normalize_revision("1000002"), "0002")
        self.assertEqual(normalize_revision("2000010"), "0010")

    def test_new_style_is_unchanged(self) -> None:
        for revision in ["a01041", "900092", "c03111", "abcdef"]:
            self.assertEqual(normalize_revision(revision), revision)

    def test_unparsable_is_unchanged(self) -> None:
        self.assertEqual(normalize_revision("bad_id"), "bad_id")
        self.assertEqual(normalize_revision(""), "")
