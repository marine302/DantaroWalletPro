#!/usr/bin/env python3

# Copyright © 2020-2025, Meheret Tesfaye Batu <meherett.batu@gmail.com>
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit

from ..slip44 import CoinTypes
from ..ecc import SLIP10Ed25519ECC
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


class Sui(ICryptocurrency):

    NAME = "Sui"
    SYMBOL = "SUI"
    INFO = Info({
        "SOURCE_CODE": "https://github.com/MystenLabs/sui",
        "WHITEPAPER": "https://docs.sui.io",
        "WEBSITES": [
            "https://sui.io"
        ]
    })
    ECC = SLIP10Ed25519ECC
    COIN_TYPE = CoinTypes.Sui
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
        "SUI": "Sui"
    })
    DEFAULT_ADDRESS = ADDRESSES.SUI
    PARAMS = Params({
        "KEY_TYPE": 0x00,
        "ADDRESS_PREFIX": "0x"
    })
