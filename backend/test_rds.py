from core.database import execute_single
try:
    res = execute_single('SELECT 1 as test')
    print('RDS is alive:', res)
except Exception as e:
    print('RDS failed:', e)
