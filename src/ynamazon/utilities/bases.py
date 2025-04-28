from collections.abc import Iterable, Iterator
from typing import (
    TYPE_CHECKING,
    Generic,
    SupportsIndex,
    TypeVar,
    Union,
    overload,
)

from pydantic import RootModel

from .sentinels import MISSING, Missing

if TYPE_CHECKING:
    from _collections_abc import dict_items, dict_keys, dict_values

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_T = TypeVar("_T")


class SimpleDict(RootModel[dict[_KT, _VT]], Generic[_KT, _VT]):
    """An implementation of Pydantic's RootModel for dictionaries.

    Adds (most) methods from the built-in dict class.
    """

    def __len__(self) -> int:
        """Return the number of items in the dictionary."""
        return len(self.root)

    def keys(self) -> "dict_keys[_KT, _VT]":
        """Return a new view of the dictionary's keys."""
        return self.root.keys()

    def values(self) -> "dict_values[_KT, _VT]":
        """Return a new view of the dictionary's values."""
        return self.root.values()

    def items(self) -> "dict_items[_KT, _VT]":
        """Return a new view of the dictionary's items (key, value)."""
        return self.root.items()

    @overload  # type: ignore[override]
    def get(self, key: _KT, /) -> Union[_VT, None]: ...
    @overload
    def get(self, key: _KT, default: _VT, /) -> _VT: ...
    @overload
    def get(self, key: _KT, default: _T, /) -> Union[_VT, _T]: ...
    def get(
        self, key: _KT, default: Union[_T, _VT, Missing] = MISSING, /
    ) -> Union[_VT, _T, None]:
        """Return the value for key if key is in the dictionary, else default.

        Args:
            key: The key to get.
            default: The default value to return if the key is not found.
        """
        normal_default = default if default is not MISSING else None

        return self.root.get(key, normal_default)

    @overload
    def pop(self, key: _KT, /) -> _VT: ...
    @overload
    def pop(self, key: _KT, default: _VT, /) -> _VT: ...
    @overload
    def pop(self, key: _KT, default: _T, /) -> Union[_VT, _T]: ...
    def pop(
        self, key: _KT, default: Union[_T, _VT, Missing] = MISSING, /
    ) -> Union[_VT, _T]:
        """Remove specified key and return the corresponding value.

        Args:
            key: The key to remove.
            default: The default value to return if the key is not found.
        """
        if default is MISSING:
            return self.root.pop(key)
        return self.root.pop(key, default)

    def __getitem__(self, key: _KT) -> _VT:
        """Return the value for key."""
        return self.root[key]

    def __setitem__(self, key: _KT, value: _VT) -> None:
        """Set the value for key."""
        self.root[key] = value

    def __delitem__(self, key: _KT) -> None:
        """Delete self[key]."""
        del self.root[key]

    def __eq__(self, value: object, /) -> bool:
        """Return self==value."""
        return self.root == value

    def __reversed__(self) -> Iterator[_KT]:
        """Return a reverse iterator over the keys of the dictionary."""
        return reversed(self.root)


class SimpleListRoot(RootModel[list[_T]], Generic[_T]):
    """An implementation of Pydantic's RootModel for lists.

    Adds (most) methods from the built-in list class.
    """

    def __iter__(self):
        return iter(self.root)

    @overload
    def __getitem__(self, item: SupportsIndex, /) -> _T: ...
    @overload
    def __getitem__(self, item: slice, /) -> list[_T]: ...
    def __getitem__(self, item):
        return self.root[item]

    @overload
    def __setitem__(self, key: SupportsIndex, value: _T) -> None: ...
    @overload
    def __setitem__(self, key: slice, value: Iterable[_T]) -> None: ...
    def __setitem__(self, key, value):
        self.root[key] = value

    def append(self, item: _T):
        """Append an item to the end of class."""
        self.root.append(item)

    def pop(self, index: int = -1) -> _T:
        """Remove and return item at index (default last)."""
        return self.root.pop(index)

    def __add__(self, other: "SimpleListRoot | Iterable[_T]"):
        if isinstance(other, SimpleListRoot):
            self.root += other.root
        elif isinstance(other, Iterable):
            self.root += list(other)
        else:
            raise NotImplementedError

        return self

    def __len__(self):
        return len(self.root)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.root})"
