import json

from .utils import (
    ADDRS,
    CONTRACTS,
    KEYS,
    build_deploy_contract_tx,
    deploy_contract,
    send_transaction,
    w3_wait_for_new_blocks,
)


def test_gas_eth_tx(geth, omini_cluster):
    tx_value = 10

    # send a transaction with geth
    geth_gas_price = geth.w3.eth.gas_price
    tx = {"to": ADDRS["community"], "value": tx_value, "gasPrice": geth_gas_price}
    geth_receipt = send_transaction(geth.w3, tx, KEYS["validator"])

    # send an equivalent transaction with omini
    omini_gas_price = omini_cluster.w3.eth.gas_price
    tx = {"to": ADDRS["community"], "value": tx_value, "gasPrice": omini_gas_price}
    omini_receipt = send_transaction(omini_cluster.w3, tx, KEYS["validator"])

    assert geth_receipt.gasUsed == omini_receipt.gasUsed


def test_gas_deployment(geth, omini_cluster):
    # deploy an identical contract on geth and omini
    # ensure that the gasUsed is equivalent
    info = json.loads(CONTRACTS["TestERC20A"].read_text())
    geth_tx = build_deploy_contract_tx(geth.w3, info)
    omini_tx = build_deploy_contract_tx(omini_cluster.w3, info)

    # estimate tx gas
    geth_gas_estimation = geth.w3.eth.estimate_gas(geth_tx)
    omini_gas_estimation = omini_cluster.w3.eth.estimate_gas(omini_tx)

    assert geth_gas_estimation == omini_gas_estimation

    # sign and send tx
    geth_contract_receipt = send_transaction(geth.w3, geth_tx)
    omini_contract_receipt = send_transaction(omini_cluster.w3, omini_tx)
    assert geth_contract_receipt.status == 1
    assert omini_contract_receipt.status == 1

    assert geth_contract_receipt.gasUsed == omini_contract_receipt.gasUsed

    # gasUsed should be same as estimation
    assert geth_contract_receipt.gasUsed == geth_gas_estimation
    assert omini_contract_receipt.gasUsed == omini_gas_estimation


def test_gas_call(geth, omini_cluster):
    function_input = 10

    # deploy an identical contract on geth and omini
    # ensure that the contract has a function which consumes non-trivial gas
    geth_contract, _ = deploy_contract(geth.w3, CONTRACTS["BurnGas"])
    omini_contract, _ = deploy_contract(omini_cluster.w3, CONTRACTS["BurnGas"])

    # call the contract and get tx receipt for geth
    geth_gas_price = geth.w3.eth.gas_price
    geth_tx = geth_contract.functions.burnGas(function_input).build_transaction(
        {"from": ADDRS["validator"], "gasPrice": geth_gas_price}
    )
    geth_gas_estimation = geth.w3.eth.estimate_gas(geth_tx)
    geth_call_receipt = send_transaction(geth.w3, geth_tx)

    # repeat the above for omini
    omini_gas_price = omini_cluster.w3.eth.gas_price
    omini_tx = omini_contract.functions.burnGas(function_input).build_transaction(
        {"from": ADDRS["validator"], "gasPrice": omini_gas_price}
    )
    omini_gas_estimation = omini_cluster.w3.eth.estimate_gas(omini_tx)
    omini_call_receipt = send_transaction(omini_cluster.w3, omini_tx)

    # ensure gas estimation is the same
    assert geth_gas_estimation == omini_gas_estimation

    # ensure that the gasUsed is equivalent
    assert geth_call_receipt.gasUsed == omini_call_receipt.gasUsed

    # ensure gasUsed == gas estimation
    assert geth_call_receipt.gasUsed == geth_gas_estimation
    assert omini_call_receipt.gasUsed == omini_gas_estimation


def test_block_gas_limit(omini_cluster):
    tx_value = 10

    # get the block gas limit from the latest block
    w3_wait_for_new_blocks(omini_cluster.w3, 5)
    block = omini_cluster.w3.eth.get_block("latest")
    exceeded_gas_limit = block.gasLimit + 100

    # send a transaction exceeding the block gas limit
    omini_gas_price = omini_cluster.w3.eth.gas_price
    tx = {
        "to": ADDRS["community"],
        "value": tx_value,
        "gas": exceeded_gas_limit,
        "gasPrice": omini_gas_price,
    }

    # expect an error due to the block gas limit
    try:
        send_transaction(omini_cluster.w3, tx, KEYS["validator"])
    except Exception as error:
        assert "exceeds block gas limit" in error.args[0]["message"]

    # deploy a contract on omini
    omini_contract, _ = deploy_contract(omini_cluster.w3, CONTRACTS["BurnGas"])

    # expect an error on contract call due to block gas limit
    try:
        burn_gas_tx = omini_contract.functions.burnGas(
            exceeded_gas_limit
        ).build_transaction(
            {
                "from": ADDRS["validator"],
                "gas": exceeded_gas_limit,
                "gasPrice": omini_gas_price,
            }
        )
        send_transaction(omini_cluster.w3, burn_gas_tx, KEYS["validator"])
    except Exception as error:
        assert "exceeds block gas limit" in error.args[0]["message"]


def test_estimate_gas_revert(cluster):
    w3 = cluster.w3
    call = w3.provider.make_request

    validator = ADDRS["validator"]
    contract, _ = deploy_contract(
        w3,
        CONTRACTS["TestRevert"],
    )

    method = "eth_estimateGas"

    def do_call(data):
        params = {"from": validator, "to": contract.address, "data": data}
        return call(method, [params])["error"]

    # revertWithMsg
    error = do_call("0x9ffb86a5")
    assert error["code"] == 3
    assert error["message"] == "execution reverted: Function has been reverted"
    assert (
        error["data"]
        == "0x08c379a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001a46756e6374696f6e20686173206265656e207265766572746564000000000000"
    )  # noqa: E501

    # revertWithoutMsg
    error = do_call("0x3246485d")
    assert error["code"] == -32000
    assert error["message"] == "execution reverted"
