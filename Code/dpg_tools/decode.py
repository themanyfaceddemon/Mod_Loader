import sys


def decode_string(instr: str):
    if not sys.platform == "win32":
        return instr

    translation_table = str.maketrans(
        {chr(i): chr(i + 0x350) for i in range(0x00C0, 0x100)}
    )

    translation_table.update({0x00B8: chr(0x0451), 0x00A8: chr(0x0401)})

    return instr.translate(translation_table)
