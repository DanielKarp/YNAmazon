# pyright: strict
from collections import deque
from typing import Any, Union

from .sentinels import MISSING


def getattr_path(
    obj: object, path: str, *, separator: str = "__", default: Any = MISSING
) -> Union[Any, None]:
    """Get an attribute path, as defined by a string separated by '__'.

    Example:
    ```
    >>> foo = Foo(a=Bar(b=Baz(c=42)))
    >>> getattr_path(foo, 'a__b__c')
    42
    ```


    Args:
        obj: The object to get the attribute from.
        path: The path to the attribute.
        separator: The separator to use.
        default: The default value to return if the attribute is not found.

    Returns:
        The attribute at the given path.

    Raises:
        AttributeError: If the attribute does not exist, including any intermediate attributes.
    """
    if path == "":
        return obj
    current = obj
    attr_path = deque(path.split(separator))
    for name in attr_path:
        if default is MISSING:
            try:
                current = getattr(current, name)
            except AttributeError as e:
                msg = f"'{type(obj).__name__}' object has no attribute path '{path}', since {e}"
                raise AttributeError(msg) from e

        else:
            current = getattr(current, name, MISSING)
            if current is MISSING:
                return default
        if current is None:
            return None
    return current
