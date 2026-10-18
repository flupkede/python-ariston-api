"""Unit tests for the Nuos Split GREEN write via the R2 web-app endpoint."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ariston.ariston_api import AristonAPI
from ariston.const import NuosSplitOperativeMode
from ariston.nuos_split_device import AristonNuosSplitDevice


def _device() -> AristonNuosSplitDevice:
    """Instantiate without the abstract machinery; only api+gw are used."""
    cls = AristonNuosSplitDevice
    original = cls.__abstractmethods__
    cls.__abstractmethods__ = frozenset()
    try:
        device = cls.__new__(cls)
    finally:
        cls.__abstractmethods__ = original
    device.api = AristonAPI("user", "pass")
    device.gw = "3C8A1F2EDE84"
    device.data = {}
    return device


def test_build_nuos_r2_payload_green() -> None:
    plant = {
        "gw": "3C8A1F2EDE84",
        "on": True,
        "mode": 2,
        "waterTemp": 49.0,
        "comfortTemp": 54.0,
        "reducedTemp": 16.0,
        "procReqTemp": 54.0,
        "opMode": 1,
        "holidayUntil": None,
        "boostOn": False,
        "hpState": 2,
    }
    payload = AristonAPI._build_nuos_r2_payload(plant, NuosSplitOperativeMode.GREEN.value)

    assert payload["viewModel"]["opMode"] == 0  # GREEN — the value that must change
    assert payload["viewModel"]["plantMode"] == 2
    assert payload["viewModel"]["comfortTemp"] == 54.0
    assert payload["plantData"]["gatewayId"] == "3C8A1F2EDE84"
    assert payload["plantData"]["__type__"] == [
        "my.entities.entityiface",
        "my.entities.slpplantdata",
    ]


def test_green_write_routes_through_r2() -> None:
    device = _device()
    device.api.async_set_nuos_mode_via_r2 = AsyncMock()  # type: ignore[method-assign]
    device.api.async_set_nuos_mode = AsyncMock()  # type: ignore[method-assign]

    asyncio.run(device.async_set_water_heater_operation_mode("GREEN"))

    device.api.async_set_nuos_mode_via_r2.assert_awaited_once_with(
        device.gw, NuosSplitOperativeMode.GREEN
    )
    device.api.async_set_nuos_mode.assert_not_awaited()
    assert device.data["opMode"] == 0


def test_comfort_write_keeps_direct_route() -> None:
    device = _device()
    device.api.async_set_nuos_mode_via_r2 = AsyncMock()  # type: ignore[method-assign]
    device.api.async_set_nuos_mode = AsyncMock()  # type: ignore[method-assign]

    asyncio.run(device.async_set_water_heater_operation_mode("COMFORT"))

    device.api.async_set_nuos_mode.assert_awaited_once_with(
        device.gw, NuosSplitOperativeMode.COMFORT
    )
    device.api.async_set_nuos_mode_via_r2.assert_not_awaited()
    assert device.data["opMode"] == 1


def test_enum_values_match_official_range() -> None:
    assert NuosSplitOperativeMode.GREEN.value == 0
    assert NuosSplitOperativeMode.COMFORT.value == 1
    assert NuosSplitOperativeMode.FAST.value == 2
    assert NuosSplitOperativeMode.AUTO.value == 3  # was mislabeled IMEMORY
