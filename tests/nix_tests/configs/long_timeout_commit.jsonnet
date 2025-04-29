local default = import 'default.jsonnet';

default {
  'omini_9002-1'+: {
    config+: {
      consensus+: {
        timeout_commit: '5s',
      },
    },
  },
}
