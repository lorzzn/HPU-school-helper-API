import base64


def encode_base64(source):
    base64_data = base64.b64encode(source)
    s = base64_data.decode()
    return s

def decode_base64(source):
    return base64.b64decode(source)
