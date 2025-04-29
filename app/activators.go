// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)
package app

import (
	"github.com/omini/omini/v20/app/eips"
	"github.com/omini/omini/v20/x/evm/core/vm"
)

// ominiActivators defines a map of opcode modifiers associated
// with a key defining the corresponding EIP.
var ominiActivators = map[string]func(*vm.JumpTable){
	"omini_0": eips.Enable0000,
	"omini_1": eips.Enable0001,
	"omini_2": eips.Enable0002,
}
