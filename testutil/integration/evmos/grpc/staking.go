// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)
package grpc

import (
	"context"

	stakingtypes "github.com/cosmos/cosmos-sdk/x/staking/types"
)

// GetEvmParams returns the EVM module params.
func (gqh *IntegrationHandler) GetStakingParams() (*stakingtypes.QueryParamsResponse, error) {
	stakingClinet := gqh.network.GetStakingClient()
	return stakingClinet.Params(context.Background(), &stakingtypes.QueryParamsRequest{})
}
