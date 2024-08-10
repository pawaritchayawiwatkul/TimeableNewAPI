from rest_framework import serializers
from teacher.models import UnavailableTimeOneTime
import random
import string
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import pathlib
from uuid import uuid4
import boto3

    
def generate_unique_code(length=8):
    """Generate a unique random code."""
    characters = string.ascii_letters + string.digits
    code = ''.join(random.choice(characters) for _ in range(length))
    return code


def merge_schedule(validated_data, unavailables):
    new_start = validated_data['start']
    new_stop = validated_data['stop']
    overlap = []
    for interval in unavailables:
        start = interval.start
        stop = interval.stop
        _ = False
        if start > new_stop:
            # print('1')
            continue
        elif stop < new_start:
            # print('2')
            continue
        if start <= new_start:
            # print('3')
            new_start = start
            _ = True
        if stop >= new_stop:
            # print('4')
            new_stop = stop
            _ = True
        overlap.append(interval)
        # print('5')

    validated_data['start'] = new_start
    validated_data['stop'] = new_stop
    return validated_data, overlap

def gen_query_otblock(data):
    return UnavailableTimeOneTime(**data)

def split_at_reg(rblock, otblock):
    blocks = []
    s, f = otblock['start'], otblock['stop']
    if rblock:
        otblock['stop'] = rblock[0]['start']
        if not otblock['stop'] == otblock['start']:
            blocks.append(gen_query_otblock(otblock))
        for i in range(1, len(rblock)):
            otblock['start'] = rblock[i - 1]['stop']
            otblock['stop'] = rblock[i]['start']
            blocks.append(gen_query_otblock(otblock))
        otblock['start'] = rblock[-1]['stop']
        otblock['stop'] = f
        if not otblock['stop'] == otblock['start']:
            blocks.append(gen_query_otblock(otblock))
        return blocks
    else:
        return [gen_query_otblock(otblock), ]
    