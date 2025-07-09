#!/usr/bin/env python3

# Copyright © 2020-2025, Meheret Tesfaye Batu <meherett.batu@gmail.com>
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit

from ..slip44 import CoinTypes
from ..ecc import SLIP10Nist256p1ECC
from ..const import (
    Info, Entropies, Mnemonics, Seeds, HDs, Addresses, Networks, Params, XPrivateKeyVersions, XPublicKeyVersions
)
from .icryptocurrency import (
    ICryptocurrency, INetwork
)


class Mainnet(INetwork):

    XPRIVATE_KEY_VERSIONS = XPrivateKeyVersions({
        "P2PKH": 0x0488ade4
    })
    XPUBLIC_KEY_VERSIONS = XPublicKeyVersions({
        "P2PKH": 0x0488b21e
    })


class Neo(ICryptocurrency):

    NAME = "Neo"
    SYMBOL = "NEO"
    INFO = Info({
        "SOURCE_CODE": "https://github.com/neo-project/neo",
        "WHITEPAPER": "https://docs.neo.org/docs/en-us/index.html",
        "WEBSITES": [
            "https://neo.org"
        ]
    })
    ECC = SLIP10Nist256p1ECC
    COIN_TYPE = CoinTypes.Neo
    NETWORKS = Networks({
        "MAINNET": Mainnet
    })
    DEFAULT_NETWORK = NETWORKS.MAINNET
    ENTROPIES = Entropies({
        "BIP39"
    })
    MNEMONICS = Mnemonics({
        "BIP39"
    })
    SEEDS = Seeds({
        "BIP39"
    })
    HDS = HDs({
        "BIP32", "BIP44"
    })
    DEFAULT_HD = HDS.BIP44
    ADDRESSES = Addresses({
        "NEO": "Neo"
    })
    DEFAULT_ADDRESS = ADDRESSES.NEO
    PARAMS = Params({
        "ADDRESS_PREFIX": 0x21,
        "ADDRESS_SUFFIX": 0xAC,
        "ADDRESS_VERSION": 0x17,
        "ALPHABET": "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    })
