from json import dump, load
from re import fullmatch

with open("blocks.json", "r+") as blocks:
    ids = list(map(lambda block_id: block_id if fullmatch(".+:.+", block_id) else "minecraft:" + block_id, load(blocks)["block"]))
    blocks.truncate(0)
    blocks.seek(0)
    dump(ids, blocks)
