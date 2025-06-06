// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)
package coordinator

import (
	"strconv"
	"testing"

	sdk "github.com/cosmos/cosmos-sdk/types"
	ibctesting "github.com/cosmos/ibc-go/v8/testing"
	"github.com/omini/omini/v20/cmd/config"
	"github.com/omini/omini/v20/testutil/integration/common/network"
)

// getIBCChains returns a map of TestChain's for the given network interface.
func getIBCChains(t *testing.T, coord *ibctesting.Coordinator, chains []network.Network) map[string]*ibctesting.TestChain {
	ibcChains := make(map[string]*ibctesting.TestChain)
	for _, chain := range chains {
		ibcChains[chain.GetChainID()] = chain.GetIBCChain(t, coord)
	}
	return ibcChains
}

// generateDummyChains returns a map of dummy chains to complement IBC connections for integration tests.
func generateDummyChains(t *testing.T, coord *ibctesting.Coordinator, numberOfChains int) (map[string]*ibctesting.TestChain, []string) {
	ibcChains := make(map[string]*ibctesting.TestChain)
	ids := make([]string, numberOfChains)
	// dummy chains use the ibc testing chain setup
	// that uses the default sdk address prefix ('cosmos')
	// Update the prefix configs to use that prefix
	cfg := sdk.GetConfig()
	cfg.SetBech32PrefixForAccount(sdk.Bech32PrefixAccAddr, sdk.Bech32PrefixAccPub)
	cfg.SetBech32PrefixForValidator(sdk.Bech32PrefixValAddr, sdk.Bech32PrefixValPub)
	cfg.SetBech32PrefixForConsensusNode(sdk.Bech32PrefixConsAddr, sdk.Bech32PrefixConsPub)
	// Also need to disable address cache to avoid using modules
	// accounts with 'omini' addresses (because omini chain setup is first)
	sdk.SetAddrCacheEnabled(false)
	for i := 1; i <= numberOfChains; i++ {
		chainID := "dummychain-" + strconv.Itoa(i)
		ids[i-1] = chainID
		ibcChains[chainID] = ibctesting.NewTestChain(t, coord, chainID)
	}
	config.SetBech32Prefixes(cfg)
	return ibcChains, ids
}

// mergeMaps merges two maps of TestChain's.
func mergeMaps(m1, m2 map[string]*ibctesting.TestChain) map[string]*ibctesting.TestChain {
	for k, v := range m2 {
		m1[k] = v
	}
	return m1
}
