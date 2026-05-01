import struct
import os

def compile_po_to_mo(po_path, mo_path):
    messages = []
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    with open(po_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                if current_msgid is not None and current_msgstr is not None:
                    messages.append((current_msgid, current_msgstr))
                current_msgid = None
                current_msgstr = None
                in_msgid = False
                in_msgstr = False
                continue
            if line.startswith('msgid '):
                if current_msgid is not None and current_msgstr is not None:
                    messages.append((current_msgid, current_msgstr))
                current_msgid = line[6:].strip('"')
                current_msgstr = None
                in_msgid = True
                in_msgstr = False
            elif line.startswith('msgstr '):
                current_msgstr = line[7:].strip('"')
                in_msgid = False
                in_msgstr = True
            elif line.startswith('"') and line.endswith('"'):
                s = line.strip('"')
                if in_msgid:
                    current_msgid += s
                elif in_msgstr:
                    current_msgstr += s
    if current_msgid is not None and current_msgstr is not None:
        messages.append((current_msgid, current_msgstr))

    metadata = 'Content-Type: text/plain; charset=UTF-8\nContent-Transfer-Encoding: 8bit\n'
    final_messages = [('', metadata)]
    for msgid, msgstr in messages:
        if msgid and msgstr:
            msgid = msgid.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            msgstr = msgstr.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            final_messages.append((msgid, msgstr))

    final_messages.sort(key=lambda x: x[0])

    keys = []
    values = []
    for msgid, msgstr in final_messages:
        keys.append(msgid.encode('utf-8'))
        values.append(msgstr.encode('utf-8'))

    header_size = 7 * 4
    table_size = len(keys) * 8
    ids_offset = header_size
    strs_offset = header_size + table_size
    data_start = header_size + table_size * 2

    key_offsets = []
    pos = data_start
    for k in keys:
        key_offsets.append((len(k), pos))
        pos += len(k) + 1

    val_offsets = []
    for v in values:
        val_offsets.append((len(v), pos))
        pos += len(v) + 1

    output = []
    output.append(struct.pack('I', 0x950412de))
    output.append(struct.pack('I', 0))
    output.append(struct.pack('I', len(keys)))
    output.append(struct.pack('I', ids_offset))
    output.append(struct.pack('I', strs_offset))
    output.append(struct.pack('I', 0))
    output.append(struct.pack('I', 0))

    for length, offset in key_offsets:
        output.append(struct.pack('II', length, offset))
    for length, offset in val_offsets:
        output.append(struct.pack('II', length, offset))
    for k in keys:
        output.append(k + b'\x00')
    for v in values:
        output.append(v + b'\x00')

    with open(mo_path, 'wb') as f:
        f.write(b''.join(output))

    print(f'Compiled {len(final_messages)} messages to {mo_path}')


if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    po = os.path.join(base, 'locale', 'en', 'LC_MESSAGES', 'django.po')
    mo = os.path.join(base, 'locale', 'en', 'LC_MESSAGES', 'django.mo')
    compile_po_to_mo(po, mo)
