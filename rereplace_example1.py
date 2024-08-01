import re

def rereplace(text, pattern, replace):
    return re.sub(pattern, replace, text)

def insertText(text, position, content):
    return text[:position] + content + text[position:]

def deleteLine(text, line_number):
    lines = text.split('\n')
    del lines[line_number - 1]
    return '\n'.join(lines)

def replaceWholeLine(text, line_number, new_line):
    lines = text.split('\n')
    lines[line_number - 1] = new_line
    return '\n'.join(lines)

def position_from_line(text, line_number):
    lines = text.split('\n')
    total_chars = 0
    for i in range(line_number - 1):
        total_chars += len(lines[i]) + 1  # Add 1 for the newline character
    return total_chars

tchanges = []
limsCool = []

with open('your_file.txt', 'r') as file:
    text = file.read()

# First replace comments
text = rereplace(text, r'[(](.*)[)]', lambda m: ';' + m.group(1))

# Refresh text for 2nd pass
text_2nd_pass = text

reoSco = r'G50.+S(.+)'

"""handle M8 and LIMS"""
get_lims_cool = re.finditer(reoSco, text_2nd_pass)
for l in get_lims_cool:
    match_start = l.start()
    line_number = sum(1 for line in text_2nd_pass[:match_start].split('\n'))
    limsCool.append(tuple((line_number, l.group(1))))

revLCool = limsCool[::-1]

for i, (lin1, lims1) in enumerate(revLCool):
    # Calculate position from line for insertion
    lnum = position_from_line(text, sum(len(line) for line in text[:lin1 + 4]))
    text = insertText(text, lnum, f'LIMS={lims1}\nM3=8\n')
    for a in range(4):  # delete 4 lines
        text = deleteLine(text, lin1 - 1)

# Refresh text for 3rd pass
text_3rd_pass = text

"""handle toolchange line"""
tool_changes_pattern = r'G(97|96|95|94) S(\d+) (X.+) (T[0-9]{2}[0-9]{2}).+M(\d+)'

get_tchLine = re.finditer(tool_changes_pattern, text_3rd_pass)
for m in get_tchLine:
    match_start = m.start()
    line_number = sum(1 for line in text_3rd_pass[:match_start].split('\n'))
    tchanges.append(tuple((line_number, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5))))

revTs = tchanges[::-1]

for i, (lin, gmode, spd, posxz, tno, mspin) in enumerate(revTs):
    mMode = 'MCTURNS1' if int(gmode) >= 96 else 'MCMILLS1'
    tPrep = f'\nTLPREP1("{revTs[i - 1][4]}")' if i > 0 else '\nTLPREP1'
    sMode = f'M1={mspin}' if int(gmode) >= 96 else f'M3={int(mspin) - 48}'
    text = replaceWholeLine(text, lin - 1, f'TLCH1("{tno}",0){tPrep}\n{mMode}\nG{gmode} S1={spd} {sMode}\nG0 {posxz}\n')

# put your replacements below,
# note: there will be several format changes to the original code present already
text = rereplace(text, '([XYZ])(\S+)', r'\1=\2')
text = rereplace(text, r'G50.+S(.+)\W\n.+\W\n.+\W\n.[M](.+)', r'LIMS=\1 \nM3=\2')
text = rereplace(text, '(G97 S1=50)', 'MCHOME')
text = rereplace(text, r'(G0 [XYZ]1=0 [XYZ]1=0 T.+M)', r'M')

with open('new_nc_code.txt', 'w') as file:
    file.write(text)
