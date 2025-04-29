from pathlib import Path

import pytest
from pystarport import ports

from .network import build_patched_ominid, setup_custom_omini
from .utils import (
    supervisorctl,
    update_omini_bin,
    update_node_cmd,
    wait_for_block,
    wait_for_port,
)


@pytest.fixture(scope="module")
def custom_omini(tmp_path_factory):
    path = tmp_path_factory.mktemp("rollback")
    broken_binary = build_patched_ominid("broken-ominid")
    print(broken_binary)

    # init with genesis binary
    yield from setup_custom_omini(
        path,
        26300,
        Path(__file__).parent / "configs/rollback-test.jsonnet",
        post_init=update_omini_bin(broken_binary, [1]),
        wait_port=False,
    )


def test_rollback(custom_omini):
    """
    test using rollback command to fix app-hash mismatch situation.
    - the broken node will sync up to block 10 then crash.
    - use rollback command to rollback the db.
    - switch to correct binary should make the node syncing again.
    """
    target_port = ports.rpc_port(custom_omini.base_port(1))
    wait_for_port(target_port)

    print("wait for node1 to sync the first 10 blocks")
    cli1 = custom_omini.cosmos_cli(1)
    wait_for_block(cli1, 10)

    print("wait for a few more blocks on the healthy nodes")
    cli0 = custom_omini.cosmos_cli(0)
    wait_for_block(cli0, 13)

    # (app hash mismatch happens after the 10th block, detected in the 11th block)
    print("check node1 get stuck at block 10")
    assert cli1.block_height() == 10

    print("stop node1")
    supervisorctl(
        custom_omini.base_dir / "../tasks.ini",
        "stop",
        f"{custom_omini.cosmos_cli().chain_id}-node1",
    )

    print("do rollback on node1")
    cli1.rollback()

    print("switch to normal binary")
    update_node_cmd(custom_omini.base_dir, "ominid", 1)
    supervisorctl(custom_omini.base_dir / "../tasks.ini", "update")
    wait_for_port(target_port)

    print("check node1 sync again")
    wait_for_block(cli1, 15)
