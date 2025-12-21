# De-Identification module - 去标识化处理
from .rewriter import DeIDRewriter
from .methods import (
    hash_value,
    mask_email,
    mask_phone,
    mask_name,
    generalize_age,
    format_preserving_encrypt,
    date_shift,
    geographic_generalize,
    suppress_rare_values,
    KAnonymizer,
    LDiversifier
)

__all__ = [
    "DeIDRewriter",
    "hash_value",
    "mask_email", 
    "mask_phone",
    "mask_name",
    "generalize_age",
    "format_preserving_encrypt",
    "date_shift",
    "geographic_generalize",
    "suppress_rare_values",
    "KAnonymizer",
    "LDiversifier",
]

