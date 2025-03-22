from mod.BlockChain import BlockChain
from mod.users import users
import time

# ブロックチェーンインスタンス
bc = BlockChain()

# トランザクションの作成
tx = {
    'time':     time.time(),
    'sender':   users['A']['public_key'],
    'to':       users['B']['public_key'],
    'coin':     3
}

# トランザクション署名の追加
tx['signature'] = bc.gen_signature(tx, users['A']['private_key'])

# 送信
res = bc.send_tx(tx)
print(res.text)