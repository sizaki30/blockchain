import random
from ecdsa import SECP256k1, SigningKey, VerifyingKey, BadSignatureError
import binascii
import json
import requests
import pandas as pd
import os
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor

# ブロックチェーンのコア機能を実装するためのクラス
class BlockChain:
    def __init__(self):
        # ノードのIPアドレス
        self.node_ips = [
            '127.0.0.1'
            #'192.168.56.101',
            #'192.168.56.102',
            #'192.168.56.103'            
        ]

        # トランザクションプール
        self.tx_pool = {'txs': []}

        # トランザクションプールの保存先
        self.tx_pool_file = './blockchain/data/tx_pool.pkl'

        # ジェネシスブロック
        self.genesis_block = {
            'time':             1736575754.072457,
            'previous_hash':    'none',
            'nonce':            0,
            'txs':              []
        }

        # チェーン
        self.chain = {'blocks': []}
        self.chain['blocks'].append(self.genesis_block)

        # チェーンの保存先
        self.chain_file = './blockchain/data/chain.pkl'

        # マイニングの報酬
        self.reward_coin = 50

        # マイニングの難易度（数が多いほど難しくなる）
        self.difficulty = 4

        # 全ブロックのトランザクションリスト set_all_block_txs() メソッドでセットする
        self.all_block_txs = []

    # ノードのアドレスをどれか１つ返す
    def get_node_ip(self):
        return random.choice(self.node_ips)
    
    # 署名の生成
    def gen_signature(self, target_dict, private_key):
        # 秘密鍵をオブジェクト化
        private_key_obj = SigningKey.from_string(binascii.unhexlify(private_key), curve=SECP256k1)

        # 署名対象をJSONに変換してから署名（辞書型のままでは署名できない）
        target_json = json.dumps(target_dict).encode('utf-8')
        signature   = private_key_obj.sign(target_json)

        # 署名（16進数）を返す
        return signature.hex()
    
    # トランザクションの送信
    def send_tx(self, tx_dict):
        # ノードのIPアドレス
        node_ip = self.get_node_ip()

        # トランザクションの送信先URL
        url = 'http://' + node_ip + ':8000/tx-pool'

        # トランザクションをJSONに変換（辞書型のままでは送信できない）
        tx_json = json.dumps(tx_dict).encode('utf-8')

        # 送信
        res = requests.post(url, tx_json)

        # 送信結果を返す
        return res
    
    # トランザクションプールをファイルに保存する
    def save_tx_pool(self):
        pd.to_pickle(self.tx_pool, self.tx_pool_file)

    # 受け取ったトランザクションをトランザクションプールに追加する
    def add_tx_pool(self, tx):
        self.tx_pool['txs'].append(tx)

        # トランザクションプールをファイルに保存する
        self.save_tx_pool()

    # ファイルに保存されているトランザクションプールを読み出す
    def load_tx_pool(self):
        if os.path.isfile(self.tx_pool_file):
            return pd.read_pickle(self.tx_pool_file)
        else:
            # ファイルが無ければ初期状態のトランザクションプールを返す
            return self.tx_pool
        
    # トランザクションの正当性の検証
    def validate_tx(self, tx):        
        # トランザクションのコピー（値渡し）で検証を行う
        tx_copy = tx.copy()

        # マイナスのコインは許可しない
        if (tx_copy['coin'] < 0):
            print('コインの枚数がマイナス')
            return False

        # 送信者の公開鍵をオブジェクト化
        public_key_obj = VerifyingKey.from_string(binascii.unhexlify(tx_copy['sender']), curve=SECP256k1)

        # トランザクションから署名を取出す
        signature = binascii.unhexlify(tx_copy['signature'])
        del tx_copy['signature']

        # トランザクションをJSONに変換
        tx_json = json.dumps(tx_copy).encode('utf-8')

        # トランザクション署名の検証
        try:
            return public_key_obj.verify(signature, tx_json)
        except BadSignatureError:
            print('トランザクションの署名が不正')
            return False
        
    # トランザクションの重複チェック（二重支払い問題対策）    
    def validate_duplicate_tx(self, tx):
        # トランザクションプールに同じトランザクションがないか？
        if tx in self.tx_pool['txs']:
            print('トランザクションプールに同じトランザクションがある')
            return False
        
        # 全ブロックのトランザクションリストに同じトランザクションがないか？
        if tx in self.all_block_txs:
            print('全ブロックのトランザクションリストに同じトランザクションがある')
            return False
        
        # チェックOK
        return True

    # トランザクションプールの取得
    def get_tx_pool(self):
        # ノードのIPアドレス
        node_ip = self.get_node_ip()

        # トランザクションプールのURL
        url = 'http://' + node_ip + ':8000/tx-pool'

        # 取得実行
        res = requests.get(url)

        # JSONを辞書(dict)型に変換して返す
        tx_pool_dict = res.json()

        return tx_pool_dict
    
    # ファイルに保存されているチェーンを読み出す
    def load_chain(self):
        if os.path.isfile(self.chain_file):
            return pd.read_pickle(self.chain_file)
        else:
            # ファイルが無ければ初期状態のチェーンを返す
            return self.chain
        
    # チェーンの取得
    def get_chain(self):
        # ノードのIPアドレス
        node_ip = self.get_node_ip()

        # トランザクションプールのURL
        url = 'http://' + node_ip + ':8000/chain'

        # 取得実行
        res = requests.get(url)

        # JSONを辞書(dict)型に変換して返す
        chain_dict = res.json()
        return chain_dict
    
    # ハッシュ値の生成
    def gen_hash(self, target_dict):
        # 対象をJSONに変換してからハッシュ化（辞書型のままだとエラーになる）
        target_json = json.dumps(target_dict).encode('utf-8')
        hash        = hashlib.sha256(target_json)

        # ハッシュ値（16進数）を返す
        return hash.hexdigest()
    
    # 報酬用トランザクションの作成
    def make_reward_tx(self, miner_public_key):
        # 報酬用トランザクションを返す
        return {
            'time':         time.time(),
            'sender':       'reward',
            'to':           miner_public_key,
            'coin':         self.reward_coin,
            'signature':    'none'
        }

    # ナンスの検証
    def validate_nonce(self, hash):
        # ハッシュ値の先頭 self.difficulty 文字が 0 であればマイニング成功（ナンスが正しい）とする
        if hash[:self.difficulty] == '0' * self.difficulty:
            return True
        else:
            return False
        
    # チェーンの送信
    def send_chain(self, chain_dict):
        # ノードのIPアドレス
        node_ip = self.get_node_ip()

        # チェーンの送信先URL
        url = 'http://' + node_ip + ':8000/chain'

        # チェーンをJSONに変換（辞書型のままでは送信できない）
        chain_json = json.dumps(chain_dict).encode('utf-8')

        # 送信
        res = requests.post(url, chain_json)

        # 送信結果を返す
        return res
    
    # チェーンの正当性の検証
    def validate_chain(self, chain):
        # 保持しているチェーンよりも長いことをチェック
        if len(self.chain['blocks']) >= len(chain['blocks']):
            print('保持しているチェーンより短い')
            return False

        # ジェネシスブロックが改ざんされていないことをチェック
        if self.genesis_block != chain['blocks'][0]:
            print('ジェネシスブロックが改ざんされている')
            return False

        # トランザクションの入れ物（全ブロックのトランザクションをここに入れる）
        all_block_txs = []

        # 各ブロックの正当性の検証
        for i in range(len(chain['blocks'])):
            # ジェネシスブロックはチェック済みなので検証をスキップ
            if i == 0:
                continue

            # チェック対象のブロック
            block = chain['blocks'][i]

            # 1つ前のブロック
            previous_block = chain['blocks'][i-1]

            # 1つ前のブロックのハッシュ値が正しいことをチェック
            if block['previous_hash'] != self.gen_hash(previous_block):
                print('1つ前のブロックのハッシュ値に誤りがある')
                return False
            
            # ナンスのチェック
            block_hash = self.gen_hash(block)
            if not self.validate_nonce(block_hash):
                print('ナンスに誤りがある')
                return False

            # 報酬用トランザクションの重複チェック用
            reward_duplication = False

            # 各トランザクションの正当性の検証
            for tx in block['txs']:
                # 報酬用のトランザクションのチェック
                if tx['sender'] == 'reward':
                    # 報酬用のトランザクションが重複チェック
                    if reward_duplication:
                        print('報酬用のトランザクションが重複している')
                        return False
                    else:
                        reward_duplication = True

                    # マイニングの報酬が正しく設定されていることをチェック
                    if tx['coin'] != self.reward_coin:
                        print('マイニングの報酬が誤っている')
                        return False
                else:
                    # トランザクションの正当性の検証
                    if not self.validate_tx(tx):
                        print('トランザクションに異常がある')
                        return False
                        
                # トランザクションが再利用されていないことをチェック
                if tx not in all_block_txs:
                    all_block_txs.append(tx)
                else:
                    print('トランザクションが再利用されている')
                    return False
          
        # 各アカウントの残高チェック
        if all_block_txs:
            # 各アカウントの残高を計算
            accounts = self.calc_accounts_balance(all_block_txs)

            # 各アカウントの残高のみを取り出す
            accounts_values = accounts.values()
        
            # 残高がマイナスになるアカウントがある場合はそのチェーンは不正とする
            if min(accounts_values) < 0:
                print('残高がマイナスになるアカウントがある')
                return False        
                                        
        # 検証OK            
        return True

    # チェーンの入替え
    def replace_chain(self, chain):
        self.chain = chain

        # チェーンを入替えたので全ブロックのトランザクションリストを作り直す
        self.set_all_block_txs()
        
        # ブロックに存在するトランザクションはトランザクションプールから削除する
        for tx in self.all_block_txs:
            if tx in self.tx_pool['txs']:
                self.tx_pool['txs'].remove(tx)

        # トランザクションプールをファイルに保存する
        self.save_tx_pool()

        # チェーンをファイルに保存する
        self.save_chain()

    # 全ブロックのトランザクションリストの作成
    def set_all_block_txs(self):
        self.all_block_txs = []
        for i in range(len(self.chain['blocks'])):
            block = self.chain['blocks'][i]
            for tx in block['txs']:
                self.all_block_txs.append(tx)

    # チェーンをファイルに保存する
    def save_chain(self):
        pd.to_pickle(self.chain, self.chain_file)

    # 各アカウントの残高の計算
    def calc_accounts_balance(self, txs):
        # 各カウントの残高の入れ物
        accounts = {}

        # 初期化処理
        accounts['reward'] = 0
        for tx in txs:
            accounts[tx['sender']]  = 0
            accounts[tx['to']]      = 0

        # 残高の計算
        for tx in txs:
            # 送信者の残高を減らす
            accounts[tx['sender']] -= int(tx['coin'])

            # 受信者の残高を増やす
            accounts[tx['to']] += int(tx['coin'])

        # 報酬の送金総額は削除する
        del accounts['reward']

        # 各アカウントの残高を返す
        return accounts

    # トランザクションのブロードキャスト
    def broadcast_tx(self, tx):
        # マルチスレッドで処理する
        with ThreadPoolExecutor() as executor:
            for node_ip in self.node_ips:
                # ブロードキャストがループしないように broadcast パラメータを off にする
                url = 'http://' + node_ip + ':8000/tx-pool?broadcast=off'
                executor.submit(requests.post, url, json.dumps(tx))

    # チェーンのブロードキャスト
    def broadcast_chain(self, chain):
        # マルチスレッドで処理する
        with ThreadPoolExecutor() as executor:
            for node_ip in self.node_ips:
                # ブロードキャストがループしないように broadcast パラメータを off にする
                url = 'http://' + node_ip + ':8000/chain?broadcast=off'
                executor.submit(requests.post, url, json.dumps(chain))