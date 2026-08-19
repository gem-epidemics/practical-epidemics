#!/usr/bin/env python3
"""
myst_exercise_to_colab.py

Convert MyST directives from sphinx-exercise, sphinx_code_examples
("codex"), sphinx-proof, and sphinx-design inside Jupyter notebook markdown
cells into Colab-friendly Markdown/HTML, so notebooks authored for
Jupyter Book / MyST-NB render sensibly when opened directly in Google Colab
(which has no MyST parser and just shows raw ```{directive} ...``` text).

=========================
sphinx-exercise
=========================
Handles both usage patterns:

1. Inline, single-cell:
    ```{exercise}
    :label: ex1
    Compute the mean of ...
    ```
    ```{solution} ex1
    :label: sol1
    The mean is ...
    ```

2. Multi-cell "start/end" (exercise or solution spans several cells,
   including code cells):
    ```{solution-start} ex1
    :label: sol1
    ```
    ...any number of markdown/code cells...
    ```{solution-end}
    ```

OUTPUT:
- Single-cell exercises  -> "#### Exercise N" heading + blockquoted body.
- Single-cell solutions  -> real <details><summary>Solution</summary>
  collapse (closed by default, since <details> has no "open" attribute).
- Multi-cell exercise spans -> start/end marker cells become headings.
- Multi-cell solution spans -> the start marker cell is also a heading, and
  its cell id is added to metadata.colab.collapsed_sections, so Colab
  starts that section folded on load. Exercises stay expanded; only
  solutions fold. (Colab can only auto-collapse a section that begins
  with a heading cell - a literal <details> tag can't open in one cell
  and close in another, since Colab sanitizes each markdown cell's HTML
  independently.)

=========================
sphinx_code_examples ("codex")
=========================
```{codex}
:label: example-codex
This is an example. Not code, no solution pairing.
```
```{codex-start}
:label: example-code
```
...cells with executable code...
```{codex-end}
```
-> rendered the same way as exercises (heading, numbered "Code Example N"),
since codex has no paired "solution" concept.

=========================
sphinx-proof
=========================
All `{prf:<type>}` directives (theorem, lemma, corollary, definition,
remark, conjecture, axiom, criterion, algorithm, example, property,
observation, proposition, assumption, notation) ->
"#### <Type> N[: title]" heading + blockquoted body, numbered per type
(Theorem 1, Theorem 2, ... Lemma 1, ...).

If `:class: dropdown` is set (sphinx-proof's own convention, via
sphinx-togglebutton, for hiding content) -> rendered as a collapsed
<details> instead of a heading.

`{prf:proof}` has no :label: support in sphinx-proof itself, and is
always rendered as a collapsed <details><summary>Proof</summary>, since a
proof is conventionally the "reveal this to check your work" part.

Assumed single-cell only: sphinx-proof does not document a multi-cell
start/end pattern the way sphinx-exercise does, so no such support here.

=========================
sphinx-design
=========================
- `{dropdown} Title`            -> <details><summary>Title</summary>...
- `{card} Title` / `{grid-item-card}` -> a blockquoted block with a bold
  title; sphinx-design's `^^^` (header) and `+++` (footer) section
  separators inside a card are respected if present.
- `{grid}`, `{grid-item}`, `{tab-set}` -> these are pure responsive-layout
  containers with no Colab equivalent (no columns, no real tabs in a
  markdown cell), so they are flattened: the wrapper is dropped and their
  content is processed in place, in document order.
- `{tab-item} Title`            -> rendered as "**Tab: Title**" followed by
  its content, still in linear document order (not an actual clickable
  tab - Colab markdown has no tab widget).
- `{button-link} <url>`         -> a plain Markdown link `[text](url)`.
- `{button-ref} <target>`       -> bold text noting the link target, since
  cross-reference targets can't be resolved outside a full Sphinx build.

Assumed single-cell only, same reasoning as sphinx-proof above.

KNOWN LIMITATIONS (see inline notes above for specifics):
- Assumes the MyST convention that an outer directive's fence is longer
  than any fenced code sample nested directly inside it.
- Directive options other than :label:/:class: are parsed but not
  rendered.
- sphinx-design layout (grid columns, real tabs) cannot be reproduced in
  a linear Colab notebook; content is preserved, layout is not.
- {exercise-end}/{solution-end}/{codex-end} close the most recently
  opened span of the same kind (a stack), not by label, matching how
  sphinx-exercise itself resolves them.

USAGE:
    python myst_exercise_to_colab.py notebook.ipynb
    python myst_exercise_to_colab.py notebook.ipynb -o notebook.colab.ipynb
"""

