// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)

package utils

import (
	"fmt"
	"sort"
	"strings"

	ibctransfertypes "github.com/cosmos/ibc-go/v8/modules/apps/transfer/types"
	"github.com/ethereum/go-ethereum/common"

	"github.com/omini/omini/v20/crypto/ethsecp256k1"

	errorsmod "cosmossdk.io/errors"
	"github.com/cosmos/cosmos-sdk/crypto/keys/ed25519"
	cryptotypes "github.com/cosmos/cosmos-sdk/crypto/types"
	"github.com/cosmos/cosmos-sdk/crypto/types/multisig"
	sdk "github.com/cosmos/cosmos-sdk/types"
	errortypes "github.com/cosmos/cosmos-sdk/types/errors"
	"golang.org/x/exp/constraints"
)

const (
	// MainnetChainID defines the omini EIP155 chain ID for mainnet
	MainnetChainID = "omini_9001"
	// TestnetChainID defines the omini EIP155 chain ID for testnet
	TestnetChainID = "omini_9000"
	// TestingChainID defines the omini EIP155 chain ID for testing purposes
	// like the local node.
	TestingChainID = "omini_9002"
	// SixDecChainID defines the omini EIP155 chain ID with 6 decimals precision
	SixDecChainID = "ominiix_9000"
	// ICSChainID defines the omini EIP155 chain ID with IBC uatom as denom with 6 decimals precision
	ICSChainID = "ominiics_9000"
)

// EthHexToCosmosAddr takes a given Hex string and derives a Cosmos SDK account address
// from it.
func EthHexToCosmosAddr(hexAddr string) sdk.AccAddress {
	return EthToCosmosAddr(common.HexToAddress(hexAddr))
}

// EthToCosmosAddr converts a given Ethereum style address to an SDK address.
func EthToCosmosAddr(addr common.Address) sdk.AccAddress {
	return sdk.AccAddress(addr.Bytes())
}

// Bech32ToHexAddr converts a given Bech32 address string and converts it to
// an Ethereum address.
func Bech32ToHexAddr(bech32Addr string) (common.Address, error) {
	accAddr, err := sdk.AccAddressFromBech32(bech32Addr)
	if err != nil {
		return common.Address{}, errorsmod.Wrapf(err, "failed to convert bech32 string to address")
	}

	return CosmosToEthAddr(accAddr), nil
}

// CosmosToEthAddr converts a given SDK account address to
// an Ethereum address.
func CosmosToEthAddr(accAddr sdk.AccAddress) common.Address {
	return common.BytesToAddress(accAddr.Bytes())
}

// IsMainnet returns true if the chain-id has the omini mainnet EIP155 chain prefix.
func IsMainnet(chainID string) bool {
	return strings.HasPrefix(chainID, MainnetChainID)
}

// IsTestnet returns true if the chain-id has the omini testnet EIP155 chain prefix.
func IsTestnet(chainID string) bool {
	return strings.HasPrefix(chainID, TestnetChainID)
}

// IsSupportedKey returns true if the pubkey type is supported by the chain
// (i.e eth_secp256k1, amino multisig, ed25519).
// NOTE: Nested multisigs are not supported.
func IsSupportedKey(pubkey cryptotypes.PubKey) bool {
	switch pubkey := pubkey.(type) {
	case *ethsecp256k1.PubKey, *ed25519.PubKey:
		return true
	case multisig.PubKey:
		if len(pubkey.GetPubKeys()) == 0 {
			return false
		}

		for _, pk := range pubkey.GetPubKeys() {
			switch pk.(type) {
			case *ethsecp256k1.PubKey, *ed25519.PubKey:
				continue
			default:
				// Nested multisigs are unsupported
				return false
			}
		}

		return true
	default:
		return false
	}
}

// GetominiAddressFromBech32 returns the sdk.Account address of given address,
// while also changing bech32 human readable prefix (HRP) to the value set on
// the global sdk.Config (eg: `omini`).
// The function fails if the provided bech32 address is invalid.
func GetominiAddressFromBech32(address string) (sdk.AccAddress, error) {
	bech32Prefix := strings.SplitN(address, "1", 2)[0]
	if bech32Prefix == address {
		return nil, errorsmod.Wrapf(errortypes.ErrInvalidAddress, "invalid bech32 address: %s", address)
	}

	addressBz, err := sdk.GetFromBech32(address, bech32Prefix)
	if err != nil {
		return nil, errorsmod.Wrapf(errortypes.ErrInvalidAddress, "invalid address %s, %s", address, err.Error())
	}

	// safety check: shouldn't happen
	if err := sdk.VerifyAddressFormat(addressBz); err != nil {
		return nil, err
	}

	return sdk.AccAddress(addressBz), nil
}

// CreateAccAddressFromBech32 creates an AccAddress from a Bech32 string.
func CreateAccAddressFromBech32(address string, bech32prefix string) (addr sdk.AccAddress, err error) {
	if len(strings.TrimSpace(address)) == 0 {
		return sdk.AccAddress{}, fmt.Errorf("empty address string is not allowed")
	}

	bz, err := sdk.GetFromBech32(address, bech32prefix)
	if err != nil {
		return nil, err
	}

	err = sdk.VerifyAddressFormat(bz)
	if err != nil {
		return nil, err
	}

	return sdk.AccAddress(bz), nil
}

// GetIBCDenomAddress returns the address from the hash of the ICS20's DenomTrace Path.
func GetIBCDenomAddress(denom string) (common.Address, error) {
	if !strings.HasPrefix(denom, "ibc/") {
		return common.Address{}, ibctransfertypes.ErrInvalidDenomForTransfer.Wrapf("coin %s does not have 'ibc/' prefix", denom)
	}

	if len(denom) < 5 || strings.TrimSpace(denom[4:]) == "" {
		return common.Address{}, ibctransfertypes.ErrInvalidDenomForTransfer.Wrapf("coin %s is not a valid IBC voucher hash", denom)
	}

	// Get the address from the hash of the ICS20's DenomTrace Path
	bz, err := ibctransfertypes.ParseHexHash(denom[4:])
	if err != nil {
		return common.Address{}, ibctransfertypes.ErrInvalidDenomForTransfer.Wrap(err.Error())
	}

	return common.BytesToAddress(bz), nil
}

// ComputeIBCDenomTrace compute the ibc voucher denom trace associated with
// the portID, channelID, and the given a token denomination.
func ComputeIBCDenomTrace(
	portID, channelID,
	denom string,
) ibctransfertypes.DenomTrace {
	denomTrace := ibctransfertypes.DenomTrace{
		Path:      fmt.Sprintf("%s/%s", portID, channelID),
		BaseDenom: denom,
	}

	return denomTrace
}

// ComputeIBCDenom compute the ibc voucher denom associated to
// the portID, channelID, and the given a token denomination.
func ComputeIBCDenom(
	portID, channelID,
	denom string,
) string {
	return ComputeIBCDenomTrace(portID, channelID, denom).IBCDenom()
}

// SortSlice sorts a slice of any ordered type.
func SortSlice[T constraints.Ordered](slice []T) {
	sort.Slice(slice, func(i, j int) bool {
		return slice[i] < slice[j]
	})
}
