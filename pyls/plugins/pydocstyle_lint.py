# Copyright 2017 Palantir Technologies, Inc.
import contextlib
import debug_tools
import sys

import pydocstyle
from pyls import hookimpl, lsp

log = debug_tools.getLogger(__name__)

# PyDocstyle is a little verbose in debug message
pydocstyle_logger = debug_tools.getLogger(pydocstyle.utils.__name__)
pydocstyle_logger.setLevel("INFO")


@hookimpl
def pyls_settings():
    # Default pydocstyle to disabled
    return {'plugins': {'pydocstyle': {'enabled': False}}}


@hookimpl
def pyls_lint(config, document):
    conf = pydocstyle.config.ConfigurationParser()
    settings = config.plugin_settings('pydocstyle')
    settings_codes = settings.get('select', []) + settings.get('ignore', [])

    with _patch_sys_argv([document.path]):
        # TODO(gatesn): We can add more pydocstyle args here from our pyls config
        conf.parse()

    # Will only yield a single filename, the document path
    diags = []
    for filename, checked_codes, ignore_decorators in conf.get_files_to_check():
        errors = pydocstyle.checker.ConventionChecker().check_source(
            document.source, filename, ignore_decorators=ignore_decorators
        )
        checked_codes = list(set(checked_codes) - set(settings_codes))
        log.debug( "checked_codes: %s", checked_codes )

        try:
            for error in errors:
                if error.code not in checked_codes:
                    continue
                diags.append(_parse_diagnostic(document, error))
        except pydocstyle.parser.ParseError:
            # In the case we cannot parse the Python file, just continue
            pass

    log.debug("Got pydocstyle errors: %s", diags)
    return diags


def _parse_diagnostic(document, error):
    lineno = error.definition.start - 1
    line = document.lines[0] if document.lines else ""

    start_character = len(line) - len(line.lstrip())
    end_character = len(line)

    return {
        'source': 'pydocstyle',
        'code': error.code,
        'message': error.message,
        'severity': lsp.DiagnosticSeverity.Warning,
        'range': {
            'start': {
                'line': lineno,
                'character': start_character
            },
            'end': {
                'line': lineno,
                'character': end_character
            }
        }
    }


@contextlib.contextmanager
def _patch_sys_argv(arguments):
    old_args = sys.argv

    # Preserve argv[0] since it's the executable
    sys.argv = old_args[0:1] + arguments

    try:
        yield
    finally:
        sys.argv = old_args
