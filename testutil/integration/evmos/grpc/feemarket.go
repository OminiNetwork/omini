// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)
package grpc

import (
	"context"

	feemarkettypes "github.com/omini/omini/v20/x/feemarket/types"
)

// GetBaseFee returns the base fee from the feemarket module.
func (gqh *IntegrationHandler) GetBaseFee() (*feemarkettypes.QueryBaseFeeResponse, error) {
	feeMarketClient := gqh.network.GetFeeMarketClient()
	return feeMarketClient.BaseFee(context.Background(), &feemarkettypes.QueryBaseFeeRequest{})
}

// GetBaseFee returns the base fee from the feemarket module.
func (gqh *IntegrationHandler) GetFeeMarketParams() (*feemarkettypes.QueryParamsResponse, error) {
	feeMarketClient := gqh.network.GetFeeMarketClient()
	return feeMarketClient.Params(context.Background(), &feemarkettypes.QueryParamsRequest{})
}
