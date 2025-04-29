import pytest

from .network import setup_omini, setup_omini_6dec, setup_omini_rocksdb, setup_geth


@pytest.fixture(scope="session")
def omini(tmp_path_factory):
    path = tmp_path_factory.mktemp("omini")
    yield from setup_omini(path, 26650)


@pytest.fixture(scope="session")
def omini_6dec(tmp_path_factory):
    path = tmp_path_factory.mktemp("omini-6dec")
    yield from setup_omini_6dec(path, 46650)


@pytest.fixture(scope="session")
def omini_rocksdb(tmp_path_factory):
    path = tmp_path_factory.mktemp("omini-rocksdb")
    yield from setup_omini_rocksdb(path, 20650)


@pytest.fixture(scope="session")
def geth(tmp_path_factory):
    path = tmp_path_factory.mktemp("geth")
    yield from setup_geth(path, 8545)


@pytest.fixture(scope="session", params=["omini", "omini-ws", "omini-6dec"])
def omini_rpc_ws(request, omini, omini_6dec):
    """
    run on both omini and omini websocket
    """
    provider = request.param
    if provider == "omini":
        yield omini
    elif provider == "omini-ws":
        omini_ws = omini.copy()
        omini_ws.use_websocket()
        yield omini_ws
    elif provider == "omini-6dec":
        yield omini_6dec
    else:
        raise NotImplementedError


@pytest.fixture(
    scope="module", params=["omini", "omini-ws", "omini-6dec", "omini-rocksdb", "geth"]
)
def cluster(request, omini, omini_6dec, omini_rocksdb, geth):
    """
    run on omini, omini websocket,
    omini built with rocksdb (memIAVL + versionDB)
    and geth
    """
    provider = request.param
    if provider == "omini":
        yield omini
    elif provider == "omini-ws":
        omini_ws = omini.copy()
        omini_ws.use_websocket()
        yield omini_ws
    elif provider == "omini-6dec":
        yield omini_6dec
    elif provider == "geth":
        yield geth
    elif provider == "omini-rocksdb":
        yield omini_rocksdb
    else:
        raise NotImplementedError


@pytest.fixture(scope="module", params=["omini", "omini-6dec", "omini-rocksdb"])
def omini_cluster(request, omini, omini_6dec, omini_rocksdb):
    """
    run on omini default build &
    omini with rocksdb build and memIAVL + versionDB
    """
    provider = request.param
    if provider == "omini":
        yield omini
    elif provider == "omini-6dec":
        yield omini_6dec
    elif provider == "omini-rocksdb":
        yield omini_rocksdb
    else:
        raise NotImplementedError
