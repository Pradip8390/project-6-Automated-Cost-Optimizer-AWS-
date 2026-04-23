import boto3
from datetime import datetime, timedelta

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    instances = ec2.describe_instances()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']

            if state != 'running':
                continue

            metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(minutes=30),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )

            datapoints = metrics['Datapoints']

            if len(datapoints) == 0:
                continue

            avg_cpu = sum([point['Average'] for point in datapoints]) / len(datapoints)

            print(f"{instance_id} CPU: {avg_cpu}")

            if avg_cpu < 100:
                print(f"Stopping idle instance: {instance_id}")
                ec2.stop_instances(InstanceIds=[instance_id])