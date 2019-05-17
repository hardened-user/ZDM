## Role Variables

**logrotate_d_config**: A list of logrotate scripts and the directives to use for the rotation.

* name - The name of the script that goes into /etc/logrotate.d/<name>
* paths - List of paths to point logrotate to for the log rotation.
* options - List of directives for logrotate, view the logrotate man page for specifics
* postrotate - Postrotate scripts, view the logrotate man page for specifics
* prerotate - Prerotate scripts, view the logrotate man page for specifics


## Example Playbook
```
---
# Замена настроек по-умолчанию для syslog

- name: "Configuration logrotate.d: syslog"
  hosts: vm
  become: yes
  vars:
    logrotate_d_config:
      - name: "syslog"
        paths:
          - "/var/log/cron"
          - "/var/log/maillog"
          - "/var/log/messages"
          - "/var/log/secure"
          - "/var/log/spooler"
        postrotate: /bin/kill -HUP `cat /var/run/syslogd.pid 2> /dev/null` 2> /dev/null || true
        options:
          - rotate 2
          - missingok
          - sharedscripts
  roles:
    - logrotate
```
