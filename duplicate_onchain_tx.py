from mod.BlockChain import BlockChain

# ブロックチェーンインスタンス
bc = BlockChain()

# チェーンの取得
chain = bc.get_chain()

# 最後のブロックのトランザクションを１つ送信（トランザクションを重複させる） 
last_block = chain['blocks'][-1]
res = bc.send_tx(last_block['txs'][0])
print(res.text)