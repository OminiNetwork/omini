package evm_test

import (
	"math/big"

	evmante "github.com/omini/omini/v20/app/ante/evm"
	"github.com/omini/omini/v20/testutil"

	storetypes "cosmossdk.io/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	testutiltx "github.com/omini/omini/v20/testutil/tx"
	evmtypes "github.com/omini/omini/v20/x/evm/types"
)

func (suite *AnteTestSuite) TestEthSetupContextDecorator() {
	dec := evmante.NewEthSetUpContextDecorator(suite.GetNetwork().App.EvmKeeper)

	evmChainID := evmtypes.GetEthChainConfig().ChainID

	ethContractCreationTxParams := &evmtypes.EvmTxArgs{
		ChainID:  evmChainID,
		Nonce:    1,
		Amount:   big.NewInt(10),
		GasLimit: 1000,
		GasPrice: big.NewInt(1),
	}
	tx := evmtypes.NewTx(ethContractCreationTxParams)

	testCases := []struct {
		name    string
		tx      sdk.Tx
		expPass bool
	}{
		{"invalid transaction type - does not implement GasTx", &testutiltx.InvalidTx{}, false},
		{
			"success - transaction implement GasTx",
			tx,
			true,
		},
	}

	for _, tc := range testCases {
		suite.Run(tc.name, func() {
			ctx, err := dec.AnteHandle(suite.GetNetwork().GetContext(), tc.tx, false, testutil.NextFn)

			if tc.expPass {
				suite.Require().NoError(err)
				suite.Equal(storetypes.GasConfig{}, ctx.KVGasConfig())
				suite.Equal(storetypes.GasConfig{}, ctx.TransientKVGasConfig())
			} else {
				suite.Require().Error(err)
			}
		})
	}
}
