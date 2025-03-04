from django.db import models

# AWS模型
class AWSVPC(models.Model):
    vpc_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    ipv4_cidr = models.CharField(max_length=50)
    owner_id = models.CharField(max_length=50, blank=True, null=True)
    main_route_table = models.CharField(max_length=50, blank=True, null=True)
    main_network_acl = models.CharField(max_length=50, blank=True, null=True)
    region = models.CharField(max_length=50,default="unknown")

    def __str__(self):
        return f"{self.name} ({self.vpc_id})"


class AWSSecurityGroup(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    group_id = models.CharField(max_length=50, unique=True)
    group_name = models.CharField(max_length=255, blank=True, null=True)
    vpc_id = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    owner = models.CharField(max_length=100, blank=True, null=True)
    inbound_rules_count = models.IntegerField(default=0)
    outbound_rules_count = models.IntegerField(default=0)

    def __str__(self):
        # 返回一个可读字符串，如 "sg-xxxx (MySecurityGroup)"
        return f"{self.group_id} ({self.group_name or self.name})"


class AWSSecurityGroupRule(models.Model):
    """
    存储安全组中的每条Inbound/Outbound规则
    """
    security_group = models.ForeignKey(
        AWSSecurityGroup,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    direction = models.CharField(
        max_length=10,
        choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')]
    )
    ip_protocol = models.CharField(max_length=20, blank=True, null=True)
    from_port = models.IntegerField(blank=True, null=True)
    to_port = models.IntegerField(blank=True, null=True)
    cidr_ipv4 = models.CharField(max_length=50, blank=True, null=True)
    cidr_ipv6 = models.CharField(max_length=50, blank=True, null=True)
    rule_type = models.CharField(max_length=100, blank=True, null=True)  # "Type"
    rule_description = models.CharField(max_length=255, blank=True, null=True) # "Description"
    # 如果需要PrefixList或其他字段，可继续添加

    def __str__(self):
        return f"{self.security_group.group_id} {self.direction} {self.ip_protocol} {self.from_port}-{self.to_port}"
# class AWSSecurityGroup(models.Model):
#     group_id = models.CharField(max_length=50, unique=True)
#     name = models.CharField(max_length=255, blank=True, null=True)
#
#     def __str__(self):
#         return f"{self.name} ({self.group_id})"


class AWSEC2Instance(models.Model):
    instance_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    vpc_id = models.CharField(max_length=50)
    subnet_id = models.CharField(max_length=50)
    private_ips = models.TextField(blank=True, null=True)  # 可能有多个，存逗号分隔的字符串
    public_ips = models.TextField(blank=True, null=True)  # 可能有多个，存逗号分隔的字符串
    state = models.CharField(max_length=20)
    instance_type = models.CharField(max_length=50)
    region = models.CharField(max_length=50,default="unknown")
    security_groups = models.ManyToManyField(AWSSecurityGroup)  # 使用多对多关系


    def __str__(self):
        return f"{self.name} ({self.instance_id})"


class AWSSubnet(models.Model):
    name = models.CharField(max_length=255)
    subnet_id = models.CharField(max_length=255)
    vpc = models.CharField(max_length=255)
    ipv4_cidr = models.CharField(max_length=255)
    available_ipv4_address = models.IntegerField()
    route_table = models.CharField(max_length=255)
    vpc_id = models.CharField(max_length=255)
    region = models.CharField(max_length=50,default="unknown")

    def __str__(self):
        return self.name

class AWSRouteTable(models.Model):
    name = models.CharField(max_length=255, default='N/A')
    route_table_id = models.CharField(max_length=255)
    vpc = models.CharField(max_length=255, default='N/A')
    vpc_id = models.CharField(max_length=255, default='N/A')
    region = models.CharField(max_length=50,default="unknown")
    def __str__(self):
        return self.name

class AWSRoute(models.Model):
    route_table = models.ForeignKey(AWSRouteTable, on_delete=models.CASCADE, related_name='routes')
    destination_cidr_block = models.CharField(max_length=255, default='N/A')
    target = models.CharField(max_length=255, default='N/A')
    status = models.CharField(max_length=255, default='N/A')
    region = models.CharField(max_length=50,default="unknown")
    def __str__(self):
        return f"{self.route_table.route_table_id}-{self.destination_cidr_block}"


class AWSElasticIP(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    allocated_ipv4_address = models.GenericIPAddressField()
    ip_type = models.CharField(max_length=50)
    allocation_id = models.CharField(max_length=100, unique=True)
    reverse_dns_record = models.CharField(max_length=255, blank=True, null=True)
    associated_instance_id = models.CharField(max_length=100, blank=True, null=True)
    private_ip_address = models.GenericIPAddressField(blank=True, null=True)
    association_id = models.CharField(max_length=100, blank=True, null=True)
    network_interface_owner_account_id = models.CharField(max_length=50, blank=True, null=True)
    network_border_group = models.CharField(max_length=100)

    class Meta:
        db_table = "aws_elastic_ip"
        verbose_name = "AWS Elastic IP"
        verbose_name_plural = "AWS Elastic IPs"

    def __str__(self):
        return self.allocated_ipv4_address

class VPCEndpoint(models.Model):
    endpoint_id = models.CharField(max_length=50, unique=True)  # 确保字段名正确
    name = models.CharField(max_length=255, blank=True, null=True)
    vpc_id = models.CharField(max_length=50)
    service_name = models.CharField(max_length=255)
    endpoint_type = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    creation_time = models.DateTimeField(null=True, blank=True)
    region = models.CharField(max_length=50, default='unknown')
    subnets = models.JSONField(default=list)
    network_interfaces = models.JSONField(default=list)

    def __str__(self):
        return self.endpoint_id

# Azure模型
class AzureVirtualNetwork(models.Model):
    name = models.CharField(max_length=255)
    resource_group = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    subscription = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class AzureVnet(models.Model):
    name = models.CharField(max_length=255)
    address_space = models.CharField(max_length=255)
    subnets = models.CharField(max_length=255)
    peerings = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class AzureSubnet(models.Model):
    name = models.CharField(max_length=255)
    ipv4 = models.CharField(max_length=255)
    available_ips = models.IntegerField()
    secret_group = models.CharField(max_length=255)
    route_table = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class AzureRouteTable(models.Model):
    address_prefix = models.CharField(max_length=255)
    next_hop_type = models.CharField(max_length=255)

    def __str__(self):
        return self.address_prefix