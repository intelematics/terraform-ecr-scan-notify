#!/usr/bin/env python3
import boto3
import requests
import os
import json
import argparse

MAX_FINDINGS_TO_REPORT = 10

parser = argparse.ArgumentParser()
parser.add_argument("--ssm-parameter-name-config", default=os.getenv("SSM_PARAMETER_NAME_CONFIG"))
args = parser.parse_args()


def send_slack_message(msg, config):
    msg['channel'] = config['slack_channel']
    res = requests.post(config['slack_webhook_url'], json.dumps(msg))
    if 200 != res.status_code:
        raise Exception(res.content)


def lambda_handler(event, context):
    ecr_client = boto3.client('ecr')

    pages = ecr_client.get_paginator('describe_image_scan_findings').paginate(
        repositoryName=event['detail']['repository-name'],
        imageId={
            'imageDigest': event['detail']['image-digest'],
            'imageTag': event['detail']['image-tags'][0],
        },
    )

    scan_results = {}
    for page in pages:
        image_key = '%s:%s' % (page['repositoryName'], page['imageId']['imageTag'])
        if image_key not in scan_results:
            scan_results[image_key] = {
                'status': page['imageScanStatus']['status'],
                'digest': page['imageId']['imageDigest'],
                'findings': []
            }
        scan_results[image_key]['findings'] += page['imageScanFindings']['findings']

    for image_key in scan_results.keys():
        findings_details_uri = 'https://%s.console.aws.amazon.com/ecr/repositories/terraform/image/%s/scan-results' % (event['region'], scan_results[image_key]['digest'])

        findings_truncated_message = None
        if len(scan_results[image_key]['findings']) > MAX_FINDINGS_TO_REPORT:
            findings_truncated_message = '*MORE THAN %s VULNERABILITIES FOUND*' % MAX_FINDINGS_TO_REPORT
            scan_results[image_key]['findings'] = scan_results[image_key]['findings'][:MAX_FINDINGS_TO_REPORT]

        msg = {
            'text': '*ECR Image Scan results for %s - %s*' % (image_key, scan_results[image_key]['status']),
            'attachments': [
                {
                    'type': 'section',
                    'fields': [
                        {
                            'title': 'Name',
                            'value': '<%s|%s> %s' % (finding.get('uri'), finding.get('name'), finding.get('severity')),
                            'short': False,
                        },
                        {
                            'title': 'Description',
                            'value': finding.get('description', 'none available'),
                            'short': False,
                        },
                        {
                            'title': 'Attributes',
                            'value': '\n'.join(['%s = %s' % (a['key'], a['value']) for a in finding.get('attributes')]),
                            'short': False,
                        },
                    ]
                } for finding in scan_results[image_key]['findings']
            ]
            +
            [
                {
                    'text': findings_truncated_message,
                }
            ]
            +
            [
                {
                    'text': '<%s|%s>' % (findings_details_uri, 'View all Findings'),
                }
            ]
        }

        if not scan_results[image_key]['findings']:
            msg['attachments'] = [
                {'text': 'No vulnerabilities found'}
            ]

        ssm_client = boto3.client('ssm')
        config = json.loads(ssm_client.get_parameter(Name=args.ssm_parameter_name_config, WithDecryption=True)['Parameter']['Value'])

        send_slack_message(msg, config)
