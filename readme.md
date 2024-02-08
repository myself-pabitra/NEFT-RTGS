(env) [ec2-user@ip-105-0-1-130 NEFT-RTGS]$ pkill gunicorn
(env) [ec2-user@ip-105-0-1-130 NEFT-RTGS]$ sudo systemctl stop nginx
(env) [ec2-user@ip-105-0-1-130 NEFT-RTGS]$ gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8888 -t 60 --access-logfile /home/ec2-user/NEFT-RTGS/access.log --error-logfile /home/ec2-user/NEFT-RTGS/error.log --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s' --capture-output --log-syslog --log-syslog-prefix gunicorn --log-level debug -D main:app
(env) [ec2-user@ip-105-0-1-130 NEFT-RTGS]$ sudo systemctl restart nginx
