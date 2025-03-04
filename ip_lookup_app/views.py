
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import AWSSubnet, AWSRouteTable, AWSEC2Instance,VPCEndpoint, AWSSecurityGroup, Route53Record,AWSVPC, AWSElasticIP, AzureSubnet, AzureRouteTable, AzureVirtualNetwork, AzureVnet
from .serializers import AWSSubnetSerializer, AWSVpcEndpointSerializer, AWSEC2InstanceSerializer,AWSRoute53RecordSerializer, AWSElasticIPSerializer, AWSSecurityGroupSerializer, AWSRouteTableSerializer, AWSVPCSerializer, AzureSubnetSerializer, AzureRouteTableSerializer, AzureVirtualNetworkSerializer, AzureVnetSerializer
import ipaddress
from django.http import JsonResponse

import logging,json
import traceback

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class IPLookupView(APIView):
    def get(self, request):
        ip = request.query_params.get('ip')
        # 如果没有 ip => 返回 JSON 错误, 而不是渲染模板
        if not ip:
            return JsonResponse({'error': 'No IP parameter provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ip_obj = ipaddress.ip_network(ip, strict=False)
        except ValueError:
            logger.error(f"Invalid IP address or range: {ip}")
            return JsonResponse({'error': 'Invalid IP address or range'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info("Checking EC2 instances...")

        from .models import AWSEC2Instance, AWSSubnet, AWSVPC
        # 优先查询 EC2
        for ec2 in AWSEC2Instance.objects.all():
            try:
                # 处理 private_ips / public_ips
                ec2_ips = eval(ec2.private_ips) if isinstance(ec2.private_ips, str) else ec2.private_ips
                if not isinstance(ec2_ips, list):
                    ec2_ips = [ec2_ips]

                ec2_public_ips = eval(ec2.public_ips) if isinstance(ec2.public_ips, str) else ec2.public_ips
                if not isinstance(ec2_public_ips, list):
                    ec2_public_ips = [ec2_public_ips]

                combined_ips = ec2_ips + ec2_public_ips
                for ec2_ip in combined_ips:
                    try:
                        ec2_ip_obj = ipaddress.ip_address(ec2_ip)
                    except:
                        continue
                    if ec2_ip_obj in ip_obj:
                        # 找到匹配 => 构造结果
                        subnet_cidr = ""
                        subnet_name_val = ""
                        vpc_id_val = ec2.vpc_id
                        vpc_name_val = ""

                        # 查关联子网
                        subnet_rec = AWSSubnet.objects.filter(subnet_id=ec2.subnet_id).first()
                        if subnet_rec:
                            subnet_cidr = subnet_rec.ipv4_cidr
                            subnet_name_val = subnet_rec.name
                            if subnet_rec.vpc:
                                parts = subnet_rec.vpc.split('|')
                                if len(parts) == 2:
                                    vpc_id_val, vpc_name_val = parts
                                else:
                                    # fallback
                                    pass
                            else:
                                # 如果 awssubnet.vpc 为空 => 尝试 AWSVPC
                                try:
                                    vpc_rec = AWSVPC.objects.get(vpc_id=ec2.vpc_id)
                                    vpc_id_val = vpc_rec.vpc_id
                                    vpc_name_val = vpc_rec.name
                                except:
                                    pass

                        result = {
                            'cloud': 'tasks',
                            'type': 'EC2',
                            'instance_id': ec2.instance_id,
                            'instance_name': ec2.name,
                            'private_ips': ec2_ips,
                            'public_ips': ec2_public_ips,
                            'vpc_id': vpc_id_val,
                            'vpc_name': vpc_name_val,
                            'subnet_id': ec2.subnet_id,
                            'subnet_name': subnet_name_val,
                            'subnet_cidr': subnet_cidr,
                            'security_groups': [sg.group_id for sg in ec2.security_groups.all()],
                            'instance_type': ec2.instance_type,
                            'state': ec2.state,
                            'region': ec2.region,
                        }

                        # 若需 security_groups_info, 在此补充
                        # =========== 新增：组装 security_groups_detail ===========
                        sg_details = []
                        for sg_obj in ec2.security_groups.all():
                            # 安全组基本信息
                            sg_info = {
                                'group_id': sg_obj.group_id,
                                'group_name': sg_obj.group_name,
                                'vpc_id': sg_obj.vpc_id,
                                'description': sg_obj.description,
                                'owner': sg_obj.owner,
                            }

                            # inbound/outbound 规则
                            inbound_list = []
                            outbound_list = []

                            # 假设 AWSSecurityGroupRule 有 direction='inbound'/'outbound'
                            for rule in sg_obj.rules.filter(direction='inbound'):
                                inbound_list.append({
                                    'ip_protocol': rule.ip_protocol,
                                    'from_port': rule.from_port,
                                    'to_port': rule.to_port,
                                    'source': rule.cidr_ipv4,
                                    'rule_type': rule.rule_type,
                                    'rule_description': rule.rule_description,
                                })
                            for rule in sg_obj.rules.filter(direction='outbound'):
                                outbound_list.append({
                                    'ip_protocol': rule.ip_protocol,
                                    'from_port': rule.from_port,
                                    'to_port': rule.to_port,
                                    'source': rule.cidr_ipv4,
                                    'rule_type': rule.rule_type,
                                    'rule_description': rule.rule_description,
                                })

                            sg_info['inbound_rules'] = inbound_list
                            sg_info['outbound_rules'] = outbound_list

                            sg_details.append(sg_info)

                        # 把安全组详细信息放入 result
                        result['security_groups_detail'] = sg_details

                        logger.info(f"Found EC2 match: {result}")
                        return JsonResponse(result, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Error processing EC2 instance {ec2.instance_id}: {e}", exc_info=True)
                continue

        logger.info("No EC2 match found. Checking tasks subnets...")
        # 没匹配 => 查子网
        for subnet in AWSSubnet.objects.all():
            try:
                subnet_obj = ipaddress.ip_network(subnet.ipv4_cidr, strict=False)
                if ip_obj.subnet_of(subnet_obj):
                    parts = subnet.vpc.split('|') if subnet.vpc else []
                    vpc_id = ""
                    vpc_name = ""
                    if len(parts) == 2:
                        vpc_id, vpc_name = parts

                    route_table_id, route_table_name = subnet.route_table.split('|')
                    result = {
                        'cloud': 'tasks',
                        'type': 'Subnet',
                        'vpc_id': vpc_id,
                        'vpc_name': vpc_name,
                        'subnet_name': subnet.name,
                        'subnet_id': subnet.subnet_id,
                        'ipv4_cidr': subnet.ipv4_cidr,
                        'route_table': route_table_name
                    }
                    logger.info(f"Found match in tasks subnet: {subnet.name}, Result: {result}")
                    return JsonResponse(result, status=status.HTTP_200_OK)
            except ValueError:
                logger.error(f"Invalid CIDR in AWSSubnet: {subnet.ipv4_cidr}")
                continue

        logger.info("No match found in EC2 or tasks subnets.")
        return JsonResponse({'error': 'IP not found. Data synchronization triggered.'},
                            status=status.HTTP_404_NOT_FOUND)




class AWSDataView(APIView):
    def get(self, request, table):
        if table == 'vpc':
            vpcs = AWSVPC.objects.all()
            serializer = AWSVPCSerializer(vpcs, many=True)
        elif table == 'subnet':
            subnets = AWSSubnet.objects.all()
            serializer = AWSSubnetSerializer(subnets, many=True)
        elif table == 'route-table':
            route_tables = AWSRouteTable.objects.all()
            serializer = AWSRouteTableSerializer(route_tables, many=True)
        elif table == 'ec2':
            ec2 = AWSEC2Instance.objects.all()
            serializer = AWSEC2InstanceSerializer(ec2, many=True)
        elif table == 'security-group':
            security_group = AWSSecurityGroup.objects.all()
            serializer = AWSSecurityGroupSerializer(security_group, many=True)
        elif table == "eip":  # 添加 EIP 逻辑
            eips = AWSElasticIP.objects.all()
            serializer = AWSElasticIPSerializer(eips, many=True)
        elif table == "vpc-endpoint":
            endpoints = VPCEndpoint.objects.all()
            serializer = AWSVpcEndpointSerializer(endpoints, many=True)
        elif table == "route53":
            route53 = Route53Record.objects.all()
            serializer = AWSRoute53RecordSerializer(route53, many=True)
        else:
            return Response({'error': 'Invalid table name'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)

class AzureDataView(APIView):
    def get(self, request, table):
        if table == 'virtual_network':
            virtual_networks = AzureVirtualNetwork.objects.all()
            serializer = AzureVirtualNetworkSerializer(virtual_networks, many=True)
        elif table == 'vnet':
            vnets = AzureVnet.objects.all()
            serializer = AzureVnetSerializer(vnets, many=True)
        elif table == 'subnet':
            subnets = AzureSubnet.objects.all()
            serializer = AzureSubnetSerializer(subnets, many=True)
        elif table == 'route_table':
            route_tables = AzureRouteTable.objects.all()
            serializer = AzureRouteTableSerializer(route_tables, many=True)
        else:
            return Response({'error': 'Invalid table name'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)

def ip_lookup_page(request):
    return render(request, 'ip_lookup.html')

def aws_page(request):
    return render(request, 'aws.html')

def azure_page(request):
    return render(request, 'azure.html')

def index_page(request):
    # 返回 indexbak.html 模板
    return render(request, 'index.html')

@api_view(['GET'])
def aws_ec2_data(request):
    # 查询数据库中 EC2 实例信息
    qs = AWSEC2Instance.objects.all()
    # 将数据序列化为 JSON
    data = []
    for ec2 in qs:
        data.append({
            'instance_id': ec2.instance_id,
            'name': ec2.name,
            'private_ips': ec2.private_ips,
            'public_ips': ec2.public_ips,
            'vpc_id': ec2.vpc_id,
            'subnet_id': ec2.subnet_id,
            'instance_type': ec2.instance_type,
            'state': ec2.state,
            'region': ec2.region,
        })
    return JsonResponse(data, safe=False)

@api_view(['GET'])
def aws_vpc_data(request):
    qs = AWSVPC.objects.all()
    data = []
    for vpc in qs:
        data.append({
            'vpc_id': vpc.vpc_id,
            'name': vpc.name,
            'ipv4_cidr': vpc.ipv4_cidr,
            'owner_id': vpc.owner_id,
            'region': vpc.region,
        })
    return JsonResponse(data, safe=False)

@api_view(['GET'])
def aws_route_table_data(request):
    # 路由表与路由条目是一对多，可以做嵌套
    route_tables = AWSRouteTable.objects.all()
    data = []
    for rt in route_tables:
        # 查询关联的路由条目
        routes = rt.awsroute_set.all()
        routes_list = []
        for r in routes:
            routes_list.append({
                'destination_cidr_block': r.destination_cidr_block,
                'target': r.target,
                'status': r.status,
            })
        data.append({
            'route_table_id': rt.route_table_id,
            'name': rt.name,
            'vpc': rt.vpc_id,
            'region': rt.region,
            'routes': routes_list
        })
    return JsonResponse(data, safe=False)

@api_view(['GET'])
# def aws_sg_data(request):
#     qs = AWSSecurityGroup.objects.all()
#     data = []
#     for sg in qs:
#         data.append({
#             'group_id': sg.group_id,
#             'name': sg.name,
#             # 你可能有更多字段，如 ingress/egress 规则
#         })
#     return JsonResponse(data, safe=False)
def aws_sg_data(request):
    """
    返回所有安全组的简要信息
    """
    qs = AWSSecurityGroup.objects.all()
    data = []
    for sg in qs:
        data.append({
            'group_id': sg.group_id,
            'group_name': sg.group_name,
            'vpc_id': sg.vpc_id,
            'description': sg.description,
            'owner': sg.owner,
            'inbound_rules_count': sg.inbound_rules_count,
            'outbound_rules_count': sg.outbound_rules_count,
        })
    return JsonResponse(data, safe=False)


@api_view(['GET'])
def aws_sg_detail(request, group_id):
    """
    返回单个安全组的详细信息，含 inbound/outbound 规则
    """
    try:
        sg = AWSSecurityGroup.objects.get(group_id=group_id)
    except AWSSecurityGroup.DoesNotExist:
        return JsonResponse({'error': 'Security group not found'}, status=404)

    # 基本信息
    sg_data = {
        'group_id': sg.group_id,
        'group_name': sg.group_name,
        'vpc_id': sg.vpc_id,
        'description': sg.description,
        'owner': sg.owner,
        'inbound_rules_count': sg.inbound_rules_count,
        'outbound_rules_count': sg.outbound_rules_count,
        # 你还可加 name 等其他字段
    }

    # 取出所有规则
    inbound_list = []
    outbound_list = []

    # sg.rules.all() 即 AWSSecurityGroupRule.objects.filter(security_group=sg)
    for rule in sg.rules.all():
        rule_data = {
            'ip_protocol': rule.ip_protocol,
            'from_port': rule.from_port,
            'to_port': rule.to_port,
            'cidr_ipv4': rule.cidr_ipv4,
            'cidr_ipv6': rule.cidr_ipv6,
            'rule_type': rule.rule_type,
            'rule_description': rule.rule_description,
        }
        if rule.direction == 'inbound':
            inbound_list.append(rule_data)
        else:
            outbound_list.append(rule_data)

    sg_data['inbound_rules'] = inbound_list
    sg_data['outbound_rules'] = outbound_list

    return JsonResponse(sg_data, safe=False)
