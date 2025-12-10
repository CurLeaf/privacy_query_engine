# De-Identification module - 去标识化处理
from .rewriter import DeIDRewriter
from .methods import hash_value, mask_email, mask_phone, mask_name, generalize_age

__all__ = [
    "DeIDRewriter",
    "hash_value",
    "mask_email", 
    "mask_phone",
    "mask_name",
    "generalize_age",
]

