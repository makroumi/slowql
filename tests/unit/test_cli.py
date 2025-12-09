import argparse
import io
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from slowql.cli import build_argparser, main, run, safe_path, sql_split_statements


class TestCLI:

    def test_sql_split_statements_empty(self):
        assert sql_split_statements("") == []
        assert sql_split_statements("   ") == []

    def test_sql_split_statements_single_statement(self):
        assert sql_split_statements("SELECT 1;") == ["SELECT 1"]
        assert sql_split_statements("SELECT 1") == ["SELECT 1"]

    def test_sql_split_statements_multiple_statements(self):
        sql = "SELECT 1; UPDATE users SET name = 'test';"
        expected = ["SELECT 1", "UPDATE users SET name = 'test'"]
        assert sql_split_statements(sql) == expected

    def test_sql_split_statements_with_quotes(self):
        sql = "SELECT 'hello; world'; SELECT \"another; one\";"
        expected = ["SELECT 'hello; world'", "SELECT \"another; one\""]
        assert sql_split_statements(sql) == expected

    def test_sql_split_statements_with_escaped_quotes(self):
        sql = r"SELECT 'it\'s a test'; INSERT INTO users VALUES ('semi;colon');"
        expected = [r"SELECT 'it\'s a test'", r"INSERT INTO users VALUES ('semi;colon')"]
        assert sql_split_statements(sql) == expected

    def test_sql_split_statements_with_comments(self):
        sql = "SELECT 1; -- comment\nUPDATE users;"
        expected = ["SELECT 1", "UPDATE users"]
        assert sql_split_statements(sql) == expected

    @patch("sys.exit")
    @patch("rich.console.Console.print")
    def test_safe_path_traversal_rejection(self, mock_print, mock_exit):
        malicious_path = Path("/foo/../bar")
        safe_path(malicious_path)
        mock_print.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("rich.console.Console.print")
    @patch("sys.exit")
    def test_run_input_file_empty(self, mock_exit, mock_print):
        mock_file = MagicMock()
        mock_file.read_text.return_value = "   "  # Empty content
        run(input_file=mock_file)
        mock_print.assert_called_once_with("[bold yellow]Input file is empty. Exiting.[/]")
        mock_exit.assert_not_called() # Should return, not exit

    @patch("rich.console.Console.print")
    @patch("sys.stdin.isatty", return_value=False)
    def test_run_non_interactive_no_input(self, mock_isatty, mock_print):
        run(non_interactive=True)
        mock_print.assert_called_once_with(
            "[bold yellow]Non-interactive mode: expecting input via --input-file or piped stdin[/]"
        )

    @patch("rich.console.Console.print")
    @patch("sys.stdin.isatty", return_value=True)
    @patch("slowql.effects.animations.CyberpunkSQLEditor.get_queries", return_value="")
    def test_run_interactive_no_sql_provided_compose(self, mock_get_queries, mock_isatty, mock_print):
        run(non_interactive=False, mode="compose")
        mock_print.assert_called_once_with("[bold yellow]No queries entered. Exiting.[/]")

    @patch("rich.console.Console.print")
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", side_effect=["", ""]) # Two blank lines for EOF
    def test_run_interactive_no_sql_provided_paste_mode(self, mock_input, mock_isatty, mock_print):
        run(non_interactive=False, mode="paste")
        mock_print.assert_called_once_with("[bold yellow]No SQL provided. Exiting.[/]")

    @patch("slowql.effects.animations.MatrixRain")
    @patch("slowql.effects.animations.AnimatedAnalyzer")
    @patch("rich.console.Console.print")
    def test_run_animated_analysis_intro_exception_handling(self, mock_print, mock_animated_analyzer, mock_matrix_rain):
        mock_matrix_rain_instance = MagicMock()
        mock_matrix_rain_instance.run.side_effect = Exception("Test exception")
        mock_matrix_rain.return_value = mock_matrix_rain_instance

        mock_animated_analyzer_instance = MagicMock()
        mock_animated_analyzer.return_value = mock_animated_analyzer_instance

        # We are testing exception handling in intro, so run should continue past it
        run(intro_enabled=True, fast=False, input_file=MagicMock(read_text=lambda: "SELECT 1"))

        mock_matrix_rain_instance.run.assert_called_once()
        # The important part is that the rest of the run function continues without crashing
        mock_animated_analyzer_instance.particle_loading.assert_called_once()
        mock_animated_analyzer_instance.glitch_transition.assert_called_once()

    def test_main_build_argparser(self):
        parser = build_argparser()
        args = parser.parse_args([])
        assert args.prog == "slowql"
        assert args.no_intro is False
        assert args.fast is False
        assert args.parallel is False
        assert args.workers is None
        assert args.input_file is None
        assert args.mode == "auto"
        assert args.export is None
        assert args.out == Path.cwd() / "reports"
        assert args.duration == 3.0
        assert args.verbose is False
        assert args.non_interactive is False
        assert args.help_art is False

    @patch("slowql.cli.run")
    @patch("slowql.cli.build_argparser")
    def test_main_calls_run(self, mock_build_argparser, mock_run):
        mock_parser = MagicMock()
        mock_args = MagicMock(
            no_intro=False,
            duration=3.0,
            mode="auto",
            input_file=None,
            export=[],
            out=Path.cwd() / "reports",
            fast=False,
            verbose=False,
            non_interactive=False,
            parallel=False,
            workers=None,
            help_art=False
        )
        mock_build_argparser.return_value.parse_args.return_value = mock_args

        main(argv=[])

        mock_run.assert_called_once_with(
            intro_enabled=True,
            intro_duration=3.0,
            mode="auto",
            input_file=None,
            export_formats=[],
            out_dir=Path.cwd() / "reports",
            fast=False,
            verbose=False,
            non_interactive=False,
            parallel=False,
            workers=None,
        )

    @patch("slowql.cli_help.show_animated_help")
    @patch("slowql.cli.build_argparser")
    def test_main_calls_help_art(self, mock_build_argparser, mock_show_animated_help):
        mock_parser = MagicMock()
        mock_args = MagicMock(
            no_intro=True, # Irrelevant for help_art
            duration=2.0,
            mode="auto",
            input_file=None,
            export=None,
            out=None,
            fast=True,
            verbose=False,
            non_interactive=True,
            parallel=False,
            workers=None,
            help_art=True
        )
        mock_build_argparser.return_value.parse_args.return_value = mock_args

        main(argv=["--help-art"])

        mock_show_animated_help.assert_called_once_with(
            fast=True,
            non_interactive=True,
            duration=2.0
        )
