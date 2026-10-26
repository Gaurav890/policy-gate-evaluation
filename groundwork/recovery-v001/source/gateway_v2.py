"""Bounded, recorded retries with fixed routing and optional serial tool calls."""
import json
import math
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from gateway_budget import ROOT, MODELS, Budget, BudgetExceeded, GatewayError, NoRedirect, load_study_key, write_json


def retry_delay(header, attempt):
    if header:
        try:
            value = float(header)
            if math.isfinite(value) and value >= 0:
                return value
        except ValueError:
            try:
                date = parsedate_to_datetime(header)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                return max(0, (date-datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return 2 ** (attempt + 1)


class Gateway:
    def __init__(self, budget=None, serial_tools=False, opener=None, sleep=time.sleep):
        self.budget = budget or Budget()
        self.key = load_study_key()
        self.records_dir = ROOT / 'groundwork/api_records'
        self.serial_tools = serial_tools
        self.opener = opener or urllib.request.build_opener(NoRedirect)
        self.sleep = sleep

    def complete(self, model, messages, *, tools=None, max_tokens=2048, role='actor', episode='access', response_format=None):
        cfg = MODELS[model]
        payload = {'model':cfg['id'], 'messages':messages, 'max_tokens':max_tokens,
                   'reasoning':{'effort':cfg['effort']}, 'providerOptions':{'gateway':{'only':[cfg['route']]}}}
        if tools:
            payload.update(tools=tools, tool_choice='auto')
            if self.serial_tools:
                payload['parallel_tool_calls'] = False
        if response_format:
            payload['response_format'] = response_format
        logical = uuid.uuid4().hex
        for attempt in range(3):
            reservation = self.budget.reserve(payload, cfg, {'role':role,'episode':episode,
                'logical_request_id':logical,'attempt':attempt+1,'transport_version':2})
            record = {**reservation,'status':'reserved','request':payload}
            path = self.records_dir / (reservation['request_id']+'.json')
            write_json(path,record)
            start = time.monotonic()
            req = urllib.request.Request('https://ai-gateway.vercel.sh/v1/chat/completions',
                data=json.dumps(payload).encode(), headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},method='POST')
            try:
                with self.opener.open(req,timeout=55) as response:
                    data=json.load(response)
            except Exception as exc:
                status=getattr(exc,'code',None)
                record.update(status='request_failed',http_status=status,error_type=type(exc).__name__,elapsed_s=time.monotonic()-start)
                header=None
                if isinstance(exc,urllib.error.HTTPError):
                    header=exc.headers.get('retry-after')
                    # Preserve bounded diagnostics after removing the exact study secret.
                    body=exc.read(8192).decode('utf-8',errors='replace').replace(self.key,'[REDACTED]')
                    record['error_body_redacted']=body
                    record['response_headers']={k:exc.headers[k].replace(self.key,'[REDACTED]') for k in ('retry-after','x-request-id','x-vercel-id') if exc.headers.get(k)}
                delay=retry_delay(header,attempt)
                retry=status in {429,503} and attempt<2 and delay<=45
                record.update(will_retry=retry,retry_delay_s=delay if retry else None)
                write_json(path,record)
                if retry:
                    self.sleep(delay)
                    continue
                raise GatewayError(f'HTTP {status}; attempt {attempt+1}; diagnostics recorded; reservation retained') from None
            usage=data.get('usage',{})
            record.update(status='received',response=data,elapsed_s=time.monotonic()-start)
            p,c=usage.get('prompt_tokens'),usage.get('completion_tokens')
            write_json(path,record)
            if not isinstance(p,int) or not isinstance(c,int):
                raise GatewayError('Missing usage; stopped')
            estimate=(p*cfg['input']+c*cfg['output'])/1_000_000
            record.update(status='ok',uncached_cost_estimate_usd=estimate)
            write_json(path,record)
            reported=usage.get('cost',estimate)
            if max(estimate,float(reported))>reservation['reserved_usd']:
                raise BudgetExceeded('Observed cost exceeded reservation; stopped')
            try:
                choice=data['choices'][0]
                message=choice['message']
            except (KeyError,IndexError,TypeError):
                raise GatewayError('Malformed response') from None
            if choice.get('finish_reason')=='length':
                raise GatewayError('Output truncated; no silent retry')
            if not message.get('content') and not message.get('tool_calls'):
                raise GatewayError('Empty response')
            if self.serial_tools and len(message.get('tool_calls') or [])>1:
                raise GatewayError('Provider violated serial-tool setting; stopped before tool execution')
            return message,record
