#!/bin/bash

KEY="dev0"
CHAINID="omini_9000-1"
MONIKER="mymoniker"
DATA_DIR=$(mktemp -d -t omini-datadir.XXXXX)

echo "create and add new keys"
./ominid keys add $KEY --home "$DATA_DIR" --no-backup --chain-id $CHAINID --algo "eth_secp256k1" --keyring-backend test
echo "init omini with moniker=$MONIKER and chain-id=$CHAINID"
./ominid init $MONIKER --chain-id "$CHAINID" --home "$DATA_DIR"
echo "prepare genesis: Allocate genesis accounts"
./ominid add-genesis-account \
	"$(./ominid keys show "$KEY" -a --home "$DATA_DIR" --keyring-backend test)" 1000000000000000000aomini,1000000000000000000stake \
	--home "$DATA_DIR" --keyring-backend test
echo "prepare genesis: Sign genesis transaction"
./ominid gentx "$KEY" 1000000000000000000stake --keyring-backend test --home "$DATA_DIR" --keyring-backend test --chain-id "$CHAINID"
echo "prepare genesis: Collect genesis tx"
./ominid collect-gentxs --home "$DATA_DIR"
echo "prepare genesis: Run validate-genesis to ensure everything worked and that the genesis file is setup correctly"
./ominid validate-genesis --home "$DATA_DIR"

echo "starting omini node in background ..."
./ominid start --pruning=nothing --rpc.unsafe \
	--keyring-backend test --home "$DATA_DIR" \
	>"$DATA_DIR"/node.log 2>&1 &
disown

echo "started omini node"
tail -f /dev/null
