Zabbix Data Mining
================
EN:

A set of scripts and templates for data mining in Zabbix.


RU:

Набор скриптов и шаблонов для сбора данных в Zabbix.


Requirements for the Zabbix Server host
----------------
* zabbix server 4.0


Requirements for the Zabbix Agent host
----------------
* python 3.x
* python-memcached
* memcached

Playbook templates for distribution:
* RedHat (CentOS): 7
* Debian (Ubuntu): 18.04
* Gentoo Linux: default/linux/amd64/17.0/systemd


Ansible example
----------------
Apply all roles. Includes installation and configuration of `memcached` (required), `zabbix-agent` and `logrotate`.

Attention: Check the default settings for these roles!

    ansible-playbook example.yml

Disable roles:

    ansible-playbook example.yml --skip-tags=zabbix-agent,logrotate

Only scripts:

    ansible-playbook example.yml --tags=zdm


Modules
----------------

* memcached
* ping


EN:

Some modules must be specified in the `zdm_modules_enabled` variable. These include such scripts that require additional configuration and / or software installation in the system.


RU:

Некоторые модули требуется явно указать в переменной `zdm_modules_enabled`. К ним относятся такие скрипты, которые требуют дополнительной настройки и / или установки программного обеспечения в системе.


* iostat
* nginx
* apache
* conntrack
* cert
* postgres
* gitlab



See also [wiki](https://wiki.enchtex.info/handmade/zabbix/zabbix_data_mining) page.

