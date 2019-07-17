"""Functions used in the main appplication streams."""
from typing import Any, Dict

from .constants import STANDARD_MESSAGES
from .store import store
from .utils import reset_banks_and_controls
from .utils import send_message


def create_stream_data(midi) -> Dict[str, Any]:
    """Create items in the steam to be passed down."""
    return {
        'msg': {},
        'midi': midi,
        'translations': [],
        'store': store,
    }


def process_midi(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming message."""
    midi = data['midi']
    try:
        channel = midi.channel + 1
    except AttributeError:
        channel = None
    try:
        status, level = STANDARD_MESSAGES[midi.type](midi)
    except KeyError:
        status, level = None, None
    data['msg'] = {
        'channel': channel,
        'status': status,
        'level': level,
    }
    return data


def check_mappings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check incoming message for matches in mappings."""

    def check(mapping):
        return (
            mapping['type'] == getattr(data['midi'], 'type') and
            int(mapping['channel']) == data['msg']['channel'] and
            int(mapping['control']) == data['msg']['status'] and
            (int(mapping['bank']) == 0 or
                int(mapping['bank']) == data['store'].get('active_bank'))
        )

    mappings = data['store'].get('mappings')
    data['translations'] = [mapping for mapping in mappings if check(mapping)]
    return data


def log(data: Dict[str, Any]) -> None:
    """Log messages to console."""
    for translation in data['translations']:
        print('[{}] {}__{} => {}__{:<25} {}'.format(
            data['store'].get('active_bank'),
            translation['input-device'],
            translation['description'],
            translation['output-device'],
            translation['o-description'],
            data['msg']['level'],
        ))


def translate_and_send(data: Dict[str, Any]) -> Dict[str, Any]:
    """Translate messages and send."""
    for translation in data['translations']:
        if translation['o-type'] == 'bank_change':
            data['store'].update('active_bank', int(translation['o-control']))
            reset_banks_and_controls(data)
        else:
            translation['memory'] = data['msg']['level']
            send_message({
                'type': translation['o-type'],
                'channel': int(translation['o-channel']) - 1,
                'status': translation['o-control'],
                'level': data['msg']['level'],
            })
    return data
