// Copyright Tharsis Labs Ltd.(omini)
// SPDX-License-Identifier:ENCL-1.0(https://github.com/omini/omini/blob/main/LICENSE)
package ibctesting

import (
	"bytes"
	"fmt"

	channeltypes "github.com/cosmos/ibc-go/v8/modules/core/04-channel/types"
	ibctesting "github.com/cosmos/ibc-go/v8/testing"
)

// Path contains two endpoints representing two chains connected over IBC
type Path struct {
	EndpointA *Endpoint
	EndpointB *Endpoint
}

// NewPath constructs an endpoint for each chain using the default values
// for the endpoints. Each endpoint is updated to have a pointer to the
// counterparty endpoint.
func NewPath(chainA, chainB *ibctesting.TestChain) *Path {
	endpointA := NewDefaultEndpoint(chainA)
	endpointB := NewDefaultEndpoint(chainB)

	endpointA.Counterparty = endpointB
	endpointB.Counterparty = endpointA

	return &Path{
		EndpointA: endpointA,
		EndpointB: endpointB,
	}
}

// SetChannelOrdered sets the channel order for both endpoints to ORDERED.
func (path *Path) SetChannelOrdered() {
	path.EndpointA.ChannelConfig.Order = channeltypes.ORDERED
	path.EndpointB.ChannelConfig.Order = channeltypes.ORDERED
}

// RelayPacket attempts to relay the packet first on EndpointA and then on EndpointB
// if EndpointA does not contain a packet commitment for that packet. An error is returned
// if a relay step fails or the packet commitment does not exist on either endpoint.
func (path *Path) RelayPacket(packet channeltypes.Packet) error {
	pc := path.EndpointA.Chain.App.GetIBCKeeper().ChannelKeeper.GetPacketCommitment(path.EndpointA.Chain.GetContext(), packet.GetSourcePort(), packet.GetSourceChannel(), packet.GetSequence())
	if bytes.Equal(pc, channeltypes.CommitPacket(path.EndpointA.Chain.App.AppCodec(), packet)) {

		// packet found, relay from A to B
		if err := path.EndpointB.UpdateClient(); err != nil {
			return err
		}

		res, err := path.EndpointB.RecvPacketWithResult(packet)
		if err != nil {
			return err
		}

		ack, err := ibctesting.ParseAckFromEvents(res.GetEvents().ToABCIEvents())
		if err != nil {
			return err
		}

		return path.EndpointA.AcknowledgePacket(packet, ack)
	}

	pc = path.EndpointB.Chain.App.GetIBCKeeper().ChannelKeeper.GetPacketCommitment(path.EndpointB.Chain.GetContext(), packet.GetSourcePort(), packet.GetSourceChannel(), packet.GetSequence())
	if bytes.Equal(pc, channeltypes.CommitPacket(path.EndpointB.Chain.App.AppCodec(), packet)) {

		// packet found, relay B to A
		if err := path.EndpointA.UpdateClient(); err != nil {
			return err
		}

		res, err := path.EndpointA.RecvPacketWithResult(packet)
		if err != nil {
			return err
		}

		ack, err := ibctesting.ParseAckFromEvents(res.GetEvents().ToABCIEvents())
		if err != nil {
			return err
		}

		return path.EndpointB.AcknowledgePacket(packet, ack)
	}

	return fmt.Errorf("packet commitment does not exist on either endpoint for provided packet")
}
