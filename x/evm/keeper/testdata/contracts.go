// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)

package testdata

import (
	contractutils "github.com/omini/omini/v20/contracts/utils"
	evmtypes "github.com/omini/omini/v20/x/evm/types"
)

func LoadERC20Contract() (evmtypes.CompiledContract, error) {
	return contractutils.LegacyLoadContractFromJSONFile("ERC20Contract.json")
}

func LoadMessageCallContract() (evmtypes.CompiledContract, error) {
	return contractutils.LegacyLoadContractFromJSONFile("MessageCallContract.json")
}