import argparse
import copy
import json
import random
import re
import string
import sys
from pathlib import Path

FENCE_RE = re.compile(
    r'^(?P<indent>\s*)(?P<fence>`{3,}|:{3,})\{(?P<directive>[\w:-]+)\}\s*(?P<arg>.*)$'
)

OPTION_RE = re.compile(r'^\s*:([\w-]+):\s*(.*)$')

MULTI_CELL_DIRECTIVES = {
    'exercise-start': 'exercise', 'exercise-end': 'exercise',
    'solution-start': 'solution', 'solution-end': 'solution',
    'codex-start': 'codex', 'codex-end': 'codex',
}
INLINE_SIMPLE_DIRECTIVES = {'exercise', 'solution', 'codex'}
SD_CONTAINER_DIRECTIVES = {'grid', 'grid-item', 'tab-set'}
SD_LEAF_DIRECTIVES = {
    'dropdown', 'card', 'grid-item-card', 'tab-item',
    'button-link', 'button-ref',
}


def is_directive_of_interest(name):
    return (
        name in MULTI_CELL_DIRECTIVES
        or name in INLINE_SIMPLE_DIRECTIVES
        or name.startswith('prf:')
        or name in SD_CONTAINER_DIRECTIVES
        or name in SD_LEAF_DIRECTIVES
    )


def gen_cell_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


def ensure_cell_id(cell):
    """Return the cell's id, generating and attaching one if it lacks one.
    Colab's collapsed_sections metadata refers to cells by id."""
    cid = cell.get('id')
    if not cid:
        cid = gen_cell_id()
        cell['id'] = cid
    return cid


def get_source(cell):
    src = cell.get('source', '')
    if isinstance(src, list):
        return ''.join(src)
    return src


def set_source(cell, text):
    lines = text.splitlines(keepends=True)
    if not lines:
        lines = ['']
    cell['source'] = lines


def parse_options(lines):
    """Parse leading `:key: value` option lines from directive content."""
    options = {}
    idx = 0
    for line in lines:
        m = OPTION_RE.match(line)
        if m:
            options[m.group(1)] = m.group(2).strip()
            idx += 1
        elif line.strip() == '':
            idx += 1
        else:
            break
    return options, lines[idx:]


def find_directive_blocks(text):
    """
    Find top-level MyST fenced directive blocks of interest in a markdown
    string. Returns a list of dicts: {directive, arg, options, content,
    start_line, end_line} where start_line/end_line are line indices
    (inclusive) of the whole matched block, including its fences.
    """
    lines = text.splitlines(keepends=True)
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        m = FENCE_RE.match(lines[i].rstrip('\n'))
        if m and is_directive_of_interest(m.group('directive')):
            fence_char = m.group('fence')[0]
            fence_len = len(m.group('fence'))
            close_re = re.compile(
                r'^\s*' + re.escape(fence_char) + '{' + str(fence_len) + ',}\\s*$'
            )
            j = i + 1
            body = []
            while j < n and not close_re.match(lines[j].rstrip('\n')):
                body.append(lines[j])
                j += 1
            if j < n:  # found a matching closing fence
                options, content_lines = parse_options(body)
                blocks.append({
                    'directive': m.group('directive'),
                    'arg': m.group('arg').strip(),
                    'options': options,
                    'content': ''.join(content_lines),
                    'start_line': i,
                    'end_line': j,
                })
                i = j + 1
                continue
        i += 1
    return blocks


def is_pure_marker_cell(text):
    """
    Returns the single directive block if this markdown cell contains
    *nothing but* one multi-cell start/end fence (the pattern
    sphinx-exercise/sphinx_code_examples expect for spans in notebooks),
    else None.
    """
    blocks = find_directive_blocks(text)
    if len(blocks) != 1:
        return None
    b = blocks[0]
    if b['directive'] not in MULTI_CELL_DIRECTIVES:
        return None
    lines = text.splitlines(keepends=True)
    before = ''.join(lines[:b['start_line']]).strip()
    after = ''.join(lines[b['end_line'] + 1:]).strip()
    return b if before == '' and after == '' else None


def blockquote(body):
    return '\n'.join(('> ' + l if l else '>') for l in body.split('\n'))


def render_inline_exercise(block, number):
    title = f"Exercise {number}" if number else "Exercise"
    body = block['content'].strip('\n')
    return f"#### {title}\n\n{blockquote(body)}\n"


def render_inline_solution(block, ex_number):
    summary = f"Solution to Exercise {ex_number}" if ex_number else "Solution"
    body = block['content'].strip('\n')
    return f"<details>\n<summary>{summary}</summary>\n\n{body}\n\n</details>\n"


