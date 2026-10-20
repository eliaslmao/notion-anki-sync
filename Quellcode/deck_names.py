"""Readable deck labels; topic identity lives in note metadata, not labels."""
import re


def resolve(desired, existing, deck_names):
    occupied = {name.casefold():None for name in deck_names}
    hints = {}
    for old in existing.values():
        root, topics = old.get('root'), old.get('topics', [])
        if not root or not old.get('managed'):
            continue
        path, ids = root, ()
        for topic in topics:
            ids += (topic['id'],)
            path += '::' + topic['name']
            key = (root.casefold(),ids)
            occupied[path.casefold()] = key
            hints[key] = topic
    nodes = {}
    for value in desired.values():
        root, ids = value.get('root'), ()
        if not root:
            continue
        for topic in value.get('topics', []):
            ids += (topic['id'],)
            nodes[(root.casefold(),ids)] = (root,topic)
    resolved = {}
    for key,(root,topic) in sorted(nodes.items(),key=lambda item:(len(item[0][1]),item[0])):
        parent_key = (key[0],key[1][:-1])
        parent = resolved[parent_key][0] if key[1][:-1] else root
        title = topic['title']
        hint = hints.get(key)
        display = hint['name'] if hint and hint['title'] == title else title
        number = 2
        while (parent+'::'+display).casefold() in occupied and occupied[(parent+'::'+display).casefold()] != key:
            display = f'{title} ({number})'
            number += 1
        path = parent+'::'+display
        occupied[path.casefold()] = key
        resolved[key] = (path,display)
    for value in desired.values():
        root, ids = value.get('root'), ()
        if not root:
            continue
        for topic in value.get('topics', []):
            ids += (topic['id'],)
            path, display = resolved[(root.casefold(),ids)]
            topic['name'] = display
            value['deck'] = path


def old_decks(existing, active, roots):
    """Only old ID-suffixed topic paths evidenced by selected managed notes."""
    candidates = set()
    for old in existing.values():
        if not old.get('managed') or old['page'] not in active:
            continue
        for root in roots:
            if not old['deck'].startswith(root+'::'):
                continue
            path = root
            for part in old['deck'][len(root)+2:].split('::'):
                path += '::' + part
                if re.search(r' \[[0-9a-f]{32}\]$',part):
                    candidates.add(path)
    return candidates
