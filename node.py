from mod.BlockChain import BlockChain
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from typing import List

# FastAPIインスタンス
app = FastAPI()

# ブロックチェーンインスタンス
bc = BlockChain()

# ノードの起動処理
bc.tx_pool  = bc.load_tx_pool() # トランザクションプールの読出し
bc.chain    = bc.load_chain()   # チェーンの読出し
bc.set_all_block_txs()          # 全ブロックのトランザクションリストの作成

# トランザクションデータの定義
class Tx(BaseModel):
    time:       float
    sender:     str
    to:         str
    coin:       int
    signature:  str

# ブロックデータの定義
class Block(BaseModel):
    time:           float
    previous_hash:  str
    nonce:          int
    txs:            List[Tx]

# チェーンデータの定義
class Chain(BaseModel):
    blocks: List[Block]

# トランザクションプールを返す
@app.get('/tx-pool')
def get_tx_pool():
    return bc.tx_pool

# トランザクションの受信
@app.post('/tx-pool')
#def receiv_tx(tx :Tx):
def receiv_tx(tx :Tx, broadcast :str = 'on'):    
    # データモデルインスタンスを辞書（dict）型に変換
    tx_dict = tx.model_dump()

    # トランザクションの検証
    if bc.validate_tx(tx_dict) and bc.validate_duplicate_tx(tx_dict):
        # 受信したトランザクションをトランザクションプールに追加
        bc.add_tx_pool(tx_dict)

        # （追加）トランザクションのブロードキャスト
        if (broadcast == 'on'):
            bc.broadcast_tx(tx_dict)

        # 成功のレスポンス
        return 'ok'
    else:
        # 失敗のレスポンス
        return 'error'

# チェーンを返す
@app.get('/chain')
def get_chain():
    return bc.chain

# チェーンの受信
@app.post('/chain')
#def receiv_chain(chain :Chain):
def receiv_chain(chain :Chain, broadcast :str = 'on'):
    # データモデルインスタンスを辞書（dict）型に変換
    chain_dict = chain.model_dump()

    # チェーンの検証
    if bc.validate_chain(chain_dict):
        # チェーンの入替え
        bc.replace_chain(chain_dict)

        # （追加）チェーンのブロードキャスト
        if (broadcast == 'on'):
            bc.broadcast_chain(chain_dict)

        # 成功のレスポンス
        return 'ok'
    else:
        # 失敗のレスポンス
        return 'error'

# 各アカウントの残高を返す
@app.get('/accounts')
def get_accounts():
    return bc.calc_accounts_balance(bc.all_block_txs)

# Webサーバー起動
if __name__ == '__main__':
    uvicorn.run('node:app', host='0.0.0.0', port=8000)