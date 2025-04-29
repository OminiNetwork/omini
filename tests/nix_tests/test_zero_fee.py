from pathlib import Path

import pytest
from web3 import Web3

from .network import create_snapshots_dir, setup_custom_omini
from .utils import (
    ADDRS,
    omini_6DEC_CHAIN_ID,
    KEYS,
    eth_to_bech32,
    evm6dec_config,
    memiavl_config,
    send_transaction,
    wait_for_fn,
)


@pytest.fixture(scope="module")
def custom_omini(tmp_path_factory):
    yield from setup_custom_omini(
        tmp_path_factory.mktemp("zero-fee"),
        26900,
        Path(__file__).parent / "configs/zero-fee.jsonnet",
    )


@pytest.fixture(scope="module")
def custom_omini_6dec(tmp_path_factory):
    """
    Setup an omini chain with
    an evm denom with 6 decimals
    """
    path = tmp_path_factory.mktemp("zero-fee-6dec")
    yield from setup_custom_omini(
        path, 46900, evm6dec_config(path, "zero-fee"), chain_id=omini_6DEC_CHAIN_ID
    )


@pytest.fixture(scope="module")
def custom_omini_rocksdb(tmp_path_factory):
    path = tmp_path_factory.mktemp("zero-fee-rocksdb")
    yield from setup_custom_omini(
        path,
        26810,
        memiavl_config(path, "zero-fee"),
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


def test_cosmos_tx(omini_cluster):
    """
    test basic cosmos transaction works with zero fees
    """
    cli = omini_cluster.cosmos_cli()
    denom = cli.evm_denom()
    sender = eth_to_bech32(ADDRS["signer1"])
    receiver = eth_to_bech32(ADDRS["signer2"])
    amt = 1000

    old_src_balance = cli.balance(sender, denom)
    old_dst_balance = cli.balance(receiver, denom)

    tx = cli.transfer(
        sender,
        receiver,
        f"{amt}{denom}",
        gas_prices=f"0{denom}",
        generate_only=True,
    )

    tx = cli.sign_tx_json(tx, sender, max_priority_price=0)

    rsp = cli.broadcast_tx_json(tx, broadcast_mode="sync")
    assert rsp["code"] == 0, rsp["raw_log"]

    new_dst_balance = 0

    def check_balance_change():
        nonlocal new_dst_balance
        new_dst_balance = cli.balance(receiver, denom)
        return old_dst_balance != new_dst_balance

    wait_for_fn("balance change", check_balance_change)
    assert old_dst_balance + amt == new_dst_balance
    new_src_balance = cli.balance(sender, denom)
    # no fees paid, so sender balance should be
    # initial_balance - amount_sent
    assert old_src_balance - amt == new_src_balance


def test_eth_tx(omini_cluster):
    """
    test basic Ethereum transaction works with zero fees
    """
    w3: Web3 = omini_cluster.w3

    sender = ADDRS["signer1"]
    receiver = ADDRS["signer2"]
    amt = int(1e18)

    old_src_balance = w3.eth.get_balance(sender)
    old_dst_balance = w3.eth.get_balance(receiver)

    receipt = send_transaction(
        w3,
        {
            "from": sender,
            "to": receiver,
            "value": amt,
            "gasPrice": 0,
        },
        KEYS["signer1"],
    )
    assert receipt.status == 1

    new_dst_balance = 0

    def check_balance_change():
        nonlocal new_dst_balance
        new_dst_balance = w3.eth.get_balance(receiver)
        return old_dst_balance != new_dst_balance

    wait_for_fn("balance change", check_balance_change)
    assert old_dst_balance + amt == new_dst_balance
    new_src_balance = w3.eth.get_balance(sender)
    # no fees paid, so sender balance should be
    # initial_balance - amount_sent
    assert old_src_balance - amt == new_src_balance
