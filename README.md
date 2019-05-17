ZDM - Zabbix Data Mining
================
EN:

A set of scripts and templates for data mining in Zabbix


RU:

Набор скриптов и шаблонов для сбора данных в Zabbix


Requirements for the Zabbix Server host
----------------
* zabbix server 4.0


Requirements for the Zabbix Agent host
----------------
* python 3.x
* python-memcached
* memcached


Ansible example
----------------
    ansible-playbook example.yml
    ansible-playbook example.yml --tags=zdm



Optional modules
----------------
EN:

Some modules trebuesyat explicitly enable. These include such scripts that require additional configuration and / or software installation in the system.


RU:
Некоторые модули требуется явно включить. К ним относяться ьтакие скрипты, которые требуют дополнительной настройки и / или установки программного обеспечения в системе.

* iostat
