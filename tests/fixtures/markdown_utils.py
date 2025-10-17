import re

def extract_code_blocks(markdown_file, language="python"):
    with open(markdown_file, "r") as f:
        content = f.read()
    # Look for code blocks with the specified language
    code_blocks = re.findall(rf"```({language})\n(.*?)\n```", content, re.DOTALL)
    # re.findall returns a list of tuples (language, code_block), we only need the code_block
    return [block for lang, block in code_blocks if lang == language]
