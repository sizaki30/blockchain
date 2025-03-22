from mod.BlockChain import BlockChain

# ブロックチェーンインスタンス
bc = BlockChain()

# トランザクションプールを取得
tx_pool = bc.get_tx_pool()

#　先頭のトランザクションを送信（トランザクションを重複させる） 
res = bc.send_tx(tx_pool['txs'][0])
print(res.text)