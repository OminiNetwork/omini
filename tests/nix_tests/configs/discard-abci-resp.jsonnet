local config = import 'default.jsonnet';

config {
  'omini_9002-1'+: {
    config+: {
      storage: {
        discard_abci_responses: true,
      },
    },
  },
}
