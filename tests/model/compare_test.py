# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals


def test_true(user):
    assert user == user


def test_false(user, tag_model):
    assert not user == tag_model


def test_false_because_not_model(user):
    string = 'i am a string and not an instance of Model'
    assert user != string
    assert string != user
