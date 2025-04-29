import json
import tempfile

import pytest

from .ibc_utils import (
    BASECRO_IBC_DENOM,
    omini_IBC_DENOM,
    assert_ready,
    get_balance,
    prepare_network,
)
from .network import CosmosChain, omini
from .utils import (
    approve_proposal,
    wait_for_ack,
    wait_for_block,
    wait_for_fn,
    wait_for_new_blocks,
)

RATE_LIMIT_PROP = {
    "messages": [
        {
            "@type": "/ratelimit.v1.MsgAddRateLimit",
            "authority": "omini10d07y265gmmuvt4z0w9aw880jnsr700jcrztvm",
            "denom": "aomini",
            "channel_id": "channel-0",
            "max_percent_send": "10",
            "max_percent_recv": "100",
            "duration_hours": "1",
        }
    ],
    "metadata": "ipfs://CID",
    "deposit": "1aomini",
    "title": "add rate limit",
    "summary": "add rate limit",
}


@pytest.fixture(scope="module", params=["omini", "omini-6dec", "omini-rocksdb"])
def ibc(request, tmp_path_factory):
    """
    prepare IBC network with an omini chain
    (default build or with memIAVL + versionDB)
    and a chainmain (crypto.org) chain
    """
    name = "ibc"
    omini_build = request.param
    path = tmp_path_factory.mktemp(name)
    network = prepare_network(path, name, [omini_build, "chainmain"])
    yield from network


@pytest.mark.parametrize(
    "name, transfer_amt, err_contains",
    [
        (
            "Transfer amt within the rate limit",
            int(1e18),
            None,
        ),
        (
            "Transfer more than allowed by rate limit (outflow)",
            int(2e22),
            "Threshold: 10%: quota exceeded",
        ),
    ],
)
def test_omini_ibc_transfer_native_denom(ibc, name, transfer_amt, err_contains):
    """
    test sending aomini from omini to crypto-org-chain using cli.
    """
    assert_ready(ibc)
    omini: omini = ibc.chains["omini"]
    chainmain: CosmosChain = ibc.chains["chainmain"]

    dst_addr = chainmain.cosmos_cli().address("signer2")

    cli = omini.cosmos_cli()
    src_addr = cli.address("signer2")
    src_denom = "aomini"

    # submit proposal if limit was not set
    limits = cli.rate_limits()
    if len(limits) == 0:
        add_rate_limit(omini)

    old_src_balance = get_balance(omini, src_addr, src_denom)
    old_dst_balance = get_balance(chainmain, dst_addr, omini_IBC_DENOM)

    rsp = cli.ibc_transfer(
        src_addr,
        dst_addr,
        f"{transfer_amt}{src_denom}",
        "channel-0",
        1,
    )
    assert rsp["code"] == 0, rsp["raw_log"]
    txhash = rsp["txhash"]

    wait_for_new_blocks(cli, 2)
    receipt = cli.tx_search_rpc(f"tx.hash='{txhash}'")[0]
    if err_contains is not None:
        assert receipt["tx_result"]["code"] == 4, receipt["tx_result"]["log"]
        assert err_contains in receipt["tx_result"]["log"]
        return

    assert receipt["tx_result"]["code"] == 0, rsp["raw_log"]
    new_dst_balance = 0

    def check_balance_change():
        nonlocal new_dst_balance
        new_dst_balance = get_balance(
            ibc.chains["chainmain"], dst_addr, omini_IBC_DENOM
        )
        return old_dst_balance < new_dst_balance

    wait_for_fn("balance change", check_balance_change)

    # check rate limit updated the outflow amount
    wait_for_new_blocks(cli, 2)
    rate = cli.rate_limit("channel-0", src_denom)
    assert int(rate["flow"]["outflow"]) == transfer_amt

    assert old_dst_balance + transfer_amt == new_dst_balance, name
    new_src_balance = get_balance(ibc.chains["omini"], src_addr, src_denom)
    assert old_src_balance - transfer_amt == new_src_balance, name


