#!/usr/bin/python
"""
Take a git webhook as input and post a message to MS Teams
"""

import json
import os
import sys

import pymsteams

## local module to define WEBHOOK_URL string for teams incoming webhook connector
from local_defs import WEBHOOK_URL

def escape_markdown(a_string):
    """
    Escape special markdown characters in a string.
    Args:
        a_string: string to escape
    Returns: escaped string
    """
    escape_chars = ['`', '\\', '*', '_', '#']
    return ''.join('\\' + c if c in escape_chars else c for c in a_string)

def format_title(event_type, req_data):
    """
    Format title for message.
    Args:
        event_type: GitHub event type
        req_data: dictionary of event json payload
    Returns: title string
    """
    default_title = "GitHub event: {event_type} in {repository[full_name]}" \
                      .format(event_type=event_type, **req_data)
    return default_title

def add_body(teams_message, event_type, req_data):
    """
    Add body to message.
    Args:
        teams_message: MS Teams message object
        event_type: GutHub event type
        req_data: dictionary of event json payload
    Returns: whether to send message.
    """
    ## note: you need \n\n for a newline in MS Teams markdown
    desc_fmt = event_type
    do_send = True
    if event_type == "commit_comment":
        desc_fmt = ("{comment[user][login]} commented on {comment[commit_id]} "
                    "in {repository[full_name]}\n\n{comment[body]}")
    if event_type == "create":
        desc_fmt = "{sender[login]} created {ref_type} ({ref}) in {repository[full_name]}"
    if event_type == "issue_comment":
        desc_fmt = ("{sender[login]} commented on issue #{issue[number]} "
                    "in {repository[full_name]}\n\n"
                    " Title: {issue[title]}\n\n{comment[body]}")
        teams_message.addLinkButton("Issue", "{issue[html_url]}".format(**req_data))
        teams_message.addLinkButton("Comment", "{comment[html_url]}".format(**req_data))
    if event_type == "issues":
        desc_fmt = ("{sender[login]} {action} issue #{issue[number]} "
                    "in {repository[full_name]}\n\nTitle: {issue[title]}\n\n"
                    "--\n\n{issue[body]}")
        teams_message.addLinkButton("Issue", "{issue[html_url]}".format(**req_data))
        if req_data['action'] not in ['opened', 'reopened', 'closed', 'edited', 'deleted']:
            do_send = False
    if event_type == "project_card":
        desc_fmt = ("{sender[login]} {action} card note {project_card[note]} "
                    "in {repository[full_name]}")
    if event_type == "pull_request":
        desc_fmt = ("{sender[login]} {action} pull #{pull_request[number]} "
                    "in {repository[full_name]}\n\n"
                    "Title: {pull_request[title]}\n\n"
                    "Merge: {pull_request[head][repo][full_name]}:{pull_request[head][ref]}"
                    "into {pull_request[base][repo][full_name]}:{pull_request[base][ref]}")
        teams_message.addLinkButton("Pull Request", "{pull_request[html_url]}".format(**req_data))
        if req_data['action'] not in ['opened', 'reopened', 'closed', 'edited']:
            do_send = False
    if event_type == "pull_request_review":
        desc_fmt = ("{sender[login]} {action} {review[state]} "
                    "review on pull #{pull_request[number]} in {repository[full_name]}")
    if event_type == "pull_request_review_comment":
        desc_fmt = ("{comment[user][login]} {action} comment "
                    "on pull #{pull_request[number]} in {repository[full_name]}")
    if event_type == "push":
        desc_fmt = "{pusher[name]} pushed to {ref} in {repository[full_name]}"
        teams_message.addLinkButton("Compare", "{compare}".format(**req_data))
    desc = escape_markdown(desc_fmt.format(**req_data))
    teams_message.text(desc)
    return do_send

def build_and_send(event_type, req_body, webhook_url, test=False):
    """
    build and send message to teams.
    Args:
        event_type: GutHub event type
        req_data: dictionary of event json payload
        webhook_url: MS Teams incoming webhook connector URL
        test: whether we are in test mode
    """
    req_data = json.loads(req_body)
    teams_message = pymsteams.connectorcard(webhook_url)
    title = format_title(event_type, req_data)
    teams_message.title(title)
    do_send = add_body(teams_message, event_type, req_data)
    if test:
        teams_message.printme()
    elif do_send:
        teams_message.send()

if __name__ == "__main__":
    ## extract paameters from http POST request
    CONTENT_LEN = int(os.environ["CONTENT_LENGTH"])
    EVENT_TYPE = os.environ["HTTP_X_GITHUB_EVENT"]
    REQ_BODY = sys.stdin.read(CONTENT_LEN)
    build_and_send(EVENT_TYPE, REQ_BODY, WEBHOOK_URL)

    print("Content-Type: text/plain")
    print("")
