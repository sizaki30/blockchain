from mod.BlockChain import BlockChain
from mod.users import users
import time
import sys

# ブロックチェーンインスタンス
bc = BlockChain()

# チェーンの取得
chain = bc.get_chain()

# チェーンを検証
bc.chain['blocks'] = [] # インスタンス内のチェーンを空にする
if not bc.validate_chain(chain):
    sys.exit('取得したチェーンが不正なため処理を終了しました')

# 最後のブロックのハッシュ値を生成
last_block      = chain['blocks'][-1]
last_block_hash = bc.gen_hash(last_block)

# ブロックに含めるトランザクション
tx_pool     = bc.get_tx_pool()
target_txs  = tx_pool['txs']

# 全ブロックのトランザクションリストを作成（残高チェック用）
bc.chain = chain
bc.set_all_block_txs()
all_block_txs = bc.all_block_txs.copy()

# 残高がマイナスになるトランザクションは除外する
for tx in target_txs.copy():
    all_block_txs.append(tx)
    if min(bc.calc_accounts_balance(all_block_txs).values()) < 0:
        target_txs.remove(tx)
        all_block_txs.remove(tx)

# マイナーの公開鍵
miner_public_key = users['C']['public_key']

# 報酬用トランザクションを作成
reward_tx = bc.make_reward_tx(miner_public_key)

# ブロックに含めるトランザクションに報酬用トランザクションを追加
target_txs.append(reward_tx)

# ナンスの初期値
nonce = 0

# マイニング処理
mining_start_time = time.time()
while True:
    # 新しいブロックを作成
    new_block = {
        'time':             time.time(),
        'previous_hash':    last_block_hash,
        'nonce':            nonce,
        'txs':              target_txs,
    }

    # 新しいブロックのハッシュ値を生成
    new_block_hash = bc.gen_hash(new_block)

    # ナンスの検証
    if bc.validate_nonce(new_block_hash):
        # マイニングが成功したらナンスとハッシュ値とマイニング時間を表示してマイニング処理を終了する
        print('mining success.')
        print('nonce: ' + str(nonce))
        print('hash: ' + new_block_hash)
        print('mining time: ' + str(time.time() - mining_start_time) + ' second')
        break
    else:
        # マイニングが失敗している場合はナンスを増やして再度マイニング処理を実行
        nonce += 1

# チェーンに新しいブロックを追加
chain['blocks'].append(new_block)

# ノードにチェーンを送信
res = bc.send_chain(chain)
print(res.text)