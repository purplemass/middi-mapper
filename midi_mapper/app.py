"""Translate midi messages between input/output devices."""
import signal
import sys
import time

from rx.subject import Subject
from rx import operators as ops

from .mappings import import_mappings
from .store import store
from .stream import (
    check_mappings,
    create_stream_data,
    log,
    process_midi,
    translate_and_send,
)
from .utils import (
    set_initial_bank,
    io_ports,
)


def run() -> None:
    """Update store, create streams and run the main loop."""

    midi_stream = Subject()

    store.update('mappings', import_mappings())
    store.update('midi_stream', midi_stream)

    io_ports()

    translated_stream = midi_stream.pipe(
        ops.map(lambda x: create_stream_data(x)),
        ops.map(lambda x: process_midi(x)),
        ops.map(lambda x: check_mappings(x)),
        ops.filter(lambda x: x['translations']),
    )

    translated_stream.pipe(
        ops.do_action(lambda x: log(x)),
        ops.map(lambda x: translate_and_send(x)),
    ).subscribe()

    # send initial bank to reset controller
    set_initial_bank(8, midi_stream)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    """Add keyboard interupt handler and run application."""

    def signal_handler(signal, frame) -> None:
        print('\033[H\033[J')
        print('Keyboard interupt detected')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    run()