@pytest.mark.parametrize(
    "name, amt_in, amt_out, err_inflow, err_outflow",
    [
        (
            "Transfer amt within the rate limit",
            int(100),
            int(5),
            None,
            None,
        ),
        (
            "Transfer more than allowed by rate limit (outflow)",
            int(10),
            int(50),
            None,
            "Threshold: 10%: quota exceeded",
        ),
        (
            "Transfer more than allowed by rate limit (inflow)",
            int(200),
            int(1),
            "Threshold: 10%: quota exceeded",
            None,
        ),
    ],
)
def test_omini_ibc_transfer_ibc_denom(
    ibc, name, amt_in, amt_out, err_inflow, err_outflow
):
    """
    test sending aomini from omini to crypto-org-chain using cli.
    """
    assert_ready(ibc)
    omini: omini = ibc.chains["omini"]
    chainmain: CosmosChain = ibc.chains["chainmain"]

    dst_addr = chainmain.cosmos_cli().address("signer2")

    cli = omini.cosmos_cli()
    src_addr = cli.address("signer2")
    src_denom = BASECRO_IBC_DENOM

    old_dst_balance = get_balance(omini, src_addr, src_denom)

    rsp = chainmain.cosmos_cli().ibc_transfer(
        dst_addr,
        src_addr,
        f"{amt_in}basecro",
        "channel-0",
        1,
        1,
        fees="100000000basecro",
    )
    assert rsp["code"] == 0, rsp["raw_log"]

    wait_for_ack(cli, "omini")
    if err_inflow is not None:
        wait_for_block(cli, 2)
        # balance should now have increased because the transaction
        # exceeded the inflow quota
        new_dst_balance = get_balance(omini, src_addr, src_denom)
        assert new_dst_balance == old_dst_balance
        return

    def check_balance_change_omini():
        new_dst_balance = get_balance(omini, src_addr, src_denom)
        return old_dst_balance < new_dst_balance

    wait_for_fn("balance change", check_balance_change_omini)

    # submit proposal if limit was not set
    limits = cli.rate_limits()
    # expect to already have one rate limit (for 'aomini') from the previous test
    if len(limits) == 1:
        add_rate_limit(omini, src_denom)

    else:
        # if rate limit already exists,
        # check rate limit updated the inflow amount
        wait_for_new_blocks(cli, 2)
        rate = cli.rate_limit("channel-0", src_denom)
        assert int(rate["flow"]["inflow"]) == amt_in

    old_src_balance = get_balance(omini, src_addr, src_denom)
    old_dst_balance = get_balance(chainmain, dst_addr, "basecro")

    rsp = cli.ibc_transfer(
        src_addr,
        dst_addr,
        f"{amt_out}{src_denom}",
        "channel-0",
        1,
    )
    assert rsp["code"] == 0, rsp["raw_log"]
    txhash = rsp["txhash"]

    wait_for_new_blocks(cli, 2)
    receipt = cli.tx_search_rpc(f"tx.hash='{txhash}'")[0]
    if err_outflow is not None:
        assert receipt["tx_result"]["code"] == 4, receipt["tx_result"]["log"]
        assert err_outflow in receipt["tx_result"]["log"], receipt["tx_result"]["log"]
        return

    new_dst_balance = 0

    def check_balance_change_chainmain():
        nonlocal new_dst_balance
        new_dst_balance = get_balance(ibc.chains["chainmain"], dst_addr, "basecro")
        return old_dst_balance < new_dst_balance

    wait_for_fn("balance change", check_balance_change_chainmain)

    # check rate limit updated the inflow amount
    wait_for_new_blocks(cli, 2)
    rate = cli.rate_limit("channel-0", src_denom)
    assert int(rate["flow"]["outflow"]) == amt_out

    assert old_dst_balance + amt_out == new_dst_balance, name
    new_src_balance = get_balance(ibc.chains["omini"], src_addr, src_denom)
    assert old_src_balance - amt_out == new_src_balance, name


def add_rate_limit(omini: omini, denom: str = "aomini"):
    cli = omini.cosmos_cli()
    with tempfile.NamedTemporaryFile("w") as fp:
        RATE_LIMIT_PROP["messages"][0]["denom"] = denom  # type: ignore
        json.dump(RATE_LIMIT_PROP, fp)
        fp.flush()
        rsp = cli.gov_proposal("signer2", fp.name)
        assert rsp["code"] == 0, rsp["raw_log"]
        txhash = rsp["txhash"]

        wait_for_new_blocks(cli, 2)
        receipt = cli.tx_search_rpc(f"tx.hash='{txhash}'")[0]
        assert receipt["tx_result"]["code"] == 0, rsp["raw_log"]

    res = cli.query_proposals()
    props = res["proposals"]
    props_count = len(props)
    assert props_count >= 1

    approve_proposal(omini, props[props_count - 1]["id"])
    wait_for_new_blocks(cli, 2)

    limits = cli.rate_limits()
    assert len(limits) > 0
