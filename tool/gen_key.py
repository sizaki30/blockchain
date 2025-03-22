from ecdsa import SigningKey, SECP256k1

secret_key = SigningKey.generate(curve = SECP256k1)
print("秘密鍵：" + secret_key.to_string().hex())

public_key = secret_key.verifying_key
print("公開鍵：" + public_key.to_string().hex())