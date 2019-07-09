"""Translate midi messages between input/output devices."""

import signal
import sys
import time

import mido
from mido.ports import MultiPort
from rx.subjects import Subject
from rx import operators as ops

from utils import csv_dict_list


TRANSLATIONS_FILE = './mappings/mappings.csv'
translations = csv_dict_list(TRANSLATIONS_FILE)


def io_ports(midi_stream):
    """Create input/output ports and add incoming messages to the stream."""

    def input_message(msg):
        midi_stream.on_next(msg)

    input_names = mido.get_input_names()
    output_names = mido.get_output_names()
    print(f'input_names: {input_names}')
    print(f'output_names: {output_names}')
    inports = MultiPort(
        [mido.open_input(
            device, callback=input_message) for device in input_names])
    outports = MultiPort(
        [mido.open_output(device) for device in input_names])
    return inports, outports


def process_message(msg):
    """Process incoming message."""

    if msg.type == 'control_change':
        mtype = 'CC'
        value = msg.value
        control = msg.control
    elif msg.type == 'note_off':
        mtype = 'OFF'
        value = msg.velocity
        control = msg.note
    elif msg.type == 'note_on':
        mtype = 'ON'
        value = msg.velocity
        control = msg.note

    return {
        'type': mtype,
        'channel': msg.channel + 1,
        'control': control,
        'value': value,
        'msg': msg,
    }


def check_message(msg):
    """Check incoming message."""

    def check(t):
        return (
            t['type'] == msg['type'] and
            int(t['channel']) == msg['channel'] and
            int(t['control']) == msg['control']
        )

    return [(t, msg) for t in translations if check(t)]


def translate_message_list(msg_list):
    """Translate incoming message list."""

    return msg_list


def print_message(msg_list):
    """Print message."""

    if len(msg_list) == 0:
        return

    msg = msg_list[0]
    print('[{}] {}__{} => {}__{:<25}{}'.format(
        msg[0]['bank'],
        msg[0]['input-device'],
        msg[0]['description'],
        msg[0]['output-device'],
        msg[0]['o-description'],
        msg[1]['value'],
    ))


def main():
    """Main loop of the application."""

    def signal_handler(signal, frame):
        # print('\n' * 100)
        print('\033[H\033[J')
        print('Keyboard interupt detected')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    midi_stream = Subject()
    midi_stream.pipe(
        ops.map(lambda x: process_message(x)),
        ops.map(lambda x: check_message(x)),
        ops.map(lambda x: translate_message_list(x)),
    ).subscribe(print_message)

    io_ports(midi_stream)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()