def render_codex(block, number):
    title = f"Code Example {number}" if number else "Code Example"
    body = block['content'].strip('\n')
    return f"#### {title}\n\n{blockquote(body)}\n"


def render_start_marker(base, number):
    if base == 'exercise':
        title = f"Exercise {number}" if number else "Exercise"
        return f"#### {title}\n"
    if base == 'codex':
        title = f"Code Example {number}" if number else "Code Example"
        return f"#### {title}\n"
    title = f"Solution to Exercise {number}" if number else "Solution"
    return f"#### {title} (collapsed by default - click to expand)\n"


def render_end_marker(base):
    word = {'exercise': 'exercise', 'codex': 'code example', 'solution': 'solution'}.get(base, base)
    return f"---\n_end of {word}_\n"


def render_prf_proof(block):
    body = block['content'].strip('\n')
    return f"<details>\n<summary>Proof</summary>\n\n{body}\n\n</details>\n"


def render_prf_statement(block, number, typ):
    word = typ.capitalize()
    title_arg = block['arg']
    is_dropdown = 'dropdown' in block['options'].get('class', '')
    label_text = f"{word} {number}" + (f": {title_arg}" if title_arg else "")
    body = block['content'].strip('\n')
    if is_dropdown:
        return f"<details>\n<summary>{label_text}</summary>\n\n{body}\n\n</details>\n"
    return f"#### {label_text}\n\n{blockquote(body)}\n"


def render_sd_dropdown(block):
    title = block['arg'] or 'Details'
    body = block['content'].strip('\n')
    return f"<details>\n<summary>{title}</summary>\n\n{body}\n\n</details>\n"


def split_card_sections(content):
    """Split a sphinx-design card's content on its ^^^ (header) and
    +++ (footer) separator lines. If no separators are present, the
    whole content is treated as the body."""
    lines = content.split('\n')
    sep_hdr = re.compile(r'^\^\^\^\s*$')
    sep_ftr = re.compile(r'^\+\+\+\s*$')
    header, body, footer = [], [], []
    state = 'header' if any(sep_hdr.match(l) for l in lines) else 'body'
    for l in lines:
        if sep_hdr.match(l):
            state = 'body'
            continue
        if sep_ftr.match(l):
            state = 'footer'
            continue
        (header if state == 'header' else body if state == 'body' else footer).append(l)
    return '\n'.join(header).strip('\n'), '\n'.join(body).strip('\n'), '\n'.join(footer).strip('\n')


def render_sd_card(block, convert_inline_directives):
    title = block['arg']
    header, body, footer = split_card_sections(block['content'])
    parts = []
    if title:
        parts.append(f"**{title}**")
    if header:
        parts.append(convert_inline_directives(header))
    if body:
        parts.append(convert_inline_directives(body))
    if footer:
        parts.append(f"_{convert_inline_directives(footer)}_")
    text = '\n\n'.join(p for p in parts if p)
    return f"{blockquote(text)}\n"


def render_sd_tab_item(block, convert_inline_directives):
    title = block['arg'] or 'Tab'
    body = convert_inline_directives(block['content']).strip('\n')
    return f"**Tab: {title}**\n\n{body}\n"


def render_sd_button_link(block):
    url = block['arg'].strip()
    text = block['content'].strip() or url
    return f"[{text}]({url})\n"


def render_sd_button_ref(block):
    target = block['arg'].strip()
    text = block['content'].strip() or target
    return (
        f"**{text}** _(originally linked to `{target}` - cross-reference "
        "targets can't be resolved outside a Sphinx build)_\n"
    )


