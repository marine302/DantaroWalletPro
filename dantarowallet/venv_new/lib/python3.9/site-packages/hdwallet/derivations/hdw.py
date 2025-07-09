#!/usr/bin/env python3

# Copyright © 2020-2025, Meheret Tesfaye Batu <meherett.batu@gmail.com>
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit

from typing import (
    Tuple, Union, Optional, Dict, Type
)

from ..ecc import (
    ECCS as EllipticCurveCryptographies, IEllipticCurveCryptography
)
from ..utils import (
    normalize_index, normalize_derivation, index_tuple_to_string
)
from ..exceptions import DerivationError
from .iderivation import IDerivation


class ECCS:

    SLIP10_Secp256k1: str = "SLIP10-Secp256k1"
    SLIP10_Ed25519: str = "SLIP10-Ed25519"
    SLIP10_Nist256p1: str = "SLIP10-Nist256p1"
    KHOLAW_ED25519: str = "Kholaw-Ed25519"
    SLIP10_Ed25519_Blake2b: str = "SLIP10-Ed25519-Blake2b"
    SLIP10_Ed25519_Monero: str = "SLIP10-Ed25519-Monero"


class HDWDerivation(IDerivation):
    """
    This class implements the HDW standard for hierarchical deterministic wallets.
    HDW defines a specific path structure for deriving keys from a master seed.

    .. note::
        This class inherits from the ``IDerivation`` class, thereby ensuring that all functions are accessible.

    +------------------------+------------------------+
    | Name                   | Value                  |
    +========================+========================+
    | SLIP10_Secp256k1       | SLIP10-Secp256k1       |
    +------------------------+------------------------+
    | SLIP10_Ed25519         | SLIP10-Ed25519         |
    +------------------------+------------------------+
    | SLIP10_Nist256p1       | SLIP10-Nist256p1       |
    +------------------------+------------------------+
    | KHOLAW_ED25519         | Kholaw-Ed25519         |
    +------------------------+------------------------+ 
    | SLIP10_Ed25519_Blake2b | SLIP10-Ed25519-Blake2b |
    +------------------------+------------------------+
    | SLIP10_Ed25519_Monero  | SLIP10-Ed25519-Monero  |
    +------------------------+------------------------+
    """

    _account: Union[Tuple[int, bool], Tuple[int, int, bool]]
    _ecc: Tuple[int, bool]
    _address: Union[Tuple[int, bool], Tuple[int, int, bool]]
    eccs: Dict[str, int] = {
        "SLIP10-Secp256k1": 0,
        "SLIP10-Ed25519": 1,
        "SLIP10-Nist256p1": 2,
        "Kholaw-Ed25519": 3,
        "SLIP10-Ed25519-Blake2b": 4,
        "SLIP10-Ed25519-Monero": 5
    }

    def __init__(
        self,
        account: Union[str, int, Tuple[int, int]] = 0,
        ecc: Optional[Union[str, int, Type[IEllipticCurveCryptography]]] = "SLIP10-Secp256k1",
        address: Union[str, int, Tuple[int, int]] = 0
    ) -> None:
        """
        Initialize a HDW derivation path with specified parameters.

        :param account: The HDW account index or tuple. Defaults to 0.
        :type account: Union[str, int, Tuple[int, int]]
        :param ecc: The HDW ecc index. 
        :type ecc: Union[str, int, Type[IEllipticCurveCryptography]]
        :param address: The HDW address index or tuple. Defaults to 0.
        :type address: Union[str, int, Tuple[int, int]]

        :return: None
        """
        super(HDWDerivation, self).__init__()

        self.excepted_ecc = [
            *self.eccs.keys(),
            *self.eccs.values(),
            *EllipticCurveCryptographies.classes(),
            *map(str, self.eccs.values())
        ]
        if ecc not in self.excepted_ecc:
            raise DerivationError(
                f"Bad {self.name()} ecc index", expected=self.excepted_ecc, got=ecc
            )
        ecc = ecc if type(ecc) in [str, int] else ecc.NAME

        self._account = normalize_index(index=account, hardened=True)
        self._ecc = normalize_index(
            index=(self.eccs[ecc] if ecc in self.eccs.keys() else ecc), hardened=False
        )
        self._address = normalize_index(index=address, hardened=False)
        self._path, self._indexes, self._derivations = normalize_derivation(path=(
            f"m/"
            f"{index_tuple_to_string(index=self._account)}/"
            f"{index_tuple_to_string(index=self._ecc)}/"
            f"{index_tuple_to_string(index=self._address)}"
        ))

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the derivation class.

        :return: The name of the derivation class.
        :rtype: str
        """

        return "HDW"


    def from_account(self, account: Union[str, int, Tuple[int, int]]) -> "HDWDerivation":
        """
        Set the object's `_account` attribute to the specified account index or tuple,
        updating `_path`, `_indexes`, and `_derivations` accordingly.

        :param account: The account index or tuple to set. Can be a string, integer, or tuple of two integers.
        :type account: Union[str, int, Tuple[int, int]]

        :return: The updated `HDWDerivation` object itself after setting the account.
        :rtype: HDWDerivation
        """

        self._account = normalize_index(index=account, hardened=True)
        self._path, self._indexes, self._derivations = normalize_derivation(path=(
            f"m/"
            f"{index_tuple_to_string(index=self._account)}/"
            f"{index_tuple_to_string(index=self._ecc)}/"
            f"{index_tuple_to_string(index=self._address)}"
        ))
        return self

    def from_ecc(self, ecc: Union[str, int, Type[IEllipticCurveCryptography]]) -> "HDWDerivation":
        """
        Set the object's `_ecc` attribute to the specified ecc index or key,
        updating `_path`, `_indexes`, and `_derivations` accordingly.

        :param ecc: The ecc index or key to set. Can be a string, integer, or one of the predefined keys.
        :type ecc: Union[str, int, Type[IEllipticCurveCryptography]]

        :return: The updated `HDWDerivation` object itself after setting the ecc.
        :rtype: HDWDerivation
        """

        if ecc not in self.excepted_ecc:
            raise DerivationError(
                f"Bad {self.name()} ecc index", expected=self.excepted_ecc, got=ecc
            )
        ecc = ecc if type(ecc) in [str, int] else ecc.NAME
        self._ecc = normalize_index(
            index=(self.eccs[ecc] if ecc in self.eccs.keys() else ecc), hardened=False
        )
        self._path, self._indexes, self._derivations = normalize_derivation(path=(
            f"m/"
            f"{index_tuple_to_string(index=self._account)}/"
            f"{index_tuple_to_string(index=self._ecc)}/"
            f"{index_tuple_to_string(index=self._address)}"
        ))
        return self

    def from_address(self, address: Union[str, int, Tuple[int, int]]) -> "HDWDerivation":
        """
        Set the object's `_address` attribute to the specified address index or tuple of indexes,
        updating `_path`, `_indexes`, and `_derivations` accordingly.

        :param address: The address index or tuple of indexes to set. Should be non-hardened.
        :type address: Union[str, int, Tuple[int, int]]

        :return: The updated `HDWDerivation` object itself after setting the address.
        :rtype: HDWDerivation
        """

        self._address = normalize_index(index=address, hardened=False)
        self._path, self._indexes, self._derivations = normalize_derivation(path=(
            f"m/"
            f"{index_tuple_to_string(index=self._account)}/"
            f"{index_tuple_to_string(index=self._ecc)}/"
            f"{index_tuple_to_string(index=self._address)}"
        ))
        return self

    def clean(self) -> "HDWDerivation":
        """
        Reset the object's attributes related to HDW derivation to their initial states or defaults.

        :return: The updated `HDWDerivation` object itself after cleaning.
        :rtype: HDWDerivation
        """

        self._account = normalize_index(index=0, hardened=True)
        self._address = normalize_index(index=0, hardened=False)
        self._path, self._indexes, self._derivations = normalize_derivation(path=(
            f"m/"
            f"{index_tuple_to_string(index=self._account)}/"
            f"{index_tuple_to_string(index=self._ecc)}/"
            f"{index_tuple_to_string(index=self._address)}"
        ))
        return self

    def account(self) -> int:
        """
        Retrieve the account value from the object's `_account` attribute.

        Checks the length of `_account`. If it equals 3, returns the second
        element; otherwise, returns the first element.

        :return: The account value stored in `_account`.
        :rtype: int
        """

        return (
            self._account[1] if len(self._account) == 3 else self._account[0]
        )

    def ecc(self) -> str:
        """
        Retrieve the ecc value from the object's eccs dictionary.

        Iterates through the `eccs` dictionary, and if a value matches the first element of `_ecc`,
        sets the corresponding key as the ecc value.

        :return: The key from the `eccs` dictionary that corresponds to the `_ecc` value, or `None` if not found.
        :rtype: str
        """

        _ecc: Optional[str] = None
        for key, value in self.eccs.items():
            if value == self._ecc[0]:
                _ecc = key
                break
        return _ecc

    def address(self) -> int:
        """
        Retrieve the address from the object.

        :return: The address value.
        :rtype: int
        """

        return (
            self._address[1] if len(self._address) == 3 else self._address[0]
        )
