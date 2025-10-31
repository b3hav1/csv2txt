from csv import reader
from textwrap import wrap
from argparse import ArgumentParser

from os import getcwd
from os.path import basename, splitext, join

from enum import Enum
from dataclasses import dataclass
from typing import List, Iterable, Optional


class Align(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'


class VAlign(Enum):
    TOP = 'top'
    MIDDLE = 'middle'
    BOTTOM = 'bottom'


@dataclass
class CSV2TXT:
    '''
    Converts CSV to the text table with box-drawing borders.
    Supports both the CLI and the module.
    '''

    border_symbols: str = \
    '─ │ ┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘'                 # Appearance of the table botders. 

    spacing: int = 1                        # Spacing between the text and the border.
    separator: str = ','                    # Element separator for CSV.

    max_width: Optional[int] = None         # Maximum width per cell.
    align: Optional[List[Align]] = None     # Horizontal alignment (cols).

    valign: VAlign = VAlign.MIDDLE          # Vertical alignment.
    title_align: Align = Align.CENTER       # Horizontal alignment (title).


    def __post_init__(self):
        self.spacing = max(0, self.spacing)


    def escape(self, text: str) -> str:
        '''
        Returns the escaped text string.
        '''
        sep = self.separator

        return text\
            .replace(f'\\n', '\n')\
            .replace(f'\\{sep}', f'{sep}')
    

    def wrap_cell(self, text: str) -> List[str]:
        '''
        Wraps cell content respecting max width and line breaks.
        '''
        if text is None: return ['']

        text = self.escape(text)
        lines = text.splitlines()
        wrapped = []

        for line in lines or ['']:
            if self.max_width: wrapped.extend(wrap(line, self.max_width))
            else: wrapped.append(line)

        return wrapped or ['']


    def align_text(self, text: str, width: int, align: Align) -> str:
        '''
        Aligns text within a given width based on the alignment rule.
        '''
        match align:
            case Align.LEFT: return text.ljust(width)
            case Align.RIGHT: return text.rjust(width)
            case Align.CENTER: return text.center(width)


    def align_cell(self, text: str, width: int, column: int) -> str:
        '''
        Aligns text within a cell based on column settings.
        '''
        align = Align.LEFT

        if isinstance(self.align, list) and column < len(self.align): 
            align = self.align[column]

        return self.align_text(text, width, align)
    

    def get_rows(self, input: Iterable[str]) -> List[List[str]]:
        '''
        Parses raw CSV text data into a rows list.
        '''
        com = '__COMMA__'
        sep = self.separator

        lines = [line.replace(f'\\{sep}', com) for line in input]
        parser = reader(lines, delimiter = self.separator, skipinitialspace = True)

        return [[cell.replace(com, sep) for cell in row] for row in parser]
    

    def read(self, path: str, title: Optional[str] = None, output: Optional[str] = None) -> str:
        '''
        Reads CSV data from file, generates a text table, and optionally saves it.
        '''
        with open(path, 'r', encoding = 'utf-8', newline = '') as file:
            table = self.generate(file, title)
        
        if not output: return table

        if output == '.':
            base = splitext(basename(path))[0]
            output = join(getcwd(), f'{base}.txt')

        with open(output, 'w', encoding = 'utf-8') as file:
            file.write(table)

        return f'{table}\nSaved the text table to: {output}'
    

    def generate(self, input: Iterable[str], title: Optional[str] = None) -> str:
        '''
        Generates a complete text table from parsed CSV data with optional title.
        '''
        rows = self.get_rows(input)
        if not rows: return ''

        cells = [[self.wrap_cell(cell) for cell in row] for row in rows]
        cols = max(len(row) for row in rows)

        for row in cells:
            if len(row) < cols: row.extend([['']] * (cols - len(row)))

        cols_width = \
        [
            max(len(line) for row in cells for line in row[col]) 
            for col in range(cols)
        ]

        spaced_cols = [width + self.spacing * 2 for width in cols_width]
        total_width = sum(spaced_cols) + (len(spaced_cols) - 1)

        H, V, TL, TM, TR, ML, MM, MR, BL, BM, BR = self.border_symbols.split()


        def make_separator(left: str, center: str, right: str) -> str:
            '''
            Builds a horizontal separator line respecting to column width.
            '''
            return left + center.join(H * w for w in spaced_cols) + right
        

        top = make_separator(TL, TM, TR)
        middle = make_separator(ML, MM, MR)
        bottom = make_separator(BL, BM, BR)

        lines = []
        if not title: lines.append(top)

        else:
            title_text = f" {title} "
            title_text = self.align_text(title_text, total_width, self.title_align)

            lines.append(TL + H * total_width + TR)
            lines.append(V + title_text + V)
            lines.append(make_separator(ML, TM, MR))

        for ri, row in enumerate(cells):
            rows_height = [len(cell) for cell in row]
            max_height = max(rows_height)
            spaced_cells = []

            for col in row:
                delta = max_height - len(col)
                spaced = []

                if self.valign == VAlign.TOP:
                    spaced = col + [''] * delta

                elif self.valign == VAlign.BOTTOM:
                    spaced = [''] * delta + col

                else:
                    top_space = delta // 2
                    bottom_space = delta - top_space
                    spaced = [''] * top_space + col + [''] * bottom_space

                spaced_cells.append(spaced)

            for line in range(max_height):
                parts = []

                for ci, cell in enumerate(spaced_cells):
                    text = cell[line]
                    content = self.align_cell(text, cols_width[ci], ci)
                    parts.append(' ' * self.spacing + content + ' ' * self.spacing)

                lines.append(V + V.join(parts) + V)

            if ri < len(cells) - 1: lines.append(middle)

        lines.append(bottom)
        return '\n'.join(lines)
    

def main():
    '''
    Handles command-line arguments and runs CSV2TXT conversion process.
    '''
    parser = ArgumentParser(description = 'Converts CSV to the text table with box-drawing borders.')
    parser.add_argument('input',            help = 'path to CSV file')
    parser.add_argument('-n', '--name',     help = 'optional table title',              default = None)
    parser.add_argument('-s', '--space',    help = 'spacing between text',              default = 1,                type = int)
    parser.add_argument('-w', '--width',    help = 'maximum width per cell',            default = None,             type = int)
    parser.add_argument('-a', '--align',    help = 'horizontal alignment (cols)',       default = None,             nargs = '+')
    parser.add_argument('-t', '--talign',   help = 'horizontal alignment (title)',      default = Align.CENTER)
    parser.add_argument('-v', '--valign',   help = 'vertical alignment',                default = VAlign.MIDDLE)
    parser.add_argument('-o', '--output',   help = 'output file path',                  default = None)
    args = parser.parse_args()

    align = [Align(align) for align in args.align] if args.align else None

    app = CSV2TXT \
    (
        spacing = args.space,
        max_width = args.width,

        align = align,
        valign = args.valign,
        title_align = args.talign,
    )

    result = app.read(args.input, args.name, args.output)
    if result: print(result)


if __name__ == '__main__': main()