def convert_notebook(nb):
    nb = copy.deepcopy(nb)
    cells = nb.get('cells', [])

    exercise_counter = 0
    codex_counter = 0
    label_to_number = {}
    prf_counters = {}
    open_spans = []  # stack of {'directive_base', 'number'}
    collapsed_cell_ids = []  # solution-start cells: collapsed-by-default in Colab
    warnings = []

    def render_and_dispatch(block):
        nonlocal exercise_counter, codex_counter

        directive = block['directive']

        # Multi-cell marker directives mixed inline with other content
        # can't safely become a proper section - fall back to a marker.
        if directive in MULTI_CELL_DIRECTIVES:
            warnings.append(
                f"'{{{directive}}}' was mixed with other content in one "
                "cell; converted to a plain text marker instead of a "
                "proper section."
            )
            return f"_{directive}_\n"

        if directive == 'exercise':
            exercise_counter += 1
            label = block['options'].get('label', '')
            if label:
                label_to_number[label] = exercise_counter
            return render_inline_exercise(block, exercise_counter)

        if directive == 'solution':
            ref = block['arg'] or block['options'].get('label', '')
            ex_number = label_to_number.get(ref)
            return render_inline_solution(block, ex_number)

        if directive == 'codex':
            codex_counter += 1
            return render_codex(block, codex_counter)

        if directive.startswith('prf:'):
            typ = directive.split(':', 1)[1]
            if typ == 'proof':
                return render_prf_proof(block)
            prf_counters[typ] = prf_counters.get(typ, 0) + 1
            return render_prf_statement(block, prf_counters[typ], typ)

        if directive == 'dropdown':
            return render_sd_dropdown(block)

        if directive in ('card', 'grid-item-card'):
            return render_sd_card(block, convert_inline_directives)

        if directive in ('grid', 'grid-item', 'tab-set'):
            return convert_inline_directives(block['content']).strip('\n') + '\n'

        if directive == 'tab-item':
            return render_sd_tab_item(block, convert_inline_directives)

        if directive == 'button-link':
            return render_sd_button_link(block)

        if directive == 'button-ref':
            return render_sd_button_ref(block)

        # Shouldn't happen given is_directive_of_interest(), but fall
        # back safely rather than silently dropping content.
        warnings.append(f"Unhandled directive '{{{directive}}}' left as plain content.")
        return block['content']

    def convert_inline_directives(text):
        blocks = find_directive_blocks(text)
        if not blocks:
            return text
        lines = text.splitlines(keepends=True)
        out = []
        cursor = 0
        for b in blocks:
            out.append(''.join(lines[cursor:b['start_line']]))
            rendered = render_and_dispatch(b)
            if not rendered.endswith('\n\n'):
                rendered = rendered.rstrip('\n') + '\n\n'
            out.append(rendered)
            cursor = b['end_line'] + 1
        out.append(''.join(lines[cursor:]))
        return ''.join(out)

    for cell in cells:
        if cell.get('cell_type') != 'markdown':
            continue
        text = get_source(cell)
        if '{' not in text:
            continue

        marker = is_pure_marker_cell(text)
        if marker is not None:
            directive = marker['directive']
            base = MULTI_CELL_DIRECTIVES[directive]
            if directive.endswith('-start'):
                number = None
                if base == 'exercise':
                    exercise_counter += 1
                    number = exercise_counter
                    label = marker['options'].get('label', marker['arg'])
                    if label:
                        label_to_number[label] = number
                elif base == 'codex':
                    codex_counter += 1
                    number = codex_counter
                else:  # solution
                    ref = marker['arg'] or marker['options'].get('label', '')
                    number = label_to_number.get(ref)
                open_spans.append({'directive_base': base, 'number': number})
                new_text = render_start_marker(base, number)
                if base == 'solution':
                    cid = ensure_cell_id(cell)
                    collapsed_cell_ids.append(cid)
            else:  # -end
                if open_spans:
                    span = open_spans.pop()
                    new_text = render_end_marker(span['directive_base'])
                else:
                    warnings.append(
                        f"Found a '{{{directive}}}' with no matching start; "
                        "left as a plain divider."
                    )
                    new_text = render_end_marker(base)
            set_source(cell, new_text)
            continue

        new_text = convert_inline_directives(text)
        if new_text != text:
            set_source(cell, new_text)

    if open_spans:
        warnings.append(
            f"{len(open_spans)} start directive(s) were never closed with a "
            "matching end."
        )

    if collapsed_cell_ids:
        # Cell ids require nbformat >= 4.5.
        if nb.get('nbformat', 4) < 4 or (
            nb.get('nbformat', 4) == 4 and nb.get('nbformat_minor', 0) < 5
        ):
            nb['nbformat_minor'] = 5
        colab_meta = nb.setdefault('metadata', {}).setdefault('colab', {})
        existing = colab_meta.setdefault('collapsed_sections', [])
        for cid in collapsed_cell_ids:
            if cid not in existing:
                existing.append(cid)

    return nb, warnings


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('notebook', type=Path, help='Path to input .ipynb file')
    parser.add_argument(
        '-o', '--output', type=Path, default=None,
        help='Output path (default: <name>.colab.ipynb)'
    )
    args = parser.parse_args()

    nb = json.loads(args.notebook.read_text(encoding='utf-8'))
    new_nb, warnings = convert_notebook(nb)

    out_path = args.output or args.notebook.with_suffix('.colab.ipynb')
    out_path.write_text(json.dumps(new_nb, indent=1, ensure_ascii=False), encoding='utf-8')

    print(f"Wrote {out_path}")
    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)


if __name__ == '__main__':
    main()
