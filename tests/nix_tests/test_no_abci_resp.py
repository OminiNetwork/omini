from pathlib import Path

import pytest

from .network import create_snapshots_dir, setup_custom_omini
from .utils import omini_6DEC_CHAIN_ID, evm6dec_config, memiavl_config, wait_for_block


@pytest.fixture(scope="module")
def custom_omini(tmp_path_factory):
    path = tmp_path_factory.mktemp("no-abci-resp")
    yield from setup_custom_omini(
        path,
        26260,
        Path(__file__).parent / "configs/discard-abci-resp.jsonnet",
    )


@pytest.fixture(scope="module")
def custom_omini_6dec(tmp_path_factory):
    path = tmp_path_factory.mktemp("no-abci-resp-6dec")
    yield from setup_custom_omini(
        path,
        46860,
        evm6dec_config(path, "discard-abci-resp"),
        chain_id=omini_6DEC_CHAIN_ID,
    )


@pytest.fixture(scope="module")
def custom_omini_rocksdb(tmp_path_factory):
    path = tmp_path_factory.mktemp("no-abci-resp-rocksdb")
    yield from setup_custom_omini(
        path,
        26810,
        memiavl_config(path, "discard-abci-resp"),
        post_init=create_snapshots_dir,
        chain_binary="ominid-rocksdb",
    )


@pytest.fixture(scope="module", params=["omini", "omini-6dec", "omini-rocksdb"])
def omini_cluster(request, custom_omini, custom_omini_6dec, custom_omini_rocksdb):
    """
    run on omini and
    omini built with rocksdb (memIAVL + versionDB)
    """
    provider = request.param
    if provider == "omini":
        yield custom_omini
    elif provider == "omini-6dec":
        yield custom_omini_6dec
    elif provider == "omini-rocksdb":
        yield custom_omini_rocksdb

    else:
        raise NotImplementedError


def test_gas_eth_tx(omini_cluster):
    """
    When node does not persist ABCI responses
    eth_gasPrice should return an error instead of crashing
    """
    wait_for_block(omini_cluster.cosmos_cli(), 3)
    try:
        omini_cluster.w3.eth.gas_price  # pylint: disable=pointless-statement
        raise Exception(  # pylint: disable=broad-exception-raised
            "This query should have failed"
        )
    except Exception as error:
        assert "block result not found" in error.args[0]["message"]
