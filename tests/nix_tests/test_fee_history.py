from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from web3 import Web3

from .network import setup_omini, setup_omini_6dec, setup_omini_rocksdb
from .utils import ADDRS, send_transaction


@pytest.fixture(scope="module")
def custom_omini(tmp_path_factory):
    path = tmp_path_factory.mktemp("fee-history")
    yield from setup_omini(path, 26500)


@pytest.fixture(scope="module")
def custom_omini_6dec(tmp_path_factory):
    path = tmp_path_factory.mktemp("fee-history-6dec")
    yield from setup_omini_6dec(path, 46510)


@pytest.fixture(scope="module")
def custom_omini_rocksdb(tmp_path_factory):
    path = tmp_path_factory.mktemp("fee-history-rocksdb")
    yield from setup_omini_rocksdb(path, 26510)


@pytest.fixture(scope="module", params=["omini", "omini-6dec", "omini-rocksdb", "geth"])
def cluster(request, custom_omini, custom_omini_6dec, custom_omini_rocksdb, geth):
    """
    run on omini, omini built with rocksdb and geth
    """
    provider = request.param
    if provider == "omini":
        yield custom_omini
    elif provider == "omini-6dec":
        yield custom_omini_6dec
    elif provider == "omini-rocksdb":
        yield custom_omini_rocksdb
    elif provider == "geth":
        yield geth
    else:
        raise NotImplementedError


def test_basic(cluster):
    w3: Web3 = cluster.w3
    call = w3.provider.make_request
    tx = {"to": ADDRS["community"], "value": 10, "gasPrice": w3.eth.gas_price}
    send_transaction(w3, tx)
    size = 4
    # size of base fee + next fee
    max_size = size + 1
    # only 1 base fee + next fee
    min_size = 2
    method = "eth_feeHistory"
    field = "baseFeePerGas"
    percentiles = [100]
    height = w3.eth.block_number
    latest = dict(
        blocks=["latest", hex(height)],
        expect=max_size,
    )
    earliest = dict(
        blocks=["earliest", "0x0"],
        expect=min_size,
    )
    for tc in [latest, earliest]:
        res = []
        with ThreadPoolExecutor(len(tc["blocks"])) as executor:
            tasks = [
                executor.submit(call, method, [size, b, percentiles])
                for b in tc["blocks"]
            ]
            res = [future.result()["result"][field] for future in as_completed(tasks)]
        assert len(res) == len(tc["blocks"])
        assert res[0] == res[1]
        assert len(res[0]) == tc["expect"]

    for x in range(max_size):
        i = x + 1
        fee_history = call(method, [size, hex(i), percentiles])
        # start to reduce diff on i <= size - min
        diff = size - min_size - i
        reduce = size - diff
        target = reduce if diff >= 0 else max_size
        res = fee_history["result"]
        assert len(res[field]) == target
        oldest = i + min_size - max_size
        assert res["oldestBlock"] == hex(oldest if oldest > 0 else 0)
