from dataclasses import dataclass
from typing import dataclass_transform


@dataclass_transform(
    frozen_default=True,
    eq_default=True,
    kw_only_default=True,
)
def value_object[ValueObjectClsT](cls: type[ValueObjectClsT]) -> type[ValueObjectClsT]:
    return dataclass(
        frozen=True,
        eq=True,
        kw_only=True,
        repr=True,
        match_args=True,
        slots=True,
    )(cls)
