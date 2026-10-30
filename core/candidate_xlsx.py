# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Bounded candidate-table OOXML output; exact address counts are text, never formulas."""
from io import BytesIO
from xml.sax.saxutils import escape, quoteattr
import zipfile


XMLNS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def candidate_workbook(headers, rows, sheet_name):
    """Build one sheet for at most 5,000 validated candidates, with filter and frozen header."""
    rows = tuple(rows)
    if not rows or len(rows) > 5000 or len(headers) != 9 or any(len(row) != 9 for row in rows):
        raise ValueError('Invalid candidate worksheet dimensions')
    output = BytesIO()
    columns = ''.join(f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>'
                      for i, width in enumerate((14, 14, 42, 42, 22, 44, 44, 28, 24), 1))
    sheet = [f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{XMLNS}">',
             '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
             '<cols>'+columns+'</cols><sheetData>']
    for number, row in enumerate((headers, *rows), 1):
        sheet.append(f'<row r="{number}" ht="{44 if number == 1 else 30}" customHeight="1">')
        for index, value in enumerate(row):
            address = f'{chr(65+index)}{number}'
            # Only bounded original index, physical line and overlap count are numeric.
            # Every address count stays inline text, even when small, to preserve the whole column.
            if number > 1 and index in (0, 1, 7):
                if type(value) is not int or not 0 <= value <= 20000:
                    raise ValueError('Invalid candidate numeric cell')
                sheet.append(f'<c r="{address}" s="2"><v>{value}</v></c>')
            else:
                sheet.append(f'<c r="{address}" s="{1 if number == 1 else 2}" t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>')
        sheet.append('</row>')
    sheet.append(f'</sheetData><autoFilter ref="A1:I{len(rows)+1}"/></worksheet>')
    styles = f'''<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="{XMLNS}">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF1769AA"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf></cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        archive.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        archive.writestr('xl/workbook.xml', f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{XMLNS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name={quoteattr(sheet_name)} sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        archive.writestr('xl/styles.xml', styles)
        archive.writestr('xl/worksheets/sheet1.xml', ''.join(sheet))
    return output.getvalue()
