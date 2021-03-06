from huey.contrib.djhuey import task
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
import json
from asgiref.sync import async_to_sync

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

from .helpers import get_player_from_code, handle_bid
from .messages import MatchMessage

@task()
def automated_bid(code, round_number):
    player = get_player_from_code(code)
    session_code = player.participant.session.code + str(player.group.id_in_subsession)
    logging_info = 'automated_bid: round_number: {}, player_id: {}, code: {}, value: {}, display_id: {}, call_round_number: {}, is_bot: {}'.format(player.round_number, player.id, code, player.last_offer, player.display_id, round_number, player.participant.vars['is_bot'])
    logger.info(logging_info)
    if 'is_bot' in player.participant.vars and player.participant.vars['is_bot'] and player.match_with is None and player.last_offer is None and player.round_number is round_number:
        player.is_bot = True
        player.save()

        bid_info = {
            "type": "action.value." + player.participant.vars["role"],
            "player": player,
            "value": player.money if player.participant.vars["role"] == "buyer" else player.cost,
            "optionalPlayerId": None
        }
        responses = handle_bid(bid_info, is_bot=True)
        responses = [responses] if isinstance(responses, str) else responses
        for response in responses:
            async_to_sync(channel_layer.group_send)(session_code, {
                "text": json.dumps(response)
            })

        logger.info("automated bid for %s", code)
