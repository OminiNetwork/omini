<!--
parent:
  order: false
-->

<div align="center">
  <h1> omini </h1>
</div>

<div align="center">
  <a href="https://github.com/omini/omini/releases/latest">
    <img alt="Version" src="https://img.shields.io/github/tag/omini/omini.svg" />
  </a>
  <a href="https://github.com/omini/omini/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/omini/omini.svg" />
  </a>
  <a href="https://pkg.go.dev/github.com/omini/omini">
    <img alt="GoDoc" src="https://godoc.org/github.com/omini/omini?status.svg" />
  </a>
  <a href="https://goreportcard.com/report/github.com/omini/omini">
    <img alt="Go report card" src="https://goreportcard.com/badge/github.com/omini/omini"/>
  </a>
</div>
<div align="center">
  <a href="https://discord.gg/omini">
    <img alt="Discord" src="https://img.shields.io/discord/809048090249134080.svg" />
  </a>
  <a href="https://github.com/omini/omini/actions?query=branch%3Amain+workflow%3ALint">
    <img alt="Lint Status" src="https://github.com/omini/omini/actions/workflows/lint.yml/badge.svg?branch=main" />
  </a>
  <a href="https://codecov.io/gh/omini/omini">
    <img alt="Code Coverage" src="https://codecov.io/gh/omini/omini/branch/main/graph/badge.svg" />
  </a>
  <a href="https://x.com/ominiOrg">
    <img alt="Follow omini on X" src="https://x.com/ominiOrg"/>
  </a>
</div>

## About

omini is a scalable, high-throughput Proof-of-Stake EVM blockchain
that is fully compatible and interoperable with Ethereum.
It's built using the [Cosmos SDK](https://github.com/cosmos/cosmos-sdk/)
which runs on top of the [CometBFT](https://github.com/cometbft/cometbft) consensus engine.

## Quick Start

To learn how omini works from a high-level perspective,
go to the [Protocol Overview](https://docs.omini.org/protocol) section of the documentation.
You can also check the instructions to [Run a Node](https://docs.omini.org/protocol/omini-cli#run-an-omini-node).

## Documentation

Our documentation is hosted in a [separate repository](https://github.com/omini/docs) and can be found at [docs.omini.org](https://docs.omini.org).
Head over there and check it out.

## Installation

For prerequisites and detailed build instructions
please read the [Installation](https://docs.omini.org/protocol/omini-cli) instructions.
Once the dependencies are installed, run:

```bash
make install
```

Or check out the latest [release](https://github.com/omini/omini/releases).

## Community

The following chat channels and forums are great spots to ask questions about omini:

- [omini X (Twitter)](https://x.com/ominiOrg)
- [omini Discord](https://discord.gg/omini)
- [omini Forum](https://commonwealth.im/omini)

## Contributing

Looking for a good place to start contributing?
Check out some
[`good first issues`](https://github.com/omini/omini/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22).

For additional instructions, standards and style guides, please refer to the [Contributing](./CONTRIBUTING.md) document.

## Careers

See our open positions on [our Careers page](https://omini.org/careers/).

## Licensing

Starting from April 21st, 2023, the omini repository will update its License
from GNU Lesser General Public License v3.0 (LGPLv3) to [omini Non-Commercial
License 1.0 (ENCL-1.0)](./LICENSE). This license applies to all software released from omini
version 13 or later, except for specific files, as follows, which will continue
to be licensed under LGPLv3:

- `x/erc20/keeper/proposals.go`
- `x/erc20/types/utils.go`

LGPLv3 will continue to apply to older versions ([<v13.0.0](https://github.com/omini/omini/releases/tag/v12.1.5))
of the omini repository. For more information see [LICENSE](./LICENSE).

> [!WARNING]
>
> **NOTE: If you are interested in using this software**
> email us at [os@omini.org](mailto:os@omini.org).

### SPDX Identifier

The following header including a license identifier in [SPDX](https://spdx.dev/learn/handling-license-info/)
short form has been added to all ENCL-1.0 files:

```go
// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)
```

Exempted files contain the following SPDX ID:

```go
// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:LGPL-3.0-only
```

### License FAQ

Find below an overview of the Permissions and Limitations of the omini Non-Commercial License 1.0.
For more information, check out the full ENCL-1.0 FAQ [here](./LICENSE_FAQ.md).

| Permissions                                                                                                                                                                  | Prohibited                                                                 |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| - Private Use, including distribution and modification<br />- Commercial use on designated blockchains<br />- Commercial use with omini permit (to be separately negotiated) | - Commercial use, other than on designated blockchains, without omini permit |
