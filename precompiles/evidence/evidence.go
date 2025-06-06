// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)

package evidence

import (
	"embed"
	"fmt"

	evidencekeeper "cosmossdk.io/x/evidence/keeper"

	"cosmossdk.io/log"
	storetypes "cosmossdk.io/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	authzkeeper "github.com/cosmos/cosmos-sdk/x/authz/keeper"
	"github.com/ethereum/go-ethereum/accounts/abi"
	"github.com/ethereum/go-ethereum/common"

	cmn "github.com/omini/omini/v20/precompiles/common"
	"github.com/omini/omini/v20/x/evm/core/vm"
	evmtypes "github.com/omini/omini/v20/x/evm/types"
)

var _ vm.PrecompiledContract = &Precompile{}

// Embed abi json file to the executable binary. Needed when importing as dependency.
//
//go:embed abi.json
var f embed.FS

// Precompile defines the precompiled contract for evidence.
type Precompile struct {
	cmn.Precompile
	evidenceKeeper evidencekeeper.Keeper
}

// LoadABI loads the evidence ABI from the embedded abi.json file
// for the evidence precompile.
func LoadABI() (abi.ABI, error) {
	return cmn.LoadABI(f, "abi.json")
}

// NewPrecompile creates a new evidence Precompile instance as a
// PrecompiledContract interface.
func NewPrecompile(
	evidenceKeeper evidencekeeper.Keeper,
	authzKeeper authzkeeper.Keeper,
) (*Precompile, error) {
	abi, err := LoadABI()
	if err != nil {
		return nil, err
	}

	p := &Precompile{
		Precompile: cmn.Precompile{
			ABI:                  abi,
			AuthzKeeper:          authzKeeper,
			KvGasConfig:          storetypes.KVGasConfig(),
			TransientKVGasConfig: storetypes.TransientGasConfig(),
			ApprovalExpiration:   cmn.DefaultExpirationDuration, // should be configurable in the future.
		},
		evidenceKeeper: evidenceKeeper,
	}

	// SetAddress defines the address of the evidence precompiled contract.
	p.SetAddress(common.HexToAddress(evmtypes.EvidencePrecompileAddress))

	return p, nil
}

// RequiredGas calculates the precompiled contract's base gas rate.
func (p Precompile) RequiredGas(input []byte) uint64 {
	// NOTE: This check avoid panicking when trying to decode the method ID
	if len(input) < 4 {
		return 0
	}
	methodID := input[:4]

	method, err := p.MethodById(methodID)
	if err != nil {
		// This should never happen since this method is going to fail during Run
		return 0
	}

	return p.Precompile.RequiredGas(input, p.IsTransaction(method))
}

// Run executes the precompiled contract evidence methods defined in the ABI.
func (p Precompile) Run(evm *vm.EVM, contract *vm.Contract, readOnly bool) (bz []byte, err error) {
	ctx, stateDB, snapshot, method, initialGas, args, err := p.RunSetup(evm, contract, readOnly, p.IsTransaction)
	if err != nil {
		return nil, err
	}

	// This handles any out of gas errors that may occur during the execution of a precompile tx or query.
	// It avoids panics and returns the out of gas error so the EVM can continue gracefully.
	defer cmn.HandleGasError(ctx, contract, initialGas, &err)()

	switch method.Name {
	// evidence transactions
	case SubmitEvidenceMethod:
		bz, err = p.SubmitEvidence(ctx, evm.Origin, contract, stateDB, method, args)
	// evidence queries
	case EvidenceMethod:
		bz, err = p.Evidence(ctx, method, args)
	case GetAllEvidenceMethod:
		bz, err = p.GetAllEvidence(ctx, method, args)
	default:
		return nil, fmt.Errorf(cmn.ErrUnknownMethod, method.Name)
	}

	if err != nil {
		return nil, err
	}

	cost := ctx.GasMeter().GasConsumed() - initialGas

	if !contract.UseGas(cost) {
		return nil, vm.ErrOutOfGas
	}

	if err := p.AddJournalEntries(stateDB, snapshot); err != nil {
		return nil, err
	}

	return bz, nil
}

// IsTransaction checks if the given method name corresponds to a transaction or query.
//
// Available evidence transactions are:
// - SubmitEvidence
func (Precompile) IsTransaction(method *abi.Method) bool {
	switch method.Name {
	case SubmitEvidenceMethod:
		return true
	default:
		return false
	}
}

// Logger returns a precompile-specific logger.
func (p Precompile) Logger(ctx sdk.Context) log.Logger {
	return ctx.Logger().With("evm extension", "evidence")
}
