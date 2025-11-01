from celery import shared_task
from django.utils import timezone
from decimal import Decimal
import os

import graphene
from graphene.test import Client

# بناء سكيمة GraphQL محلياً من Query و Mutation (بما أن schema غير مصرح به في schema.py)
from .schema import Query, Mutation
schema = graphene.Schema(query=Query, mutation=Mutation)
client = Client(schema)

LOG_PATH = '/tmp/crm_report_log.txt'  # على Windows: C:\tmp\crm_report_log.txt

@shared_task(name='crm.tasks.generate_crm_report')
def generate_crm_report():
    # استعلام GraphQL لجلب البيانات
    query = '''
    query CRMReport {
      customers { id }
      orders { id totalAmount }
    }
    '''

    result = client.execute(query)

    if 'errors' in result and result['errors']:
        raise Exception(f'GraphQL errors: {result["errors"]}')

    data = result.get('data', {}) or {}
    customers = data.get('customers') or []
    orders = data.get('orders') or []

    total_customers = len(customers)
    total_orders = len(orders)

    total_revenue = Decimal('0')
    for o in orders:
        val = o.get('totalAmount')
        if val is not None:
            # Graphene قد يعيد Decimal كسلسلة، لذا نحوله إلى Decimal
            total_revenue += Decimal(str(val))

    # صيغة الوقت المطلوبة
    ts = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'{ts} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n'

    # تأكد أن المجلد موجود
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    except Exception:
        pass

    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line)

    return {'customers': total_customers, 'orders': total_orders, 'revenue': str(total_revenue)}