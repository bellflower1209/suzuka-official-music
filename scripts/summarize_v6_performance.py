"""Summarize paired local Lighthouse reports; never compare them to PSI as an A/B."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
from urllib.parse import urlparse

AUDITS = {
    'lcpMs': 'largest-contentful-paint', 'fcpMs': 'first-contentful-paint',
    'cls': 'cumulative-layout-shift', 'speedIndexMs': 'speed-index',
    'transferBytes': 'total-byte-weight', 'jsMs': 'bootup-time',
    'mainThreadMs': 'mainthread-work-breakdown', 'tbtMs': 'total-blocking-time',
}


def summarize(root):
    records, rejected, environments = [], [], {}
    for device in ('mobile', 'desktop'):
        for path in sorted((root / device).rglob('*.json')):
            value = json.loads(path.read_text())
            url = urlparse(value['requestedUrl'])
            if url.hostname != '127.0.0.1' or url.port not in (8880, 8882):
                raise ValueError('Unexpected measurement origin')
            if value.get('runtimeError') or value.get('runWarnings'):
                rejected.append({'file': path.relative_to(root).as_posix(),
                    'error': value.get('runtimeError'), 'warnings': value.get('runWarnings')})
                continue
            settings = value['configSettings']
            environment = {'lighthouseVersion': value['lighthouseVersion'],
                'browserUserAgent': value['environment']['hostUserAgent'],
                'settings': {k: settings[k] for k in ('formFactor', 'throttling', 'throttlingMethod',
                    'screenEmulation', 'disableStorageReset', 'disableFullPageScreenshot',
                    'blockedUrlPatterns', 'maxWaitForLoad')}}
            if settings['formFactor'] != device or device in environments and environments[device] != environment:
                raise ValueError('Mixed browser or measurement settings; do not combine these runs')
            environments[device] = environment
            audits = value['audits']
            items = audits['network-requests']['details']['items']
            images = [i for i in items if i.get('resourceType') == 'Image']
            css = [i for i in items if i.get('resourceType') == 'Stylesheet']
            hero = [i for i in images if '/assets/cinema/' in i['url'] or '/assets/baba-nova/' in i['url']][:1]
            amaterasu = [i for i in images if 'enomoto-mia-amaterasu-official-jacket.png' in i['url']
                         or '22dc21412a1af458c731-' in i['url']]
            durations = [i['networkEndTime'] - i['rendererStartTime'] for i in images
                         if i.get('finished') and i.get('networkEndTime') is not None]
            metric = audits['metrics']['details']['items'][0]
            record = {'device': device, 'route': url.path,
                'variant': 'before' if url.port == 8880 else 'after',
                'file': path.relative_to(root).as_posix(), 'fetchTime': value['fetchTime'],
                'score': value['categories']['performance']['score'] * 100,
                **{k: audits[a]['numericValue'] for k, a in AUDITS.items()},
                'requests': len(items), 'cssRequests': len(css), 'imageRequests': len(images),
                'imageTransferBytes': sum(i.get('transferSize', 0) for i in images),
                'maxImageDownloadMs': max(durations, default=0),
                'heroDownloadMs': max((i['networkEndTime'] - i['rendererStartTime'] for i in hero
                    if i.get('finished') and i.get('networkEndTime') is not None), default=0),
                'amaterasuRequests': len(amaterasu),
                'amaterasuResourceBytes': sum(i.get('resourceSize', 0) for i in amaterasu),
                'amaterasuSources': [urlparse(i['url']).path for i in amaterasu],
                'requestsBeforeObservedFCP': sum(i.get('rendererStartTime', float('inf')) <=
                    metric['observedFirstContentfulPaint'] for i in items),
                'incompleteImages': sum(not i.get('finished') for i in images)}
            records.append(record)
    groups = defaultdict(list)
    for r in records:
        groups[(r['device'], r['route'], r['variant'])].append(r)
    summaries = []
    numeric = ('score', *AUDITS, 'requests', 'cssRequests', 'imageRequests', 'imageTransferBytes',
               'maxImageDownloadMs', 'heroDownloadMs', 'amaterasuRequests', 'amaterasuResourceBytes',
               'requestsBeforeObservedFCP', 'incompleteImages')
    for (device, route, variant), data in sorted(groups.items()):
        summaries.append({'device': device, 'route': route, 'variant': variant, 'runs': len(data),
            'median': {k: statistics.median(r[k] for r in data) for k in numeric},
            'range': {k: [min(r[k] for r in data), max(r[k] for r in data)] for k in numeric}})
    return {'method': 'paired localhost HTTP/1.1 + gzip; cold browser cache; alternating A/B order',
        'limits': ['not comparable to the earlier public PSI score', 'no GA4 on localhost',
                   'protected audio requests blocked identically in both variants',
                   'loopback image download times are not cellular-network estimates'],
        'environments': environments, 'records': records, 'summaries': summaries, 'rejected': rejected}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = summarize(args.root)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'measurements': len(result['records']), 'groups': len(result['summaries']),
                      'rejected': len(result['rejected'])}))
