# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import logging

from pylsp import _utils, hookimpl, uris

log = logging.getLogger(__name__)


@hookimpl
def pylsp_rename(config, workspace, document, position, new_name):
    log.debug(
        "Executing rename of %s to %s", document.word_at_position(position), new_name
    )
    kwargs = _utils.position_to_jedi_linecolumn(document, position)
    kwargs["new_name"] = new_name
    try:
        refactoring = document.jedi_script().rename(**kwargs)
    except NotImplementedError as exc:
        raise Exception(
            "No support for renaming in Python 2/3.5 with Jedi. "
            "Consider using the pylsp-rope plugin instead"
        ) from exc
    log.debug("Finished rename: %s", refactoring.get_diff())
    changes = []

    changed_files = refactoring.get_changed_files()
    for file_path, changed_file in changed_files.items():
        uri = uris.from_fs_path(str(file_path))
        doc = workspace.get_maybe_document(uri)
        source = workspace.get_document(uri).source
        changes.append(
            {
                "textDocument": {"uri": uri, "version": doc.version if doc else None},
                "edits": [
                    {
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": _end_position(source),
                        },
                        "newText": changed_file.get_new_code(),
                    }
                ],
            }
        )
    return {"documentChanges": changes}


def _end_position(file_contents):
    lines = file_contents.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return {
        "line": len(lines) - 1,
        "character": len(lines[-1].encode("utf-16-le")) // 2,
    }
