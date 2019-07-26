from cryptography.fernet import Fernet as fernet


def gen_crypt_key() -> bytes:
    """
    Uses cryptography library to generate deg Fernet encryption key. KEEP IT SAFE!

    Returns:
    --------
    key : bytes
        Fernet encryption key
    """
    key = fernet.generate_key()
    return key


def encrypt(key, msg) -> str:
    """
    Uses cryptography library to encrypt str/bytes with deg key

    Parameters:
    -----------
    key : str, bytes
        Fernet encryption key
    msg : str, bytes
        String or bytes to decrypt

    Returns:
    --------
    Encrypted string
    """
    if isinstance(msg, str):
        msg = bytes(msg, 'utf-8')
    if isinstance(key, str):
        key = bytes(key, 'utf-8')

    f = fernet(key)
    encryption = f.encrypt(msg)
    return encryption.decode('utf-8')


def decrypt(key, msg) -> str:
    """
    Uses cryptography library to decrypt str/bytes with deg key

    Parameters:
    -----------
    key : str, bytes
        Fernet encryption key
    msg : str, bytes
        String or bytes to decrypt

    Returns:
    --------
    Decrypted string
    """
    if isinstance(msg, str):
        msg = bytes(msg, 'utf-8')
    if isinstance(key, str):
        key = bytes(key, 'utf-8')

    f = fernet(key)
    decryption = f.decrypt(msg)
    return decryption.decode('utf-8')
