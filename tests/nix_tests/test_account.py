import pytest
from web3 import Web3

from .network import setup_omini, setup_omini_6dec, setup_omini_rocksdb
from .utils import (
    ADDRS,
    KEYS,
    derive_new_account,
    send_transaction,
    w3_wait_for_new_blocks,
)


# start a brand new chain for this test
@pytest.fixture(scope="module")
def custom_omini(tmp_path_factory):
    path = tmp_path_factory.mktemp("account")
    yield from setup_omini(path, 26700, long_timeout_commit=True)


@pytest.fixture(scope="module")
def custom_omini_6dec(tmp_path_factory):
    path = tmp_path_factory.mktemp("account-6dec")
    yield from setup_omini_6dec(
        path,
        46777,
    )


# ATM rocksdb build is not supported for sdkv0.50
# This is due to cronos dependencies (versionDB, memIAVL)
@pytest.fixture(scope="module")
def custom_omini_rocksdb(tmp_path_factory):
    path = tmp_path_factory.mktemp("account-rocksdb")
    yield from setup_omini_rocksdb(
        path,
        26777,
    )


@pytest.fixture(
    scope="module", params=["omini", "omini-ws", "omini-6dec", "omini-rocksdb", "geth"]
)
def cluster(request, custom_omini, custom_omini_6dec, custom_omini_rocksdb, geth):
    """
    run on omini, omini websocket,
    omini built with rocksdb (memIAVL + versionDB)
    and geth
    """
    provider = request.param
    if provider == "omini":
        yield custom_omini
    elif provider == "omini-ws":
        omini_ws = custom_omini.copy()
        omini_ws.use_websocket()
        yield omini_ws
    elif provider == "omini-6dec":
        yield custom_omini_6dec
    elif provider == "omini-rocksdb":
        yield custom_omini_rocksdb
    elif provider == "geth":
        yield geth
    else:
        raise NotImplementedError


def test_get_transaction_count(cluster):
    w3: Web3 = cluster.w3
    blk = hex(w3.eth.block_number)
    sender = ADDRS["validator"]

    receiver = derive_new_account().address
    n0 = w3.eth.get_transaction_count(receiver, blk)
    # ensure transaction send in new block
    w3_wait_for_new_blocks(w3, 1, sleep=0.1)
    receipt = send_transaction(
        w3,
        {
            "from": sender,
            "to": receiver,
            "value": 1000,
        },
        KEYS["validator"],
    )
    assert receipt.status == 1
    [n1, n2] = [w3.eth.get_transaction_count(receiver, b) for b in [blk, "latest"]]
    assert n0 == n1
    assert n0 == n2


def test_query_future_blk(cluster):
    w3: Web3 = cluster.w3
    acc = derive_new_account(2).address
    current = w3.eth.block_number
    future = current + 1000
    with pytest.raises(ValueError) as exc:
        w3.eth.get_transaction_count(acc, hex(future))
    print(acc, str(exc))
    assert "-32000" in str(exc)
