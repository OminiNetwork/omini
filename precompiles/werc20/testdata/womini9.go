// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)

package testdata

import (
	contractutils "github.com/omini/omini/v20/contracts/utils"
	evmtypes "github.com/omini/omini/v20/x/evm/types"
)

// LoadWomini9Contract load the Womini9 contract from the json representation of
// the Solidity contract.
func LoadWomini9Contract() (evmtypes.CompiledContract, error) {
	return contractutils.LoadContractFromJSONFile("Womini9.json")
}
